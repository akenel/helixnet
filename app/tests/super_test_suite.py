#!/usr/bin/env python3
"""
super_test_suite.py — Sherlock's Enterprise Test Harness for FastAPI Users Service
✨ Purpose:
  - Provide an interactive and scriptable test runner for /users endpoints and auth.
  - Clean JSON logs, retries, validation, helpful emojis, and small menu-driven UI.

Features:
  - CRUD flow (Create / Read / Update / Delete)
  - JWT token acquisition and validation (if python-jose is installed)
  - Structured logging (JSON lines) + human friendly output via 'rich' if available
  - Config via environment variables or interactive menu
  - Retry/backoff for flaky networks
  - Export results (JSON file)
  - Headless mode for CI (run full test with CLI flags)
Author: Sherlock (your detective-y tester)
"""

from __future__ import annotations
import os
import sys
import time
import json
import uuid
import random
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta

# Third-party modules — optional but strongly recommended
try:
    import requests
except Exception as e:
    print("ERROR: 'requests' library is required. Install with: pip install requests")
    raise

# Optional extras
try:
    from pydantic import BaseModel, EmailStr, ValidationError, Field
    HAVE_PYDANTIC = True
except Exception:
    HAVE_PYDANTIC = False

try:
    from jose import jwt as jose_jwt
    HAVE_JOSE = True
except Exception:
    HAVE_JOSE = False

try:
    from rich import print as rprint
    from rich.table import Table
    from rich.console import Console
    HAVE_RICH = True
    console = Console()
except Exception:
    HAVE_RICH = False

# ------------------------------
# LOGGING: JSONL + human console
# ------------------------------
LOGFILE = os.environ.get("TEST_LOGFILE", "super_test_suite.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOGFILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

def log_event(level: str, msg: str, **extra):
    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": msg,
        **extra
    }
    logging.getLogger().log(getattr(logging, level.upper(), logging.INFO), json.dumps(payload))
    # also pretty-print for humans when rich available
    if HAVE_RICH:
        if level.lower() == "info":
            console.print(f"ℹ️  [bold cyan]{msg}[/bold cyan]")
        elif level.lower() == "warning":
            console.print(f"⚠️  [bold yellow]{msg}[/bold yellow]")
        elif level.lower() == "error":
            console.print(f"❌ [bold red]{msg}[/bold red]")
        else:
            console.print(msg)

# ------------------------------
# CONFIG
# ------------------------------
@dataclass
class Config:
    base_url: str = os.environ.get("API_BASE_URL", "http://localhost:8000")
    timeout: int = int(os.environ.get("API_TIMEOUT", "10"))
    default_password: str = os.environ.get("TEST_DEFAULT_PASSWORD", "ChangeMe123!")
    export_file: str = os.environ.get("TEST_EXPORT_FILE", "test_results.json")
    verbose: bool = os.environ.get("TEST_VERBOSE", "1") in ("1", "true", "True")
    use_ssl_verify: bool = os.environ.get("TEST_SSL_VERIFY", "1") in ("1", "true", "True")
    default_concurrency: int = int(os.environ.get("TEST_CONCURRENCY", "5"))

cfg = Config()

# ------------------------------
# Pydantic models (for validation)
# ------------------------------
if HAVE_PYDANTIC:
    class UserCreate(BaseModel):
        email: EmailStr
        password: str = Field(min_length=8)

    class UserOut(BaseModel):
        id: uuid.UUID
        email: EmailStr
        created_at: Optional[datetime]

    class TokenOut(BaseModel):
        access_token: str
        token_type: str

else:
    # Fallback naive validators if pydantic is missing
    class UserCreate:
        def __init__(self, email: str, password: str):
            if "@" not in email:
                raise ValueError("Invalid email")
            if len(password) < 8:
                raise ValueError("Password too short")
            self.email = email
            self.password = password

    class UserOut:
        pass

    class TokenOut:
        pass

# ------------------------------
# Utilities: retry/backoff, pretty outputs
# ------------------------------
def retry(fn: Callable, attempts: int = 3, delay: float = 0.5, backoff: float = 2.0):
    """Retry helper with exponential backoff. Returns (success, result_or_exception)."""
    last_exc = None
    for i in range(attempts):
        try:
            return True, fn()
        except Exception as e:
            last_exc = e
            wait = delay * (backoff ** i)
            log_event("warning", f"Attempt {i+1}/{attempts} failed: {e!s}. Retrying in {wait:.2ff}s ⏳")
            time.sleep(wait)
    return False, last_exc

def pretty_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return str(obj)

def pretty_print_table(rows: List[Dict[str, Any]], title: str = "Results"):
    if HAVE_RICH:
        table = Table(title=title)
        # choose columns from first row
        if not rows:
            console.print("No rows to display.")
            return
        # Use a list of common keys to maintain order
        common_keys = ["id", "email", "ok", "steps", "status_code", "count"]
        
        # Get all unique keys across all rows
        all_keys = list({k for r in rows for k in r.keys()})
        
        # Build the final column list, prioritizing common keys
        cols = [k for k in common_keys if k in all_keys] + [k for k in all_keys if k not in common_keys]

        for c in cols:
            table.add_column(c)
        for r in rows:
            table.add_row(*[str(r.get(c, "")) for c in cols])
        console.print(table)
    else:
        print(title)
        for r in rows:
            print(pretty_json(r))

# ------------------------------
# HTTP Client wrappers
# ------------------------------
SESSION = requests.Session()
SESSION.headers.update({"accept": "application/json"})
SESSION.verify = cfg.use_ssl_verify

def url(path: str) -> str:
    return cfg.base_url.rstrip("/") + "/" + path.lstrip("/")

def http_post(path: str, json_payload=None, headers=None, timeout=None):
    timeout = timeout or cfg.timeout
    # Send JSON data
    return SESSION.post(url(path), json=json_payload, headers=headers or {}, timeout=timeout)

def http_post_form(path: str, data_payload=None, headers=None, timeout=None):
    timeout = timeout or cfg.timeout
    # Send form-encoded data (required for OAuth2PasswordRequestForm)
    # The 'Content-Type': 'application/x-www-form-urlencoded' header is usually added automatically by requests
    return SESSION.post(url(path), data=data_payload, headers=headers or {}, timeout=timeout)

def http_get(path: str, headers=None, timeout=None):
    timeout = timeout or cfg.timeout
    return SESSION.get(url(path), headers=headers or {}, timeout=timeout)

def http_patch(path: str, json_payload=None, headers=None, timeout=None):
    timeout = timeout or cfg.timeout
    return SESSION.patch(url(path), json=json_payload, headers=headers or {}, timeout=timeout)

def http_delete(path: str, headers=None, timeout=None):
    timeout = timeout or cfg.timeout
    return SESSION.delete(url(path), headers=headers or {}, timeout=timeout)

# ------------------------------
# Core test operations
# ------------------------------
def create_user(email: str, password: Optional[str] = None) -> Dict[str, Any] | UserOut:
    """Create a user via POST /users/ — returns parsed JSON or raises on unexpected response."""
    password = password or cfg.default_password
    payload = {"email": email, "password": password}
    log_event("info", f"Creating user {email} 🧾")
    ok, res = retry(lambda: http_post("/users/", json_payload=payload), attempts=3)
    if not ok:
        raise RuntimeError(f"Failed to POST /users/: {res}")
    resp = res
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Create user failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    # validate shape
    if HAVE_PYDANTIC:
        try:
            # Return Pydantic object
            user = UserOut.parse_obj(data)
            log_event("info", f"User created ✅ id={user.id}")
            return user
        except ValidationError as ve:
            log_event("warning", "Response validation failed for created user. Continuing with raw data.")
            # Fallback to raw data if validation fails
            return data
    else:
        user = data
    return user

def list_users() -> List[Dict[str, Any]]:
    log_event("info", "Listing users 🔎")
    # This call now relies on the SESSION having the Authorization header set by run_smoke_test
    ok, res = retry(lambda: http_get("/users/"), attempts=2)
    if not ok:
        raise RuntimeError(f"Failed to GET /users/: {res}")
    resp = res
    if resp.status_code not in (200,):
        raise RuntimeError(f"List users failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    return data

def get_user(user_id: str) -> Dict[str, Any]:
    log_event("info", f"Getting user {user_id} 🧭")
    # This call now relies on the SESSION having the Authorization header set
    ok, res = retry(lambda: http_get(f"/users/{user_id}"), attempts=2)
    if not ok:
        raise RuntimeError(f"Failed to GET /users/{user_id}: {res}")
    resp = res
    if resp.status_code != 200:
        raise RuntimeError(f"Get user failed ({resp.status_code}): {resp.text}")
    return resp.json()

def update_user(user_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    log_event("info", f"Patching user {user_id} ✏️  patch={patch}")
    # This call now relies on the SESSION having the Authorization header set
    ok, res = retry(lambda: http_patch(f"/users/{user_id}", json_payload=patch), attempts=2)
    if not ok:
        raise RuntimeError(f"Failed to PATCH /users/{user_id}: {res}")
    resp = res
    if resp.status_code not in (200,):
        raise RuntimeError(f"Update user failed ({resp.status_code}): {resp.text}")
    return resp.json()

def delete_user(user_id: str) -> int:
    log_event("info", f"Deleting user {user_id} 🧹")
    # This call now relies on the SESSION having the Authorization header set
    ok, res = retry(lambda: http_delete(f"/users/{user_id}"), attempts=2)
    if not ok:
        raise RuntimeError(f"Failed to DELETE /users/{user_id}: {res}")
    resp = res
    if resp.status_code not in (204, 200):
        raise RuntimeError(f"Delete user failed ({resp.status_code}): {resp.text}")
    return resp.status_code

# ------------------------------
# Authentication helpers
# ------------------------------
def obtain_token(email: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    POST /token or /auth/token depending on your implementation.
    This tries common patterns and returns token dict {access_token, token_type}.
    """
    password = password or cfg.default_password
    log_event("info", f"Requesting token for {email} 🔐")
    
    # Priority order for token endpoints
    # 1. Standard OAuth2 paths
    # 2. Paths under /users/ (since user CRUD is there)
    # 3. Generic paths
    candidates = [
        {"path": "/token", "type": "form"},
        {"path": "/auth/token", "type": "form"},
        {"path": "/users/token", "type": "form"}, # <-- NEW highly probable candidate
        {"path": "/users/login", "type": "form"}, # <-- NEW highly probable candidate
        {"path": "/login", "type": "form"},
        {"path": "/login", "type": "json"},
    ]

    last_exc = None
    for item in candidates:
        path = item["path"]
        req_type = item["type"]
        log_event("info", f"Attempting POST {path} ({req_type})")
        
        try:
            payload = {"username": email, "password": password}
            
            if req_type == "form":
                # OAuth2 requires form data with 'username' and 'password'
                ok, res = retry(lambda p=path: http_post_form(p, data_payload=payload), attempts=1)
            else: # json
                # JSON endpoints often use 'email' not 'username'
                payload_json = {"email": email, "password": password}
                ok, res = retry(lambda p=path: http_post(p, json_payload=payload_json), attempts=1)

            if not ok:
                last_exc = res
                log_event("warning", f"Failed to connect to {path}: {res!s}")
                continue
            
            resp = res
            
            if resp.status_code in (200,):
                data = resp.json()
                # Basic validation
                if "access_token" in data:
                    log_event("info", f"Token obtained successfully via {path} ✅")
                    return data
                else:
                    last_exc = f"Response from {path} (200 OK) was missing 'access_token'"
                    log_event("warning", last_exc)
                    continue
            else:
                # If path returns a status code (e.g., 404 Not Found, 401 Unauthorized), save it
                error_detail = resp.json().get("detail", resp.text.strip()) if resp.text else ""
                last_exc = f"{path} returned status {resp.status_code}. Detail: {error_detail}"
                log_event("warning", f"Path {path} failed: Status {resp.status_code}. Detail: {error_detail[:50]}...")
                continue
        except Exception as e:
            last_exc = e
            log_event("warning", f"Path {path} failed with connection error: {e!s}")
            continue
            
    raise RuntimeError(f"Could not obtain token. Last error: {last_exc}")

def decode_jwt_if_possible(access_token: str, skip_print: bool = False) -> Optional[Dict[str, Any]]:
    if not HAVE_JOSE:
        if not skip_print:
            log_event("warning", "python-jose not installed; cannot decode JWT. Install 'python-jose' to decode tokens.")
        return None
    try:
        # NOTE: We cannot verify signature without secret — use options to skip signature verification for inspection.
        data = jose_jwt.get_unverified_claims(access_token)
        if not skip_print:
            log_event("info", f"Decoded JWT claims: {data}")
        return data
    except Exception as e:
        log_event("warning", f"Failed to decode JWT: {e}")
        return None

# ------------------------------
# High-level test flows
# ------------------------------
def run_smoke_test(seed_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Single-run smoke test:
      - create user
      - login user and get token (CRITICAL NEW STEP)
      - list users (authenticated)
      - get user (authenticated)
      - patch user (authenticated)
      - delete user (authenticated)
      - attempt to GET deleted user (expect 404)
    Returns a structured result dict (good for CI).
    """
    results = {"steps": [], "ok": True}
    # Store original header to restore later, ensuring test isolation
    original_auth_header = SESSION.headers.get("Authorization") 

    try:
        # FIX: Use a non-reserved TLD like @test.com to pass strict Pydantic validation
        email = seed_email or f"test_{uuid.uuid4().hex[:8]}@test.com"
        
        # 1. CREATE USER
        created = create_user(email=email)
        
        # Safely extract ID
        uid = None
        if HAVE_PYDANTIC and isinstance(created, UserOut):
            uid = str(created.id)
        elif isinstance(created, dict):
            # Fallback to dict keys
            uid = str(created.get('id', created.get('user_id')))

        if not uid:
             raise RuntimeError(f"Could not determine user ID from created object: {created}")

        results["steps"].append({"name": "create", "email": email, "result": created})
        
        # 2. OBTAIN TOKEN AND AUTHENTICATE SESSION (The fix for 401)
        token_data = obtain_token(email=email, password=cfg.default_password)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise RuntimeError("Failed to obtain access token after user creation.")
            
        # Set the Authorization header for all subsequent authenticated requests
        SESSION.headers.update({"Authorization": f"Bearer {access_token}"})
        log_event("info", f"Session authenticated with token for user {email} 🔑")
        results["steps"].append({"name": "auth", "status": "success"})


        # 3. Authenticated CRUD Operations
        
        # list
        users = list_users()
        results["steps"].append({"name": "list", "count": len(users)})
        
        # get
        fetched = get_user(uid)
        results["steps"].append({"name": "get", "user": fetched})
        
        # patch
        new_email = f"patched.{random.randint(1000,9999)}@test.com" # Use test.com
        updated = update_user(uid, {"email": new_email})
        results["steps"].append({"name": "update", "user": updated})
        
        # delete
        code = delete_user(uid)
        results["steps"].append({"name": "delete", "status_code": code})
        
        # final GET should 404 (we'll try and consider that an expected error)
        try:
            # We explicitly want this authenticated GET to fail with 404
            get_user(uid) 
            # If we get here, delete didn't work
            results["ok"] = False
            results["steps"].append({"name": "post-delete-get", "unexpected": "user still exists"})
            log_event("error", "DELETE appears not to have removed user ❗")
        except Exception as e:
            # Expected failure
            results["steps"].append({"name": "post-delete-get", "expected_error": str(e)})
            log_event("info", "Confirmed deletion (GET after delete failed as expected). ✅")
            
    except Exception as e:
        results["ok"] = False
        results["error"] = str(e)
        log_event("error", f"Smoke test failed: {e}")
    finally:
        # 4. CLEANUP: Reset the Authorization header on the session
        if original_auth_header is None:
            if "Authorization" in SESSION.headers:
                del SESSION.headers["Authorization"]
        elif original_auth_header:
            SESSION.headers["Authorization"] = original_auth_header
        
    return results

def run_auth_flow(email: str, password: Optional[str] = None) -> Dict[str, Any]:
    """Try to create user (if needed) and obtain token; decode token if possible."""
    res = {"ok": True}
    try:
        # create user (idempotent if email already exists might fail)
        try:
            created = create_user(email=email, password=password)
            res["created"] = created
        except Exception as e:
            res["created_error"] = str(e)
            log_event("warning", f"Could not create user (maybe exists): {e}")
        token = obtain_token(email=email, password=password)
        res["token"] = token
        decode = decode_jwt_if_possible(token.get("access_token"))
        res["decoded_claims"] = decode
    except Exception as e:
        res["ok"] = False
        res["error"] = str(e)
        log_event("error", f"Auth flow failed: {e}")
    return res

def run_batch_smoke(count: int = 10) -> Dict[str, Any]:
    """Run multiple smoke tests in sequence (not parallel) and return aggregated results."""
    agg = {"count": count, "results": [], "ok": True}
    for i in range(count):
        log_event("info", f"Batch test {i+1}/{count} — starting 🔁")
        res = run_smoke_test()
        agg["results"].append(res)
        if not res.get("ok", False):
            agg["ok"] = False
    log_event("info", f"Batch complete. {count} runs. Success={agg['ok']}")
    return agg

# ------------------------------
# CLI / Menu
# ------------------------------
def interactive_menu():
    banner = """
🕵️‍♂️  Sherlock's Super Test Suite Version 0.0.6 — interactive menu
Please choose an action:
  [1] Run single smoke test (create -> get -> patch -> delete)
  [2] Run auth flow (create user -> obtain token -> decode)
  [3] List users
  [4] Run batch smoke tests
  [5] Export example: run one smoke test and save JSON
  [6] Update config (base URL, timeout)
  [0] Exit
"""
    while True:
        print(banner)
        choice = input("Enter choice > ").strip()
        if choice == "1":
            email = input("Email to create (blank for random): ").strip() or None
            result = run_smoke_test(seed_email=email)
            pretty_print_table([{"ok": result.get("ok"), "steps": len(result.get("steps", []))}], title="Smoke summary")
            print(pretty_json(result))
        elif choice == "2":
            email = input("Email to test auth (required): ").strip()
            if not email:
                print("Email required for auth flow.")
                continue
            password = input("Password (blank to use default): ").strip() or None
            result = run_auth_flow(email=email, password=password)
            print(pretty_json(result))
        elif choice == "3":
            users = list_users()
            pretty_print_table(users, title="Users")
        elif choice == "4":
            n = input(f"How many runs? (default {cfg.default_concurrency}) > ").strip()
            n = int(n) if n and n.isdigit() else cfg.default_concurrency
            result = run_batch_smoke(n)
            open(cfg.export_file, "w", encoding="utf-8").write(json.dumps(result, indent=2, default=str))
            log_event("info", f"Batch saved to {cfg.export_file}")
        elif choice == "5":
            r = run_smoke_test()
            with open(cfg.export_file, "w", encoding="utf-8") as fh:
                json.dump(r, fh, indent=2, default=str)
            log_event("info", f"Exported last smoke to {cfg.export_file} 📦")
        elif choice == "6":
            change_config()
        elif choice == "0":
            log_event("info", "Goodbye! 🕯️")
            break
        else:
            print("Unknown option.")

def change_config():
    print("Current config:")
    print(pretty_json(asdict(cfg)))
    new_base = input(f"Base URL [{cfg.base_url}]: ").strip()
    if new_base:
        cfg.base_url = new_base
    new_timeout = input(f"Timeout seconds [{cfg.timeout}]: ").strip()
    if new_timeout.isdigit():
        cfg.timeout = int(new_timeout)
    log_event("info", "Configuration updated.")

# ------------------------------
# Command-line entrypoint
# ------------------------------
def main(argv: Optional[List[str]] = None):
    argv = argv or sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser(prog="super_test_suite", description="Enterprise test harness for FastAPI users")
    parser.add_argument("--base-url", help="API base URL (overrides env/API_BASE_URL)")
    parser.add_argument("--smoke", action="store_true", help="Run a single smoke test and exit (headless)")
    parser.add_argument("--auth", nargs=1, metavar=("EMAIL",), help="Run auth flow for EMAIL")
    parser.add_argument("--batch", type=int, help="Run n smoke tests sequentially")
    parser.add_argument("--export", help="Write last result to file (path)")
    parser.add_argument("--no-interactive", action="store_true", help="Do not start interactive menu")
    args = parser.parse_args(argv)

    if args.base_url:
        cfg.base_url = args.base_url

    if args.smoke:
        log_event("info", "Running headless smoke test 🧪")
        r = run_smoke_test()
        out = args.export or cfg.export_file
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=2, default=str)
        log_event("info", f"Smoke result written to {out}")
        print(pretty_json(r))
        # If the smoke test failed, return a non-zero exit code
        return 0 if r.get("ok") else 1

    if args.auth:
        email = args.auth[0]
        r = run_auth_flow(email=email)
        if args.export:
            with open(args.export, "w", encoding="utf-8") as fh:
                json.dump(r, fh, indent=2, default=str)
            log_event("info", f"Auth result exported to {args.export}")
        print(pretty_json(r))
        return 0

    if args.batch:
        log_event("info", f"Running batch of {args.batch} smoke tests")
        r = run_batch_smoke(args.batch)
        out = args.export or cfg.export_file
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=2, default=str)
        log_event("info", f"Batch written to {out}")
        print(pretty_json(r))
        return 0

    if not args.no_interactive:
        interactive_menu()
    else:
        log_event("info", "No action taken. Use --smoke or --batch or run without --no-interactive for menu.")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log_event("info", "Interrupted by user. Farewell. 🕯️")
        sys.exit(130)
