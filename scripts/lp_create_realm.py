#!/usr/bin/env python3
"""Build La Piazza its own Keycloak front door -- idempotent, reproducible.

La Piazza (the Bottega + Compute Exchange) had been borrowing the camper-service
realm's door (login said "Camper & Tour"). This gives it its OWN realm, client,
roles and a user -- additively, via the KC admin API. The camper realm is never
touched. Safe to re-run (every step is check-then-create).

Run on dev:   python scripts/lp_create_realm.py
Run on box:   python scripts/lp_create_realm.py --kc-url https://bottega.lapiazza.app

CLAUDE.md rule 11: Python-first, httpx + Typer.
"""
import sys

import httpx
import typer

app = typer.Typer(add_completion=False)

ROLES = ["lapiazza-user", "lapiazza-admin"]
DEFAULT_REDIRECTS = [
    "https://helix.local/*",
    "https://bottega.lapiazza.app/*",
    "http://localhost:8000/*",
    "https://46.62.138.218/*",
]


def _admin_token(c: httpx.Client, kc: str, user: str, pw: str) -> str:
    r = c.post(f"{kc}/realms/master/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": "admin-cli",
                     "username": user, "password": pw})
    r.raise_for_status()
    return r.json()["access_token"]


@app.command()
def main(
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option("helix_pass"),
    lp_user: str = typer.Option("angel", help="La Piazza member to create"),
    lp_pass: str = typer.Option("helix_pass"),
    realm: str = typer.Option("lapiazza-realm-dev", help="Realm id to build"),
    client: str = typer.Option("lapiazza_web", help="Public client id"),
    display_name: str = typer.Option("La Piazza", help="Realm display name"),
    frontend_url: str = typer.Option("", help="Pin realm attributes.frontendUrl (required for a non-default hostname, e.g. staging)"),
    redirect: list[str] = typer.Option(None, help="Override redirect URIs (repeatable); defaults to the prod set"),
):
    REALM, CLIENT = realm, client
    REDIRECTS = redirect if redirect else DEFAULT_REDIRECTS
    kc = kc_url.rstrip("/")
    with httpx.Client(verify=False, timeout=30.0) as c:
        tok = _admin_token(c, kc, admin_user, admin_pass)
        h = {"Authorization": f"Bearer {tok}"}
        base = f"{kc}/admin/realms"

        # 1) realm --------------------------------------------------------------
        realm_body = {
            "realm": REALM, "enabled": True, "registrationAllowed": True,
            "displayName": display_name,
            "displayNameHtml": f"<b>{display_name}</b>",
            "loginTheme": "keycloak",
        }
        if frontend_url:
            # frontendUrl must be pinned per-realm when the realm is reached via a
            # non-default hostname (KC_HOSTNAME_URL is the prod host) -- else OIDC
            # discovery returns the wrong host and login cookies land on the wrong domain.
            realm_body["attributes"] = {"frontendUrl": frontend_url.rstrip("/")}
        if c.get(f"{base}/{REALM}", headers=h).status_code == 404:
            c.post(base, headers=h, json=realm_body).raise_for_status()
            typer.secho(f"  + realm {REALM} created (displayName '{display_name}'"
                        + (f", frontendUrl {frontend_url})" if frontend_url else ")"), fg="green")
        elif frontend_url:
            # idempotent: ensure frontendUrl is set on an existing realm too
            c.put(f"{base}/{REALM}", headers=h, json=realm_body).raise_for_status()
            typer.secho(f"  = realm {REALM} updated (frontendUrl {frontend_url})", fg="bright_black")
        else:
            typer.secho(f"  = realm {REALM} already exists", fg="bright_black")

        # 2) client -------------------------------------------------------------
        existing = c.get(f"{base}/{REALM}/clients", headers=h, params={"clientId": CLIENT}).json()
        if not existing:
            c.post(f"{base}/{REALM}/clients", headers=h, json={
                "clientId": CLIENT, "enabled": True, "publicClient": True,
                "standardFlowEnabled": True, "directAccessGrantsEnabled": True,
                "redirectUris": REDIRECTS, "webOrigins": ["+"],
            }).raise_for_status()
            typer.secho(f"  + client {CLIENT} created", fg="green")
        else:
            cid = existing[0]["id"]
            c.put(f"{base}/{REALM}/clients/{cid}", headers=h, json={
                **existing[0], "redirectUris": REDIRECTS, "webOrigins": ["+"],
                "publicClient": True, "standardFlowEnabled": True,
                "directAccessGrantsEnabled": True,
            }).raise_for_status()
            typer.secho(f"  = client {CLIENT} updated (redirects)", fg="bright_black")

        # 3) roles --------------------------------------------------------------
        for role in ROLES:
            if c.get(f"{base}/{REALM}/roles/{role}", headers=h).status_code == 404:
                c.post(f"{base}/{REALM}/roles", headers=h, json={"name": role}).raise_for_status()
                typer.secho(f"  + role {role} created", fg="green")
            else:
                typer.secho(f"  = role {role} exists", fg="bright_black")

        # 4) user + password + roles -------------------------------------------
        found = c.get(f"{base}/{REALM}/users", headers=h, params={"username": lp_user, "exact": "true"}).json()
        if not found:
            c.post(f"{base}/{REALM}/users", headers=h, json={
                "username": lp_user, "enabled": True, "emailVerified": True,
                "firstName": lp_user.capitalize(), "lastName": "LaPiazza",
                "email": f"{lp_user}@lapiazza.local",
                "credentials": [{"type": "password", "value": lp_pass, "temporary": False}],
            }).raise_for_status()
            found = c.get(f"{base}/{REALM}/users", headers=h, params={"username": lp_user, "exact": "true"}).json()
            typer.secho(f"  + user {lp_user} created", fg="green")
        else:
            typer.secho(f"  = user {lp_user} exists", fg="bright_black")
        uid = found[0]["id"]
        # complete the profile + clear required actions (else "Account is not fully set up":
        # KC's user-profile validation triggers VERIFY_PROFILE when email/lastName are missing)
        c.put(f"{base}/{REALM}/users/{uid}", headers=h, json={
            "enabled": True, "emailVerified": True, "requiredActions": [],
            "lastName": "LaPiazza", "email": f"{lp_user}@lapiazza.local"}).raise_for_status()
        # ensure password (reset is idempotent)
        c.put(f"{base}/{REALM}/users/{uid}/reset-password", headers=h,
              json={"type": "password", "value": lp_pass, "temporary": False}).raise_for_status()
        # assign both roles
        role_objs = [c.get(f"{base}/{REALM}/roles/{r}", headers=h).json() for r in ROLES]
        c.post(f"{base}/{REALM}/users/{uid}/role-mappings/realm", headers=h,
               json=role_objs).raise_for_status()
        typer.secho(f"  = {lp_user} has {ROLES}", fg="bright_black")

        typer.secho(f"\n✅ La Piazza front door ready on {kc} -- realm '{REALM}', "
                    f"login as '{lp_user}'", fg="cyan", bold=True)


if __name__ == "__main__":
    app()
