import copy
from urllib.parse import urlparse


def convert_openapi3_to_swagger(
    openapi3: dict, allowed_tags: list[str] | None = None, request=None
) -> dict:
    """Convert an OpenAPI 3.0 specification (dict) into a Swagger 2.0 spec (dict), optionally filtering operations by tags."""
    swagger = copy.deepcopy(openapi3)

    # 1) Version bump
    swagger["swagger"] = "2.0"
    swagger.pop("openapi", None)

    # 2) servers -> host / schemes / basePath
    _convert_servers(swagger, request)

    # 3) components -> definitions + securityDefinitions
    comps = swagger.get("components", {})
    if comps:
        _convert_schemas(swagger, comps.get("schemas", {}))
        _convert_security_schemes(swagger, comps.get("securitySchemes", {}))
        # preserve other components under x-components
        swagger["x-components"] = {
            k: v for k, v in comps.items() if k not in ("schemas", "securitySchemes")
        }
        swagger.pop("components", None)

    # 4) paths & operations
    _convert_paths(swagger.get("paths", {}), allowed_tags=allowed_tags)

    # 5) fix all $ref pointers
    _fix_refs(swagger)

    return swagger


def _convert_servers(swagger: dict, request=None) -> None:
    servers = swagger.pop("servers", [])

    # If we have a request object, use it to get the current host information
    if request:
        # Extract host and scheme from the current request
        host = request.headers.get("host", "")
        scheme = request.url.scheme

        if host:
            swagger["host"] = host
        if scheme:
            swagger["schemes"] = [scheme]
        # Use root path for cleaner endpoints
        swagger["basePath"] = "/"
        return

    # Fallback to servers if no request object
    if not servers:
        return
    url = servers[0].get("url", "")
    parsed = urlparse(url)
    if parsed.netloc:
        swagger["host"] = parsed.netloc
    if parsed.scheme:
        swagger["schemes"] = [parsed.scheme]
    swagger["basePath"] = parsed.path or "/"


def _convert_schemas(swagger: dict, schemas: dict) -> None:
    # Move schemas to definitions
    swagger["definitions"] = schemas
    # Clean each schema recursively
    for schema in swagger["definitions"].values():
        _clean_schema(schema)


def _clean_schema(schema: dict) -> None:
    # Rename examples to x-examples
    examples = schema.pop("examples", None)
    if examples is not None:
        schema["x-examples"] = examples

    # Convert JSON Schema const -> Swagger enum
    if "const" in schema:
        const_value = schema.pop("const")
        # Ensure enum exists and contains the const value
        schema["enum"] = [const_value]
        # Best-effort set of type if missing
        if "type" not in schema and const_value is not None:
            if isinstance(const_value, bool):
                schema["type"] = "boolean"
            elif isinstance(const_value, int):
                schema["type"] = "integer"
            elif isinstance(const_value, float):
                schema["type"] = "number"
            elif isinstance(const_value, str):
                schema["type"] = "string"

    # Convert JSON Schema tuple form (prefixItems) -> Swagger-compatible array
    if "prefixItems" in schema:
        prefix_items = schema.pop("prefixItems")
        if isinstance(prefix_items, list) and prefix_items:
            # Try to unify item type
            item_types = []
            for item in prefix_items:
                if isinstance(item, dict) and "type" in item:
                    item_types.append(
                        item["type"]
                    )  # e.g., 'number', 'integer', 'string'
            unified: dict = {}
            if item_types and all(t in {"number", "integer"} for t in item_types):
                unified = {"type": "number"}
            elif item_types and all(t == "string" for t in item_types):
                unified = {"type": "string"}
            elif item_types and all(t == "boolean" for t in item_types):
                unified = {"type": "boolean"}
            else:
                # Fallback to string for mixed/unknown types to maintain compatibility
                unified = {"type": "string"}

            schema["type"] = "array"
            if "items" not in schema:
                schema["items"] = unified
            # Fix length constraints to communicate tuple arity
            schema.setdefault("minItems", len(prefix_items))
            schema.setdefault("maxItems", len(prefix_items))

    # Handle anyOf/oneOf/allOf - convert to union type for Swagger 2.0 compatibility
    if "anyOf" in schema:
        any_of = schema.pop("anyOf")
        if any_of and len(any_of) > 0:
            # For Power Automate compatibility, prefer object types over primitives
            non_null_types = [item for item in any_of if item.get("type") != "null"]
            if non_null_types:
                # Prefer object types or $ref types for better Power Automate compatibility
                object_types = [
                    item
                    for item in non_null_types
                    if item.get("type") == "object" or "$ref" in item
                ]
                if object_types:
                    # Use the first object type or $ref
                    first_type = object_types[0]
                else:
                    # Fall back to first non-null type
                    first_type = non_null_types[0]

                if "$ref" in first_type:
                    schema["$ref"] = first_type["$ref"]
                else:
                    schema.update(first_type)
            else:
                # All types are null, set type to null
                schema["type"] = "null"

    if "oneOf" in schema:
        one_of = schema.pop("oneOf")
        if one_of and len(one_of) > 0:
            # For Power Automate compatibility, use the first type
            first_type = one_of[0]
            if "$ref" in first_type:
                schema["$ref"] = first_type["$ref"]
            else:
                schema.update(first_type)

    if "allOf" in schema:
        all_of = schema.pop("allOf")
        if all_of and len(all_of) > 0:
            # Merge all types for allOf
            for item in all_of:
                if "$ref" in item:
                    schema["$ref"] = item["$ref"]
                    break
                else:
                    schema.update(item)

    # OpenAPI 3 -> Swagger 2: convert numeric exclusiveMinimum/exclusiveMaximum to boolean
    # This must run AFTER anyOf/oneOf/allOf conversion to handle merged schemas
    if isinstance(schema.get("exclusiveMinimum"), (int, float)):
        schema["minimum"] = schema["exclusiveMinimum"]
        schema["exclusiveMinimum"] = True
    if isinstance(schema.get("exclusiveMaximum"), (int, float)):
        schema["maximum"] = schema["exclusiveMaximum"]
        schema["exclusiveMaximum"] = True

    # Drop OpenAPI3-only keywords
    for key in (
        "nullable",
        "discriminator",
        "readOnly",
        "writeOnly",
    ):
        schema.pop(key, None)

    # Recurse into nested schemas
    for prop_schema in schema.get("properties", {}).values():
        _clean_schema(prop_schema)
    if "items" in schema:
        _clean_schema(schema["items"])


def _convert_security_schemes(swagger: dict, schemes: dict) -> None:
    if schemes:
        # Power Automate Cloud requires API Key security scheme format for custom connectors
        # FastAPI HTTPBearer generates HTTP Bearer scheme, but Power Automate needs API Key
        swagger["securityDefinitions"] = {
            "api_key": {"type": "apiKey", "in": "header", "name": "Authorization"}
        }


def _convert_paths(paths: dict, allowed_tags: list[str] | None) -> None:
    http_methods = {
        "get",
        "put",
        "post",
        "delete",
        "options",
        "head",
        "patch",
        "trace",
    }
    # Iterate paths and filter operations based on allowed tags if provided
    for path, path_item in list(paths.items()):
        removed_all_ops = True
        for method, op in list(path_item.items()):
            if method.lower() in http_methods and isinstance(op, dict):
                # Filter by tags if allowed_tags is provided
                if allowed_tags is not None:
                    op_tags = [t for t in op.get("tags", []) if isinstance(t, str)]
                    if not set(op_tags).intersection(set(allowed_tags)):
                        # Remove operation without matching tags
                        path_item.pop(method, None)
                        continue
                _convert_operation(op)
                removed_all_ops = False
        # If a path has no remaining operations, remove the path entry
        if removed_all_ops or not any(
            m.lower() in http_methods and isinstance(v, dict)
            for m, v in path_item.items()
        ):
            paths.pop(path, None)


def _convert_operation(op: dict) -> None:
    # Capitalize first letter of operationId if present
    if "operationId" in op and op["operationId"]:
        op["operationId"] = op["operationId"][0].upper() + op["operationId"][1:]

    # Handle parameters
    parameters = op.get("parameters", [])
    converted_params = []

    for param in parameters:
        # Convert OpenAPI 3.0 parameter to Swagger 2.0 format
        converted_param = {
            "name": param.get("name"),
            "in": param.get("in"),
            "required": param.get("required", False),
            **(
                {"description": param["description"]}
                if param.get("description")
                else {}
            ),
        }

        # Extract type information from schema if available
        schema = param.get("schema")
        if schema:
            if "type" in schema:
                converted_param["type"] = schema["type"]
            if "format" in schema:
                converted_param["format"] = schema["format"]
            if "items" in schema:
                converted_param["items"] = schema["items"]
            if "enum" in schema:
                converted_param["enum"] = schema["enum"]
            if "default" in schema:
                converted_param["default"] = schema["default"]
            if "minimum" in schema:
                converted_param["minimum"] = schema["minimum"]
            if "maximum" in schema:
                converted_param["maximum"] = schema["maximum"]
            if "minLength" in schema:
                converted_param["minLength"] = schema["minLength"]
            if "maxLength" in schema:
                converted_param["maxLength"] = schema["maxLength"]
            if "pattern" in schema:
                converted_param["pattern"] = schema["pattern"]
            if "uniqueItems" in schema:
                converted_param["uniqueItems"] = schema["uniqueItems"]
            if "multipleOf" in schema:
                converted_param["multipleOf"] = schema["multipleOf"]
        elif "type" in param:
            # If type is directly in parameter (from type annotation)
            converted_param["type"] = param["type"]

        # If no type is set, default to 'string' to increase compatibility with incomplete specs
        if "type" not in converted_param:
            converted_param["type"] = "string"

        # If the type is array and items exist only in schema, ensure we copy them over
        if (
            converted_param.get("type") == "array"
            and "items" not in converted_param
            and schema
            and "items" in schema
        ):
            converted_param["items"] = schema["items"]

        # Handle examples
        if "examples" in param:
            converted_param["x-examples"] = param["examples"]

        converted_params.append(converted_param)

    op["parameters"] = converted_params

    # requestBody -> parameters + consumes
    if "requestBody" in op:
        rb = op.pop("requestBody")
        content = rb.get("content", {})
        for mime, media in content.items():
            consumes = op.setdefault("consumes", [])
            if mime not in consumes:
                consumes.append(mime)
            schema = media.get("schema", {})
            param = {
                "name": "body",
                "in": "body",
                "required": rb.get("required", False),
                "schema": schema,
            }
            # Add type if it exists in schema
            if "type" in schema:
                param["type"] = schema["type"]
            op["parameters"].append(param)
            # Only first mime
            break

    # responses.content -> schema + produces
    for resp in op.get("responses", {}).values():
        if "content" in resp:
            for mime, media in resp["content"].items():
                produces = op.setdefault("produces", [])
                if mime not in produces:
                    produces.append(mime)
                schema = media.get("schema", {})
                resp["schema"] = schema
                # Only first mime
                break
            resp.pop("content", None)

    # Drop unsupported OAS3 fields
    for key in ("servers", "callbacks", "security"):
        op.pop(key, None)


def _fix_refs(node: dict | list) -> None:
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if k == "$ref" and isinstance(v, str):
                new_ref = v.replace("#/components/schemas/", "#/definitions/")
                new_ref = new_ref.replace("#/components/", "#/x-components/")
                node[k] = new_ref
            else:
                _fix_refs(v)
    elif isinstance(node, list):
        for item in node:
            _fix_refs(item)
