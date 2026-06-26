#!/usr/bin/env python3
"""HelixNet Keycloak admin toolbox -- safe, idempotent, dry-run by default.

Two jobs for the identity cleanup + Artemis Premium cutover
(see docs/HELIX-IDENTITY-ARCHITECTURE.md):

  export-realm   P0 safe backup -- snapshot a realm to JSON BEFORE any delete.
                 Dry-run prints what's in the realm (counts); --apply writes the file.

  provision-business-account
                 ID5 realm-agnostic -- give a shop its La Piazza identity to
                 publish AS (VAT + business name + verified email -> a normal KC
                 user holding the lapiazza-business role). Prints the user id that
                 store_settings.lapiazza_business_id stores. After Phase 2 this
                 collapses to a plain role grant on an existing user.

DRY-RUN IS THE DEFAULT. Nothing writes to Keycloak (or disk) without --apply.
This is the seal-inspection rule made executable: prod KC holds 262 real logins
on borrowhood -- you preview, then you commit. Nothing outward-facing runs blind.

Run on dev:    python scripts/kc_admin.py export-realm fourtwenty
Write backup:  python scripts/kc_admin.py export-realm fourtwenty --apply
Provision:     python scripts/kc_admin.py provision-business-account \
                   --business-name "Artemis Store" --vat CHE-123.456.789 \
                   --email felix@artemis.example --realm lapiazza-realm-dev --apply

CLAUDE.md rule 11: Python-first, httpx + Typer + Pydantic.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import httpx
import typer
from pydantic import BaseModel, EmailStr, field_validator

app = typer.Typer(add_completion=False, help=__doc__)

# The role a verified shop holds on the Square to publish AS a business.
BUSINESS_ROLE = "lapiazza-business"


# --------------------------------------------------------------------------- #
# shared helpers (same idiom as scripts/lp_create_realm.py)                    #
# --------------------------------------------------------------------------- #
def _admin_token(c: httpx.Client, kc: str, user: str, pw: str) -> str:
    r = c.post(f"{kc}/realms/master/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": "admin-cli",
                     "username": user, "password": pw})
    r.raise_for_status()
    return r.json()["access_token"]


def _plan(msg: str) -> None:
    typer.secho(f"  WOULD {msg}", fg="yellow")


def _did(msg: str) -> None:
    typer.secho(f"  + {msg}", fg="green")


def _same(msg: str) -> None:
    typer.secho(f"  = {msg}", fg="bright_black")


# --------------------------------------------------------------------------- #
# command: list-realms  (read-only -- the reconciliation lens)                 #
# --------------------------------------------------------------------------- #
@app.command("list-realms")
def list_realms(
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option("helix_pass"),
    grep: str = typer.Option("", help="Only show realms whose id contains this substring"),
):
    """List every realm on a KC instance with counts -- nothing is written.

    The seal-inspection lens: before any identity change, see ALL the realms, not
    just the one on the ticket. For the box KC:

      python scripts/kc_admin.py list-realms \\
          --kc-url https://<box-kc-url> --admin-user <u> --admin-pass <p>
    """
    kc = kc_url.rstrip("/")
    with httpx.Client(verify=False, timeout=60.0) as c:
        h = {"Authorization": f"Bearer {_admin_token(c, kc, admin_user, admin_pass)}"}
        r = c.get(f"{kc}/admin/realms", headers=h)
        r.raise_for_status()
        rows = sorted(r.json(), key=lambda x: x["realm"])
        shown = [rm for rm in rows if not grep or grep in rm["realm"]]
        typer.secho(f"\n{len(rows)} realms on {kc}"
                    + (f"  ({len(shown)} match '{grep}')" if grep else ""),
                    fg="cyan", bold=True)
        for rm in shown:
            rid = rm["realm"]
            try:
                users = c.get(f"{kc}/admin/realms/{rid}/users/count", headers=h).json()
            except Exception:
                users = "?"
            try:
                clients = len(c.get(f"{kc}/admin/realms/{rid}/clients", headers=h).json())
            except Exception:
                clients = "?"
            flag = "on " if rm.get("enabled") else "OFF"
            disp = rm.get("displayName") or ""
            typer.echo(f"  [{flag}] {rid:<28} users={str(users):<5} clients={str(clients):<3} {disp}")
        typer.secho("\nread-only -- nothing written.", fg="bright_black")


# --------------------------------------------------------------------------- #
# command: export-realm  (P0 safe backup)                                      #
# --------------------------------------------------------------------------- #
@app.command("export-realm")
def export_realm(
    realm: str = typer.Argument(..., help="Realm id to snapshot (e.g. fourtwenty)"),
    apply: bool = typer.Option(False, "--apply", help="Write the backup file (default: dry-run, preview only)"),
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option("helix_pass"),
    out_dir: Path = typer.Option(Path("backups/kc"), help="Where to write the JSON snapshot"),
):
    """Snapshot a realm (clients + roles + groups + users) to JSON before deleting it.

    Dry-run prints a summary so you can confirm you're backing up the RIGHT realm.
    --apply writes backups/kc/<realm>-<UTC>.json via KC partial-export.
    """
    kc = kc_url.rstrip("/")
    with httpx.Client(verify=False, timeout=60.0) as c:
        h = {"Authorization": f"Bearer {_admin_token(c, kc, admin_user, admin_pass)}"}
        base = f"{kc}/admin/realms"
        # confirm the realm exists + summarize it (read-only)
        r = c.get(f"{base}/{realm}", headers=h)
        if r.status_code == 404:
            typer.secho(f"❌ realm '{realm}' not found on {kc}", fg="red", bold=True)
            raise typer.Exit(1)
        r.raise_for_status()
        info = r.json()

        users = c.get(f"{base}/{realm}/users/count", headers=h).json()
        clients = c.get(f"{base}/{realm}/clients", headers=h).json()
        roles = c.get(f"{base}/{realm}/roles", headers=h).json()

        typer.secho(f"\nRealm '{realm}' on {kc}", fg="cyan", bold=True)
        typer.echo(f"  enabled:  {info.get('enabled')}")
        typer.echo(f"  display:  {info.get('displayName') or '(none)'}")
        typer.echo(f"  users:    {users}")
        typer.echo(f"  clients:  {len(clients)}")
        typer.echo(f"  roles:    {len(roles)}")

        if not apply:
            dest = out_dir / f"{realm}-<UTC>.json"
            _plan(f"export realm '{realm}' -> {dest}  (re-run with --apply to write)")
            typer.secho("\nDRY-RUN -- nothing written. Add --apply to take the backup.", fg="yellow", bold=True)
            return

        # --apply: take the real partial export (realm config + clients + roles + groups)
        exp = c.post(
            f"{base}/{realm}/partial-export",
            headers=h,
            params={"exportClients": "true", "exportGroupsAndRoles": "true"},
        )
        exp.raise_for_status()
        snapshot = exp.json()

        # partial-export OMITS users -- page through /users and embed them ourselves,
        # else the "backup" can't restore a single account. Each user's realm-role
        # mappings come along too, so re-import rebuilds who-had-what.
        # NOTE: credential hashes are NOT returned by the admin REST API, so restored
        # users would need a password reset. For these dead realms that's acceptable;
        # the point is to preserve identity + attributes + role mappings.
        embedded, page, PAGE = [], 0, 100
        while True:
            batch = c.get(f"{base}/{realm}/users", headers=h,
                          params={"first": page * PAGE, "max": PAGE}).json()
            if not batch:
                break
            for u in batch:
                rm = c.get(f"{base}/{realm}/users/{u['id']}/role-mappings/realm",
                           headers=h).json()
                u["realmRoles"] = [r["name"] for r in rm]
            embedded.extend(batch)
            if len(batch) < PAGE:
                break
            page += 1
        snapshot["users"] = embedded

        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dest = out_dir / f"{realm}-{stamp}.json"
        dest.write_text(json.dumps(snapshot, indent=2))
        _did(f"wrote {dest}  ({dest.stat().st_size:,} bytes, {len(embedded)} users embedded)")
        if len(embedded) != users:
            typer.secho(f"  ⚠ embedded {len(embedded)} users but realm reports {users} -- check before deleting",
                        fg="red")
        typer.secho(f"\n✅ realm '{realm}' backed up (config+clients+roles+{len(embedded)} users). "
                    f"Re-import to restore; users need a password reset (hashes not exported).",
                    fg="green", bold=True)


# Realms that must NEVER be deleted by this tool, regardless of flags.
# borrowhood = prod (262 real logins); borrowhood-staging = the unified staging door.
PROTECTED_REALMS = {"borrowhood", "borrowhood-staging", "master"}


# --------------------------------------------------------------------------- #
# command: delete-realm  (P0 -- only after export, never a protected realm)    #
# --------------------------------------------------------------------------- #
@app.command("delete-realm")
def delete_realm(
    realm: str = typer.Argument(..., help="Dead realm id to remove (e.g. fourtwenty, blowup)"),
    apply: bool = typer.Option(False, "--apply", help="Actually delete (default: dry-run, preview only)"),
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option("helix_pass"),
    backup_dir: Path = typer.Option(Path("backups/kc"), help="Where export-realm wrote the JSON backup"),
):
    """Delete a dead realm -- but ONLY if a backup exists and it isn't protected.

    Two hard gates, both un-skippable:
      1. PROTECTED_REALMS (borrowhood / borrowhood-staging / master) are refused outright.
      2. --apply refuses unless backups/kc/<realm>-*.json exists -- you must export first.
    Dry-run shows exactly what would happen. This is Phase 0 of the cleanup roadmap.
    """
    if realm in PROTECTED_REALMS:
        typer.secho(f"❌ '{realm}' is PROTECTED -- this tool will never delete it.", fg="red", bold=True)
        raise typer.Exit(2)

    backups = sorted(backup_dir.glob(f"{realm}-*.json"))
    kc = kc_url.rstrip("/")
    with httpx.Client(verify=False, timeout=60.0) as c:
        h = {"Authorization": f"Bearer {_admin_token(c, kc, admin_user, admin_pass)}"}
        base = f"{kc}/admin/realms"
        r = c.get(f"{base}/{realm}", headers=h)
        if r.status_code == 404:
            typer.secho(f"= realm '{realm}' already gone on {kc} -- nothing to do.", fg="bright_black")
            return
        r.raise_for_status()
        users = c.get(f"{base}/{realm}/users/count", headers=h).json()

        typer.secho(f"\nDelete realm '{realm}' from {kc}", fg="cyan", bold=True)
        typer.echo(f"  users:   {users}")
        typer.echo(f"  backup:  {backups[-1] if backups else '(NONE FOUND)'}")

        if not backups:
            typer.secho(f"\n❌ no backup at {backup_dir}/{realm}-*.json -- run "
                        f"'export-realm {realm} --apply' first.", fg="red", bold=True)
            raise typer.Exit(1)

        if not apply:
            _plan(f"DELETE realm '{realm}' ({users} users)  -- backup present, safe to --apply")
            typer.secho("\nDRY-RUN -- nothing deleted. Add --apply to remove.", fg="yellow", bold=True)
            return

        c.delete(f"{base}/{realm}", headers=h).raise_for_status()
        _did(f"realm '{realm}' deleted (restore from {backups[-1]} if needed)")
        typer.secho(f"\n✅ realm '{realm}' removed. Backup retained at {backups[-1]}.", fg="green", bold=True)


# --------------------------------------------------------------------------- #
# command: provision-business-account  (ID5, realm-agnostic)                   #
# --------------------------------------------------------------------------- #
class BusinessAccount(BaseModel):
    """The shape of a shop's La Piazza business identity. Validated before any KC call."""
    business_name: str
    vat: str
    email: EmailStr
    username: str

    @field_validator("vat")
    @classmethod
    def _vat_shape(cls, v: str) -> str:
        v = v.strip()
        # Swiss UID/VAT: CHE-123.456.789 (MWST optional). Be lenient but non-empty.
        if not v or len(v) < 6:
            raise ValueError("VAT number looks too short -- expected e.g. CHE-123.456.789")
        return v

    @field_validator("business_name")
    @classmethod
    def _name_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("business_name must not be empty")
        return v.strip()


def _username_from(email: str) -> str:
    """Stable, readable username from the verifiable email (the shop's unique handle)."""
    local = email.split("@", 1)[0].lower()
    return "biz-" + re.sub(r"[^a-z0-9]+", "-", local).strip("-")


@app.command("provision-business-account")
def provision_business_account(
    business_name: str = typer.Option(..., "--business-name", help="The shop's legal/display name"),
    vat: str = typer.Option(..., "--vat", help="VAT / UID number, e.g. CHE-123.456.789"),
    email: str = typer.Option(..., "--email", help="Verifiable business email (the unique identifier)"),
    apply: bool = typer.Option(False, "--apply", help="Create/assign in Keycloak (default: dry-run, preview only)"),
    realm: str = typer.Option("lapiazza-realm-dev", help="Target La Piazza realm FOR THIS ENV (realm-agnostic by design)"),
    username: str = typer.Option("", help="Override the derived username (default: biz-<email-local>)"),
    role: str = typer.Option(BUSINESS_ROLE, help="Role granted to publish AS a business"),
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option("helix_pass"),
):
    """Give a shop a La Piazza identity to publish AS -- a normal KC user + business attributes.

    The account is keyed by the verifiable EMAIL. Idempotent: re-running finds the
    existing account and ensures the role + attributes, never duplicates. Prints the
    user id -> store_settings.lapiazza_business_id. Realm-agnostic: point --realm at
    this environment's La Piazza realm (dev/staging/prod). After identity Phase 2 this
    becomes a plain role grant on the shop owner's existing account.
    """
    acct = BusinessAccount(
        business_name=business_name, vat=vat, email=email,
        username=username.strip() or _username_from(email),
    )
    attrs = {
        "account_type": ["business"],
        "business_name": [acct.business_name],
        "vat_number": [acct.vat],
    }

    typer.secho(f"\nBusiness account for '{acct.business_name}'", fg="cyan", bold=True)
    typer.echo(f"  realm:     {realm}  ({'PROD -- 262 real logins' if realm == 'borrowhood' else 'non-prod'})")
    typer.echo(f"  username:  {acct.username}")
    typer.echo(f"  email:     {acct.email}")
    typer.echo(f"  vat:       {acct.vat}")
    typer.echo(f"  role:      {role}")

    kc = kc_url.rstrip("/")
    with httpx.Client(verify=False, timeout=60.0) as c:
        h = {"Authorization": f"Bearer {_admin_token(c, kc, admin_user, admin_pass)}"}
        base = f"{kc}/admin/realms"
        if c.get(f"{base}/{realm}", headers=h).status_code == 404:
            typer.secho(f"❌ realm '{realm}' not found on {kc}", fg="red", bold=True)
            raise typer.Exit(1)

        # find existing by email first (the true key), then by username
        found = c.get(f"{base}/{realm}/users", headers=h,
                      params={"email": acct.email, "exact": "true"}).json()
        if not found:
            found = c.get(f"{base}/{realm}/users", headers=h,
                          params={"username": acct.username, "exact": "true"}).json()

        role_exists = c.get(f"{base}/{realm}/roles/{role}", headers=h).status_code != 404

        if not apply:
            _plan(f"ensure role '{role}'" + ("" if role_exists else "  (role missing -- would create)"))
            if found:
                _plan(f"update existing user {found[0]['id']} (attrs + role)")
            else:
                _plan(f"create user '{acct.username}' with business attributes + role")
            typer.secho("\nDRY-RUN -- nothing written. Add --apply to provision.", fg="yellow", bold=True)
            return

        # --apply ------------------------------------------------------------
        # 1) ensure the business role exists in this realm
        if not role_exists:
            c.post(f"{base}/{realm}/roles", headers=h, json={"name": role}).raise_for_status()
            _did(f"role '{role}' created")
        else:
            _same(f"role '{role}' exists")

        # 2) ensure the user
        if not found:
            c.post(f"{base}/{realm}/users", headers=h, json={
                "username": acct.username, "enabled": True, "emailVerified": True,
                "email": acct.email, "firstName": acct.business_name, "lastName": "(business)",
                "attributes": attrs, "requiredActions": [],
            }).raise_for_status()
            found = c.get(f"{base}/{realm}/users", headers=h,
                          params={"username": acct.username, "exact": "true"}).json()
            _did(f"user '{acct.username}' created")
        else:
            _same(f"user '{acct.username}' exists -- updating attributes")
        uid = found[0]["id"]

        # 3) ensure attributes + verified email on the user (idempotent merge)
        c.put(f"{base}/{realm}/users/{uid}", headers=h, json={
            "enabled": True, "emailVerified": True, "email": acct.email,
            "attributes": attrs, "requiredActions": [],
        }).raise_for_status()

        # 4) grant the business role
        role_obj = c.get(f"{base}/{realm}/roles/{role}", headers=h).json()
        c.post(f"{base}/{realm}/users/{uid}/role-mappings/realm", headers=h,
               json=[role_obj]).raise_for_status()
        _did(f"{acct.username} holds '{role}'")

        typer.secho(f"\n✅ business account ready in realm '{realm}'.", fg="green", bold=True)
        typer.secho(f"   lapiazza_business_id = {uid}", fg="cyan", bold=True)
        typer.echo("   -> store this on store_settings.lapiazza_business_id for the shop.")


if __name__ == "__main__":
    app()
