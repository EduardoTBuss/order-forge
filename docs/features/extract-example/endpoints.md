# API Design for Extract (Reference Example)

> ⚠️ **This is a reference example** showing how to document endpoints for a feature, distinguishing between core (reused) and custom (to build) endpoints.

## Core Endpoints (Reused)

These endpoints from core modules are used by the Extract feature:

| Method | Path                    | Purpose                           | Core Module |
| ------ | ----------------------- | --------------------------------- | ----------- |
| GET    | /core/openai/models   | Fetch available OpenAI models     | openai      |
| POST   | /core/openai/extract  | Extract structured data from PDF  | openai      |

## Custom Endpoints (To Build)

This feature uses only core endpoints. No custom endpoints required.

> 💡 **Best Practice**: Always check if core modules provide the functionality you need before designing custom endpoints. In this case, the `openai` core module provides everything needed for extraction.

## Data Flow

1. **Page Load**
   - Frontend calls `GET /core/openai/models` to populate the model dropdown
   - User sees available models (gpt-5, gpt-4o, etc.)

2. **User Uploads PDF**
   - File is stored in local state (no API call)
   - PDF is converted to base64 for API submission

3. **User Configures Settings**
   - Model selection, strict mode, preprocessing options
   - All stored in local state

4. **User Clicks "Run Extraction"**
   - Frontend calls `POST /core/openai/extract` with:
     - Base64-encoded PDF
     - Output schema (JSON Schema format)
     - OpenAI configuration (model, etc.)
     - Preprocessing configuration (DPI, contrast, etc.)
   - Response contains extracted data and metadata

5. **Results Display**
   - UI switches to "Result" tab
   - Extracted data shown as formatted JSON
