🥋 HelixNet Testing Scripts: Core API End-to-End Flow
angel@debian:~/repos/helixnet$ docker exec -it postgres sh
/ # psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT email FROM users;"
Password for user helix_user: 
       email       
-------------------
 marcel@helix.net
 petar@helix.net
 auditor@helix.net
 chuck@example.com
(4 rows)

/ # 

This directory contains crucial integration tests designed to verify the entire lifecycle of core features, particularly the asynchronous job submission flow via Celery and PostgreSQL.
💥 The Core Entanglement & Solution

Our initial testing setup failed due to a fundamental conflict between the pytest-asyncio framework and SQLAlchemy's async connection pooling.

Problem
	

Cause
	

Solution (See app/db/database.py)

RuntimeError: Event loop is closed
	

SQLAlchemy's default connection pool (QueuePool) holds open connections, which conflict with pytest-asyncio's rapid event loop creation/destruction during tests.
	

CRITICAL FIX: When TESTING=True, we switch the engine to use NullPool.

TypeError: Invalid argument(s) 'pool_size'
	

NullPool doesn't manage connection counts, so it doesn't accept the pool_size argument.
	

CRITICAL FIX: When TESTING=True, we conditionally remove the pool_size argument from the engine creation kwargs.

ConnectionError: redis:6379. Name or service not known
	

Running tests locally outside Docker meant the redis hostname couldn't be resolved.
	

CRITICAL FIX: Explicitly set CELERY_BROKER_URL and CELERY_RESULT_BACKEND to use 127.0.0.1 (localhost).
🚀 Running End-to-End Tests (The Lifesaver Command)

You MUST run a local PostgreSQL instance and a local Redis instance before executing these tests.

Use the following command, which includes all necessary environment variables to properly configure SQLAlchemy for testing and connect Celery to your local Redis instance.

TESTING=True POSTGRES_HOST=127.0.0.1 \
CELERY_BROKER_URL="redis://127.0.0.1:6379/0" \
CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/0" \
pytest test_job_flow.py

🛠️ Creating New Integration Tests

    Use test_job_flow.py as a Template: The fixture setup and teardown within this test file are correctly configured for an async environment.

    Authentication: Use the get_auth_token() helper function (likely in conftest.py) to easily obtain the necessary headers.

    Database Access: For read/write operations within a test, you should not need to interact directly with the async engine since the FastAPI TestClient handles the request lifecycle, which includes the database dependency injection (get_db_session).

    Celery Jobs: Test that your API route successfully calls the .delay() method and checks the immediate response (Status 202). Testing the actual Celery worker execution is usually done in separate, isolated worker tests.

🛡️ Future Prevention: The Hard-Won Lesson

The core principle learned is Conditional Resource Configuration.

Whenever your service relies on a third-party resource manager (like SQLAlchemy's connection pool, or specific Celery settings), always wrap its configuration in a conditional check for the test environment (if IS_TESTING). This is the most robust way to ensure a complex, production-ready setup can still be tested reliably in a lightweight, single-process environment.

# Super Test Suite — How to run

This folder contains `super_test_suite.py` — an enterprise-style test harness for the FastAPI `users` service.

This document explains how to run the harness from the repository root, using the project's virtual environment (`./venv`) or a fresh one. It shows both interactive runs and headless CI-friendly runs, plus an example `pytest` wrapper.

---

## Requirements / Assumptions
- Linux / macOS (commands shown for Debian); Windows instructions noted when relevant.
- Python 3.9+ recommended (3.8 may work).
- You have a Python venv at the project root `./venv` (this repo already contains one), or you can create a new one.
- The API under test should be reachable (default `http://localhost:8000`). Set `API_BASE_URL` to target another host/port.

---

## Files in this folder
- `super_test_suite.py` — the harness (interactive CLI + headless modes).
- `requirements-test.txt` — test dependencies (optional; provided below).
- `test_super_smoke.py` — minimal `pytest` wrapper to run the smoke test (optional).

---

## 1) Quick — activate venv and install deps (from repo root)
If you already have the venv at the project root:
```bash
# from repo root
source ./venv/bin/activate        # Debian / macOS
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# upgrade pip and install test deps
pip install --upgrade pip
pip install -r app/tests/requirements-test.txt
# (If you prefer the single command:)
# pip install requests rich pydantic python-jose pytest
Delighted — a proper detective's primer for running the suite. Below you’ll find a ready-to-drop `README.md` to place in `app/tests/`, plus two small helper files you should add there (`requirements-test.txt` and an optional `pytest` wrapper test). The README is written as a step-by-step guide (activate your venv from the repo root, install test deps, run the harness interactively or headless, run via `pytest`, CI tips, and troubleshooting).

Save the following three files in **`app/tests/`**.

---

# `app/tests/README.md`

````markdown
# Super Test Suite — How to run

This folder contains `super_test_suite.py` — an enterprise-style test harness for the FastAPI `users` service.

This document explains how to run the harness from the repository root, using the project's virtual environment (`./venv`) or a fresh one. It shows both interactive runs and headless CI-friendly runs, plus an example `pytest` wrapper.

---

## Requirements / Assumptions
- Linux / macOS (commands shown for Debian); Windows instructions noted when relevant.
- Python 3.9+ recommended (3.8 may work).
- You have a Python venv at the project root `./venv` (this repo already contains one), or you can create a new one.
- The API under test should be reachable (default `http://localhost:8000`). Set `API_BASE_URL` to target another host/port.

---

## Files in this folder
- `super_test_suite.py` — the harness (interactive CLI + headless modes).
- `requirements-test.txt` — test dependencies (optional; provided below).
- `test_super_smoke.py` — minimal `pytest` wrapper to run the smoke test (optional).

---

## 1) Quick — activate venv and install deps (from repo root)
If you already have the venv at the project root:
```bash
# from repo root
source ./venv/bin/activate        # Debian / macOS
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# upgrade pip and install test deps
pip install --upgrade pip
pip install -r app/tests/requirements-test.txt
# (If you prefer the single command:)
# pip install requests rich pydantic python-jose pytest
````

If you do **not** have a venv and want to create one:

```bash
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r app/tests/requirements-test.txt
```

---

## 2) Configure the target API

Default target is `http://localhost:8000`. If your service runs elsewhere, export `API_BASE_URL` before running:

```bash
export API_BASE_URL="http://localhost:8000"    # Bash / Zsh
# Windows (PowerShell):
# $env:API_BASE_URL = "http://localhost:8000"
```

You can also set test log / export file names:

```bash
export TEST_LOGFILE="tests/super_test_suite.log"
export TEST_EXPORT_FILE="tests/smoke_result.json"
```

---

## 3) Start the API (if needed)

If your API runs inside Docker compose you can start it from repo root:

```bash
docker compose up -d              # starts services in background
# or selectively:
docker compose up -d web db
```

Confirm FastAPI is reachable:

```bash
curl -sS ${API_BASE_URL:-http://localhost:8000}/docs -I
# or
curl -sS ${API_BASE_URL:-http://localhost:8000}/ -I
```

---

## 4) Run the harness — interactive or headless

**Interactive (menu):**

```bash
# from repo root
python app/tests/super_test_suite.py
```

This opens a small menu where you can run a smoke test, auth flow, list users, batch tests, export results, etc.

**Headless (single smoke test):**

```bash
python app/tests/super_test_suite.py --smoke --export app/tests/smoke_result.json
```

**Headless (auth flow):**

```bash
python app/tests/super_test_suite.py --auth testuser@example.test --export app/tests/auth_result.json
```

**Batch run (n sequential runs):**

```bash
python app/tests/super_test_suite.py --batch 5 --export app/tests/batch_result.json
```

**Where logs go:** default `super_test_suite.log` in the current working directory (or set `TEST_LOGFILE`).

---

## 5) Run as a normal `pytest` test (CI-friendly)

Drop this simple wrapper (see `test_super_smoke.py` in this folder) and run:

```bash
# from repo root, with venv active
pytest -q app/tests/test_super_smoke.py
```

**Notes:**

* The wrapper ensures `API_BASE_URL` can be set via environment variable before import.
* The harness will attempt to create a user, exercise CRUD, and assert the smoke flow succeeds.

---

## 6) Minimal `pytest` wrapper example

(See `app/tests/test_super_smoke.py` in this directory.)

```python
import os
# ensure target URL is set before importing harness
os.environ.setdefault("API_BASE_URL", "http://localhost:8000")

from super_test_suite import run_smoke_test

def test_smoke():
    r = run_smoke_test()
    assert r.get("ok"), f"Smoke failed: {r.get('error')}"
```

---

## 7) CI recommendations

* Run harness in **headless** mode (`--smoke` or `--batch`), export artifact JSON, and store logs as CI artifacts.
* Use `API_BASE_URL` to point at your test environment.
* If tests create DB artifacts, ensure test DB teardown/cleanup or run against a disposable DB.

---

## 8) Troubleshooting quick cheatsheet

* `ModuleNotFoundError: requests` → `pip install requests`
* `Permission denied` running script → `chmod +x app/tests/super_test_suite.py` (or run with `python ...`)
* Unexpected 404/500 from API → confirm API is running and `API_BASE_URL` is correct; inspect `/docs` in browser.
* JWT decode fails → install `python-jose` (optional): `pip install python-jose`
* If `pydantic`/`rich` missing, the harness falls back to simpler behaviour — but install them for best UX.

---

## 9) Helpful environment variables

* `API_BASE_URL` — override default base URL (ex: `http://localhost:8000`)
* `TEST_LOGFILE` — log path (default `super_test_suite.log`)
* `TEST_EXPORT_FILE` — default export path for results

---

## 10) Next steps (optional)

* Convert to `httpx.AsyncClient` + `asyncio` for concurrent load tests.
* Add an OpenAPI-driven validator to assert responses against `openapi.json`.
* Wire into GitHub Actions / GitLab CI as a test step that runs `python ... --smoke`.

---

If you want, I will also produce the exact `requirements-test.txt` and `test_super_smoke.py` files below so you can copy them into this folder.

````

---

# `app/tests/requirements-test.txt`
```text
# Minimal extras for best experience with the test harness
requests>=2.28
rich>=13.0
pydantic>=1.10
python-jose>=3.3
pytest>=7.0
# Optional: httpx if you later convert to async
httpx>=0.24
````

---

# `app/tests/test_super_smoke.py` (pytest wrapper)

```python
import os
# Set default API target before importing the harness module
os.environ.setdefault("API_BASE_URL", "http://localhost:8000")

from super_test_suite import run_smoke_test

def test_smoke():
    r = run_smoke_test()
    assert r.get("ok"), f"Smoke failed: {r.get('error')}"
```

---

## Short usage summary (commands you can copy/paste)

```bash
# from repo root
source ./venv/bin/activate
pip install -r app/tests/requirements-test.txt
export API_BASE_URL="http://localhost:8000"

# run headless smoke:
python app/tests/super_test_suite.py --smoke --export app/tests/smoke_result.json

# or run with pytest:
pytest -q app/tests/test_super_smoke.py
```

---

If you’d like, I will now:

* generate the three files content ready to paste (I included them above), or
* create an alternate `pytest` wrapper that reads `TEST_LOGFILE` and archives logs, or
* convert the harness to an `async` `httpx` version for parallel tests.

Which enhancement shall I deduce next, Inspector Angel? 🕵️‍♂️
