#!/usr/bin/env python3
"""Clone the POS Keycloak realm into a per-environment realm (the realm split).

Carves `kc-pos-realm-stg` / `kc-pos-realm-prd` out of `kc-pos-realm-dev` so staging and prod
each get their own realm (own SMTP, own login, own blast radius) — the locked identity
north-star (realm = environment). See docs/BANCO-POS-REALM-SPLIT-PLAN.md.

What it copies: the realm's login settings (curated subset) + the `helix_pos_web` client (with
redirect URIs TRIMMED to the target env's host) + the POS realm roles (the emoji pos-* roles).
What it does NOT copy: users (re-provisioned via Banco's Staff tab) and SMTP (set afterwards
with configure_kc_smtp.py — dev/sbx=MailHog, staging/prod=Resend).

It is idempotent-ish: re-running skips the realm/client/roles that already exist (logs SKIP),
so a half-finished run is safe to repeat. Optionally seeds ONE bootstrap admin so you can log
in and provision the rest from the UI.

Admin auth: --admin-user + password from $KC_ADMIN_PASSWORD (preferred, for automation) or a
getpass prompt.

Example (run inside a box container that can reach keycloak:8080):
  KC_ADMIN_PASSWORD=... python clone_pos_realm.py \
    --kc-url http://keycloak:8080 --src kc-pos-realm-dev --dst kc-pos-realm-stg \
    --host staging-banco.lapiazza.app --frontend-url https://lapiazza.app \
    --seed-admin felix --seed-email angel.kenel@gmail.com --seed-password helix_pass
"""
from __future__ import annotations

import getpass
import os
import sys

import httpx
import typer

app = typer.Typer(add_completion=False, help=__doc__)

# The POS realm roles we carry over (the emoji-prefixed ones). KC auto-creates the defaults
# (default-roles-*, offline_access, uma_authorization), so we skip those by substring.
_SKIP_ROLE_SUBSTR = ("default-roles", "offline_access", "uma_authorization")


def _token(c: httpx.Client, kc_url: str, admin_user: str, admin_pass: str) -> str:
    r = c.post(f"{kc_url.rstrip('/')}/realms/master/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": "admin-cli",
                     "username": admin_user, "password": admin_pass})
    if r.status_code != 200:
        typer.secho(f"✗ Admin login failed ({r.status_code}): {r.text[:200]}", fg="red")
        raise typer.Exit(1)
    return r.json()["access_token"]


@app.command()
def main(
    kc_url: str = typer.Option(..., "--kc-url", help="Keycloak base URL (internal http://keycloak:8080 or https://lapiazza.app)"),
    src: str = typer.Option("kc-pos-realm-dev", "--src", help="Source realm to clone from"),
    dst: str = typer.Option(..., "--dst", help="New realm to create, e.g. kc-pos-realm-stg"),
    host: str = typer.Option(..., "--host", help="The target env's public host for redirect URIs, e.g. staging-banco.lapiazza.app"),
    frontend_url: str = typer.Option("https://lapiazza.app", "--frontend-url", help="Realm frontendUrl (the host in login/email links)"),
    client_id: str = typer.Option("helix_pos_web", "--client-id", help="The POS public client to copy"),
    admin_user: str = typer.Option("admin", "--admin-user", help="KC master-realm admin username"),
    seed_admin: str = typer.Option(None, "--seed-admin", help="Optionally seed ONE bootstrap admin username (gets pos-admin)"),
    seed_email: str = typer.Option(None, "--seed-email", help="Email for the seeded admin"),
    seed_password: str = typer.Option(None, "--seed-password", help="Password for the seeded admin"),
    verify_tls: bool = typer.Option(False, "--verify-tls/--no-verify-tls", help="Verify TLS (off for internal/self-signed)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print what would happen, change nothing"),
):
    """Clone src → dst (realm + helix_pos_web client + pos roles), optionally seed an admin."""
    admin_pass = os.getenv("KC_ADMIN_PASSWORD") or getpass.getpass(f"KC admin password for '{admin_user}': ")
    base = kc_url.rstrip("/")

    with httpx.Client(timeout=30, verify=verify_tls) as c:
        h = {"Authorization": f"Bearer {_token(c, base, admin_user, admin_pass)}"}

        # ---- 1. read the source realm's login settings ----
        sr = c.get(f"{base}/admin/realms/{src}", headers=h)
        if sr.status_code != 200:
            typer.secho(f"✗ Source realm '{src}' not readable ({sr.status_code})", fg="red")
            raise typer.Exit(1)
        s = sr.json()

        # Curated, create-safe subset (no id/defaultRole/clientPolicies to avoid conflicts).
        realm_rep = {
            "realm": dst,
            "enabled": True,
            "sslRequired": s.get("sslRequired", "external"),
            "registrationAllowed": False,
            "loginWithEmailAllowed": s.get("loginWithEmailAllowed", True),
            "duplicateEmailsAllowed": s.get("duplicateEmailsAllowed", False),
            "resetPasswordAllowed": s.get("resetPasswordAllowed", True),
            "editUsernameAllowed": s.get("editUsernameAllowed", False),
            "verifyEmail": s.get("verifyEmail", False),
            "accessTokenLifespan": s.get("accessTokenLifespan", 300),
            "ssoSessionIdleTimeout": s.get("ssoSessionIdleTimeout", 1800),
            "ssoSessionMaxLifespan": s.get("ssoSessionMaxLifespan", 36000),
            "attributes": {"frontendUrl": frontend_url},
        }

        # ---- 2. read the client + roles to copy ----
        cls = c.get(f"{base}/admin/realms/{src}/clients", headers=h, params={"clientId": client_id}).json()
        if not cls:
            typer.secho(f"✗ Client '{client_id}' not found in {src}", fg="red")
            raise typer.Exit(1)
        cl = cls[0]
        redirect_uris = [f"https://{host}/*", f"https://{host}/pos/callback"]
        web_origins = [f"https://{host}"]
        client_rep = {
            "clientId": cl["clientId"],
            "name": cl.get("name"),
            "enabled": True,
            "publicClient": cl.get("publicClient", True),
            "standardFlowEnabled": cl.get("standardFlowEnabled", True),
            "directAccessGrantsEnabled": cl.get("directAccessGrantsEnabled", True),
            "redirectUris": redirect_uris,
            "webOrigins": web_origins,
            "attributes": {"post.logout.redirect.uris": f"https://{host}/*"},
        }

        roles = c.get(f"{base}/admin/realms/{src}/roles", headers=h).json()
        copy_roles = [r for r in roles if not any(k in (r.get("name") or "") for k in _SKIP_ROLE_SUBSTR)]

        typer.secho(f"\nPlan: clone {src} → {dst}", fg="cyan")
        typer.echo(f"  realm frontendUrl = {frontend_url}")
        typer.echo(f"  client {client_id} redirects → {redirect_uris}")
        typer.echo(f"  roles → {[r.get('name') for r in copy_roles]}")
        if seed_admin:
            typer.echo(f"  seed admin → {seed_admin} <{seed_email}> (pos-admin)")
        if dry_run:
            typer.secho("DRY RUN — nothing changed.", fg="yellow")
            raise typer.Exit(0)

        # ---- 3. create realm (skip if exists) ----
        exists = c.get(f"{base}/admin/realms/{dst}", headers=h).status_code == 200
        if exists:
            typer.secho(f"SKIP realm {dst} (already exists)", fg="yellow")
        else:
            rr = c.post(f"{base}/admin/realms", headers=h, json=realm_rep)
            if rr.status_code not in (201, 204):
                typer.secho(f"✗ Create realm failed ({rr.status_code}): {rr.text[:300]}", fg="red")
                raise typer.Exit(1)
            typer.secho(f"✓ Realm {dst} created", fg="green")

        # ---- 4. create the client (skip if exists) ----
        ec = c.get(f"{base}/admin/realms/{dst}/clients", headers=h, params={"clientId": client_id}).json()
        if ec:
            typer.secho(f"SKIP client {client_id} (already exists) — refreshing redirects", fg="yellow")
            c.put(f"{base}/admin/realms/{dst}/clients/{ec[0]['id']}", headers=h,
                  json={**ec[0], "redirectUris": redirect_uris, "webOrigins": web_origins})
        else:
            cr = c.post(f"{base}/admin/realms/{dst}/clients", headers=h, json=client_rep)
            if cr.status_code not in (201, 204):
                typer.secho(f"✗ Create client failed ({cr.status_code}): {cr.text[:300]}", fg="red")
                raise typer.Exit(1)
            typer.secho(f"✓ Client {client_id} created", fg="green")

        # ---- 5. create the roles (skip existing) ----
        have = {r.get("name") for r in c.get(f"{base}/admin/realms/{dst}/roles", headers=h).json()}
        for r in copy_roles:
            if r["name"] in have:
                continue
            rc = c.post(f"{base}/admin/realms/{dst}/roles", headers=h,
                        json={"name": r["name"], "description": r.get("description")})
            tag = "✓" if rc.status_code in (201, 204) else "✗"
            typer.echo(f"  {tag} role {r['name']} ({rc.status_code})")

        # ---- 6. optional bootstrap admin ----
        if seed_admin:
            if not (seed_email and seed_password):
                typer.secho("✗ --seed-admin needs --seed-email and --seed-password", fg="red")
                raise typer.Exit(1)
            ux = c.get(f"{base}/admin/realms/{dst}/users", headers=h,
                       params={"username": seed_admin, "exact": "true"}).json()
            if ux:
                uid = ux[0]["id"]
                typer.secho(f"SKIP user {seed_admin} (exists) — resetting password", fg="yellow")
            else:
                c.post(f"{base}/admin/realms/{dst}/users", headers=h, json={
                    "username": seed_admin, "email": seed_email, "enabled": True,
                    "emailVerified": True, "firstName": seed_admin.capitalize(), "lastName": "Admin",
                }).raise_for_status()
                uid = c.get(f"{base}/admin/realms/{dst}/users", headers=h,
                            params={"username": seed_admin, "exact": "true"}).json()[0]["id"]
                typer.secho(f"✓ User {seed_admin} created", fg="green")
            c.put(f"{base}/admin/realms/{dst}/users/{uid}/reset-password", headers=h,
                  json={"type": "password", "value": seed_password, "temporary": False})
            admin_role = next((r for r in c.get(f"{base}/admin/realms/{dst}/roles", headers=h).json()
                               if "pos-admin" in (r.get("name") or "")), None)
            if admin_role:
                c.post(f"{base}/admin/realms/{dst}/users/{uid}/role-mappings/realm", headers=h, json=[admin_role])
                typer.secho(f"✓ {seed_admin} ← {admin_role['name']}", fg="green")
            else:
                typer.secho("✗ no pos-admin role to assign", fg="red")

        typer.secho(f"\n✓ Done. Next: set SMTP on {dst} (configure_kc_smtp.py) + point the "
                    f"container at POS_REALM={dst}.", fg="green")


if __name__ == "__main__":
    app()
