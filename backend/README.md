# Invoice Intake - Workshop Backend

This is the **workshop starter** backend: a minimal, modular FastAPI service that
participants extend to build an invoice intake feature.

## App Identity

The app identity is configured in `src/settings.py`:

```python
client_name: str = "Workshop"
project_name: str = "Invoice Intake"
```

The `display_name` property returns `"Invoice Intake - Workshop"` and is used as the FastAPI app title.

**Keep in sync with:** `docs/project.md` (authoritative source)

The service follows a strict structure, enabling teams to:

* Build robust, maintainable APIs
* Keep core logic isolated and reusable
* Integrate easily with stores like PostgreSQL, CosmosDB, and Blob Storage
* Collaborate efficiently by enforcing common patterns

---

## 📚 Table of Contents

* [🚀 Development Setup Guide (GitHub Codespaces)](#development-setup-guide-github-codespaces)

  * [✅ Prerequisites](#-prerequisites)
  * [🚀 Getting Started](#-getting-started)
  * [🌐 Accessing the API](#-accessing-the-api)
  * [💻 Using VS Code Locally (Optional)](#-using-vs-code-locally-optional)
  * [🛠️ Verifying Pre‑commit Hooks](#️-verifying-pre-commit-hooks)
  * [💡 Tips](#-tips)
* [🗂️ Repository Structure Overview](#️-repository-structure-overview)

  * [📁 modules/](#-modules)

    * [🔒 core](#-core)
    * [🧩 custom](#-custom)
  * [🔌 services/](#-services)
  * [📦 Custom Module Structure](#-custom-module-structure)
  * [🧱 Project Folder Overview](#-project-folder-overview)
* [🧪 Testing](#-testing)
* [🥇 Golden Rules](#-golden-rules)

---

## 🚀 Development Setup Guide (GitHub Codespaces)

This guide helps you get started with the development environment using **GitHub Codespaces** — no local setup required.

### ✅ Prerequisites

* Access to the GitHub repository.
* **GitHub Codespaces** enabled for your GitHub account.

### 🚀 Getting Started

#### 1. Create a Codespace

1. Go to the repository on GitHub.
2. Click the green **<> Code** button.
3. Select the **Codespaces** tab and click **Create codespace on `main`**.

#### 2. Wait for initialization

GitHub will automatically provision the development container. This includes:

* Python and a virtual environment
* Project dependencies (from `requirements.txt` or `pyproject.toml`)
* Pre‑commit hooks installed (`prek install`)
* Linters and formatters like **ruff**, and **ty**
* Recommended extensions (if defined in `.devcontainer`)

#### 3. Start the application

Once the Codespace is ready, run the following command in the terminal:

```bash
bash entrypoint.sh
```

This will start the application server.

### 🌐 Accessing the API

When the app is running it will be exposed on **port `8000`**, and GitHub Codespaces will create a secure public URL similar to:

```
https://turbo‑parakeet‑979xxg47x79j2p65w‑8000.app.github.dev/
```

#### 🔍 How this URL works

GitHub automatically generates this URL to safely expose your application to the browser. It includes:

* The random Codespace name (e.g. `turbo‑parakeet`)
* A unique hash for your session
* The exposed port number (e.g. `8000`)
* The `.app.github.dev` domain for secure HTTPS traffic

#### 🔐 Who can access it?

The URL is **private by default**. Only you (or members with access to the Codespace) can open it.

To access the app:

1. Open the **PORTS** tab in the Codespace interface.
2. Locate port `8000` — it will show as **Forwarded**.
3. Click the associated URL to open the app in your browser.

![Example of the PORTS tab](image-20250523-000613.png)

### 💻 Using VS Code Locally (Optional)

You can also open and work in your Codespace directly from **VS Code Desktop**, instead of the browser.

#### 1. Install the required tools

1. Install **Visual Studio Code**.
2. Install the **GitHub Codespaces** extension from the VS Code Marketplace: [https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces)

#### 2. Connect to a Codespace

1. Open VS Code.
2. Press **F1** (or **Cmd+Shift+P / Ctrl+Shift+P**) to open the Command Palette.
3. Type and select **Codespaces: Connect to Codespace**.
4. Choose your Codespace from the list.

That’s it — you’ll be working in your Codespace with the full power of VS Code!

### 🛠️ Verifying Pre‑commit Hooks

We use [prek](https://prek.j178.dev/) as our pre-commit hooks manager. Hooks run automatically when committing code. You can also run them manually:

```bash
prek run --all-files
```

This ensures your code is linted, formatted, and type‑checked **before** committing.

### 💡 Tips

* Use **Ctrl+Shift+P** to open the Command Palette in VS Code.
* If something doesn’t work as expected, try **rebuilding** the Codespace from the **Codespaces** tab.

---

## 🗂️ Repository Structure Overview

This repository is organized to separate core functionality from project‑specific custom logic, and to simplify integration with external services.

Here are the key components:

### 📁 `modules/`

This folder contains all the logic related to HTTP endpoints. It is split into two parts:

#### 🔒 `core/`

* Contains base modules shared across **all projects**.
* **Do not edit** anything in this folder.
* These modules include reusable logic and shared endpoints meant to work out of the box.

#### 🧩 `custom/`

This is where developers implement **project‑specific modules**. Each folder under `custom/` represents a separate functional module.

You are allowed to create new folders inside `custom/`, but **you must follow a strict structure** to ensure consistency across projects.

Every module must include the following components:

##### 📄 `routes.py`

* This is where **all endpoints must be defined** using FastAPI.
* The `routes.py` file acts as the module’s entry point for HTTP requests.
* You should **only**:

  * Register routes
  * Handle light validations (e.g., missing parameters, 404s)
  * Catch and handle known exceptions
* **Do not include business logic here**. Instead, delegate it to the `logic/` layer.

##### 📁 `logic/`

* This is the layer where **all core logic** must reside.
* You must include at least one file:

  * `main.py`: This file centralizes the module's primary business logic and is the main entry point from `routes.py`.
* You can create additional files if needed to improve modularity and clarity.
* The goal is to **encapsulate complexity** and keep logic clean and reusable.

##### 📁 `schemas/`

* This folder contains all **Pydantic models** used by the module.
* It must include at least:

  * `io.py`: This file defines the **input and output schemas** for each endpoint.

    * ⚠️ **Every endpoint is required to have one input and one output schema.**
  * `*.py`: Additional files as needed to define Pydantic models that support internal logic.

##### 📁 `db/` (Optional)

* Contains the module's database configuration

* `models.py`: Defines SQLAlchemy models for the database
  - Here you define tables and their relationships using SQLAlchemy
  - You can define enums and custom column types

* `queries.py`: Contains functions to interact with the database
  - Implements CRUD and other database operations
  - Uses the centralized database service

* Consult a senior engineer before finalizing the schema
  - Review the design with a senior to ensure consistency with existing conventions
  - Helps prevent migration conflicts and other downstream issues

### 🔌 `services/`

* This folder contains **interfaces to common services**, such as:

  * `PostgreSQL`
  * `CosmosDB`
  * `Blob Storage`
  * And others
* These service wrappers are **preconfigured** so you don’t need to worry about setup or environment variables.
* Just import and use them — they’re designed to abstract away the complexity of integration.

### 📦 Custom Module Structure

Every custom module must follow this structure:

```text
custom/
└── my_module/
    ├── routes.py
    ├── tests.py           # Integration tests for all endpoints
    ├── logic/
    │   ├── main.py        # Business logic entry-point for the module
    │   └── ...            # Optional: Helper logic files
    ├── schemas/
    │   ├── io.py          # Endpoint Input/Output Pydantic models
    │   └── ...            # Optional: Additional Pydantic models
    └── db/ (Optional)
        ├── models.py
        └── queries.py
```

### 🧱 Project Folder Overview

Here's a simplified view of the relevant structure based on the current repository:

```text
src/
└── app/
    ├── modules/
    │   ├── core/            # Shared, non-editable modules
    │   │   └── postgresql/
    │   │       ├── logic/
    │   │       │   └── main.py
    │   │       ├── schemas/
    │   │       │   └── io.py
    │   │       ├── routes.py
    │   │       └── tests.py     # Integration tests
    │   └── custom/          # Project-specific, editable modules
    │       └── my_feature/
    │           ├── logic/
    │           │   ├── main.py
    │           │   └── helpers.py
    │           ├── schemas/
    │           │   └── io.py
    │           ├── routes.py
    │           └── tests.py     # Integration tests
    ├── services/            # Shared service clients
    │   ├── postgresql/
    │   ├── cosmosdb/
    │   ├── blob_storage/
    │   └── ...
    ├── helpers/
    ├── middleware/
    └── ...
```

---

## 🧪 Testing

Tests are colocated with their modules. Each module contains a `tests.py` file alongside its `routes.py`, making it easy to find and maintain tests for each endpoint.

### Test Philosophy

**Focus exclusively on endpoint integration tests.** Each `tests.py` file should:

* ✅ Test all endpoints defined in `routes.py`
* ✅ Cover all possible HTTP status codes (success, validation errors, internal errors)
* ✅ Verify correct response structure and content
* ✅ Test different input scenarios and edge cases
* ✅ Run against real services (PostgreSQL, CosmosDB, Blob Storage)

**Do NOT write:**

* ❌ Unit tests for individual functions
* ❌ Tests for internal implementation details
* ❌ Mocked database/service tests (use real services)

Tests simulate real API requests against real backends and verify endpoints behave correctly from a client's perspective.

### Running Tests

Tests run against real services using Docker Compose. **Both methods run database migrations automatically before tests.**

#### Method 1: Convenience Script (Recommended for Manual Runs)

Use `./backend/run-tests.sh` during development — it handles service startup, health checks, and cleanup:

```bash
# Run all integration tests
./backend/run-tests.sh

# Skip slow tests (faster iteration)
./backend/run-tests.sh --fast

# Run tests for a specific module
./backend/run-tests.sh -- src/app/modules/core/postgresql/tests.py -v

# Run with specific markers
./backend/run-tests.sh -- -m postgresql
```

#### Method 2: Direct Docker Compose

Use when services are already running or you need more control:

```bash
# Run all tests
docker compose --profile test run --rm backend-test

# Pass pytest arguments via PYTEST_ARGS
PYTEST_ARGS="-k test_upload" docker compose --profile test run --rm backend-test
PYTEST_ARGS="src/app/modules/core/postgresql/tests.py -v" docker compose --profile test run --rm backend-test
```

⚠️ **Important:** Always use `PYTEST_ARGS` to pass arguments. Never override the command directly (e.g., `backend-test pytest ...`) — this bypasses migrations.

### Test Markers

Tests are categorized with markers for selective execution:

| Marker        | Description                                  |
| ------------- | -------------------------------------------- |
| `postgresql`  | Tests requiring PostgreSQL                   |
| `cosmosdb`    | Tests requiring CosmosDB/MongoDB             |
| `blobstorage` | Tests requiring Blob Storage (local Azurite) |
| `slow`        | Long-running tests                           |
| `integration` | Full integration tests                       |

Use markers to run or skip specific test categories:

```bash
# Run only PostgreSQL tests
./backend/run-tests.sh -m postgresql

# Skip slow tests
./backend/run-tests.sh -m "not slow"
```

### Test Report

Tests automatically generate an HTML report at `static/test-report.html`. When the server is running, access it at:

```
http://localhost:8000/static/test-report.html
```

### Pre-commit Integration

Tests are integrated with pre-commit hooks. Before each commit, tests run automatically using the test profile. If any test fails, the commit is blocked.

### On-Demand Test Execution (API)

The API provides endpoints to trigger and monitor test runs on a live server:

| Endpoint                     | Method | Description                                |
| ---------------------------- | ------ | ------------------------------------------ |
| `/core/info/tests/modules` | GET    | Lists available module names for filtering |
| `/core/info/tests/run`     | POST   | Triggers an asynchronous test run          |
| `/core/info/tests/status`  | GET    | Returns the status of the last test run    |

All endpoints require API key authentication.

**Run all tests:**

```bash
curl -X POST http://localhost:8000/core/info/tests/run \
  -H "Authorization: Bearer $API_KEY"
```

**Run tests for a specific module:**

```bash
# List available modules
curl http://localhost:8000/core/info/tests/modules \
  -H "Authorization: Bearer $API_KEY"

# Run only PostgreSQL tests
curl -X POST "http://localhost:8000/core/info/tests/run?module=postgresql" \
  -H "Authorization: Bearer $API_KEY"

# Check status
curl http://localhost:8000/core/info/tests/status \
  -H "Authorization: Bearer $API_KEY"
```

Available modules: `postgresql`, `cosmosdb`, `blob_storage`, `info`.

---

## 🥇 Golden Rules

> 🚨 **Every pull request will be automatically rejected if any of the following rules are not respected.** These standards exist to ensure consistency, maintainability, and long‑term scalability across all projects.

### ✅ 1. All Functions Must Use Type Annotations

Every function must be explicitly typed using the [`typing`](https://docs.python.org/3/library/typing.html) module.

```python
def calculate_total(a: int, b: int) -> int:
    return a + b
```

### ✅ 2. `prek` Must Be Run Before Every Push

You **must** run all `prek` hooks before pushing your code:

```bash
prek run --all-files
```

Or make sure the hooks run automatically with:

```bash
prek install
```

These checks enforce formatting, linting, and other quality standards.

### ✅ 3. All Functions Must Include Docstrings

Every function must have a descriptive docstring that briefly explains **what** the function does (and optionally **why** or **how**):

```python
def fetch_data(url: str) -> dict:
    """Fetches JSON data from a given URL."""
```

### ✅ 4. Each Endpoint Must Have Two Pydantic Models

Every endpoint must define:

* One **input model**
* One **output model**

These models should be declared in the module’s `models/io.py` file (or in one file per endpoint).

#### Required field metadata

💡 Every field in both input and output models must include:

* **description:** a clear explanation of the field’s purpose
* **example:** a realistic value that will be used by Power Automate’s custom connector UI

This improves API usability, self‑documentation, and ensures smooth integration with **Power Automate** via **custom connectors**.

```python
class CreateUserInput(BaseModel):
    name: str

class CreateUserOutput(BaseModel):
    id: str
```

> ❗ **Endpoints missing either the input or output model, or missing description and example metadata per field, will be rejected during code review.**

### ✅ 5. Use `async` for Any I/O‑Bound Operation

If your endpoint performs **any** of the following:

* Calls to external APIs
* Database access (e.g., PostgreSQL)
* Interactions with file systems or cloud services

Then the function must be declared as `async`:

```python
@router.post("/users")
async def create_user(data: CreateUserInput) -> CreateUserOutput:
    ...
```

Refer to the `postgresql` and `blob_storage` modules for implementation examples.
