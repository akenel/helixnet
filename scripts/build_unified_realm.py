#!/usr/bin/env python3
"""Build (or top-up) a unified HelixNet environment realm — idempotent, dry-run by default.

Lays the IDENTITY-UNIFIED-REALM-BLUEPRINT.md into ONE realm so every app is a CLIENT and
workforce-vs-public is a ROLE TIER (not a realm). Run it per environment:

    sandbox :  python scripts/build_unified_realm.py kc-sandbox --create --apply \
                   --base-domain sandbox-banco.lapiazza.app
    staging :  python scripts/build_unified_realm.py borrowhood-staging --apply ...   (no --create)
    prod    :  python scripts/build_unified_realm.py borrowhood --apply ...           (no --create, GATED)

DRY-RUN IS THE DEFAULT — nothing writes to Keycloak without --apply. Idempotent: existing
clients/roles/groups are left as-is (reported with '='). Plain ASCII role names only (Angel
2026-06-26: emoji dropped from identity config). Admin creds via flags or $KC_ADMIN_PASSWORD.

CLAUDE.md rule 11: Python-first, httpx + Typer.
"""
from __future__ import annotations

import os
import httpx
import typer

app = typer.Typer(add_completion=False, help=__doc__)

# --- the blueprint, as data -------------------------------------------------- #

# Cross-app TIER roles (the workforce-vs-public layer). `member` becomes the realm default role.
TIER_ROLES = ["member", "business", "staff", "admin"]

# Per-app CLIENT-level roles, PLAIN names (no emoji). Namespaced so substring-matching is safe.
APP_ROLES = [
    # POS / Banco
    "pos-cashier", "pos-manager", "pos-admin", "pos-auditor", "pos-developer",
    # Garage / Camper & Tour
    "camper-counter", "camper-mechanic", "camper-manager", "camper-admin",
    "camper-auditor", "camper-accountant", "camper-hr", "camper-qa-tester",
    # Print shop / ISOTTO
    "isotto-counter", "isotto-operator", "isotto-designer", "isotto-manager", "isotto-admin",
    # La Piazza / Bottega
    "lapiazza-user", "lapiazza-admin", "lapiazza-business",
    # Marketplace
    "bh-member", "bh-lender", "bh-operator", "bh-moderator", "bh-admin", "bh-qa-tester",
    # Core platform (namespaced from the old bare developer/guest/admin/auditor)
    "platform-developer", "platform-guest", "platform-admin", "platform-auditor",
]

# Apps as clients. `pub` = public browser client (standard flow); `svc` = bearer/service.
# redirect URIs are built from --base-domain for public clients.
CLIENTS = [
    {"id": "lapiazza_web", "pub": True},
    {"id": "borrowhood-web", "pub": True},
    {"id": "borrowhood-api", "svc": True},
    {"id": "lapiazza_publisher", "confidential": True},   # Artemis Premium token-exchange
    {"id": "helix_pos_web", "pub": True},
    {"id": "helix_pos_mobile", "pub": True},
    {"id": "helix_pos_service", "svc": True},
    {"id": "camper_service_web", "pub": True},
    {"id": "camper_service_api", "svc": True},
    {"id": "isotto_print_web", "pub": True},
    {"id": "isotto_print_mobile", "pub": True},
    {"id": "isotto_print_api", "svc": True},
    {"id": "helix_account", "pub": True},
    {"id": "helix_service_account", "svc": True},
    {"id": "helix_user", "pub": True},
]

# Tenant groups (shops). Members hold business + the relevant workforce roles.
GROUPS = ["shop:artemis"]


# --- helpers (same idiom as kc_admin.py) ------------------------------------- #
def _token(c, kc, user, pw):
    r = c.post(f"{kc}/realms/master/protocol/openid-connect/token",
               data={"grant_type": "password", "client_id": "admin-cli",
                     "username": user, "password": pw})
    r.raise_for_status()
    return r.json()["access_token"]


def _plan(msg):  typer.secho(f"  WOULD {msg}", fg="yellow")
def _did(msg):   typer.secho(f"  + {msg}", fg="green")
def _same(msg):  typer.secho(f"  = {msg}", fg="bright_black")


@app.command()
def build(
    realm: str = typer.Argument(..., help="Target env realm id (kc-sandbox / borrowhood-staging / borrowhood)"),
    create: bool = typer.Option(False, "--create", help="Create the realm if missing (sandbox only)"),
    apply: bool = typer.Option(False, "--apply", help="Write changes (default: dry-run preview)"),
    base_domain: str = typer.Option("sandbox-banco.lapiazza.app", help="Host for public-client redirect URIs"),
    kc_url: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    admin_user: str = typer.Option("helix_user"),
    admin_pass: str = typer.Option(None, help="defaults to $KC_ADMIN_PASSWORD or 'helix_pass'"),
):
    """Idempotently lay the unified blueprint (clients + tier roles + app roles + groups) into `realm`."""
    kc = kc_url.rstrip("/")
    pw = admin_pass or os.environ.get("KC_ADMIN_PASSWORD", "helix_pass")
    mode = "APPLY" if apply else "DRY-RUN"
    typer.secho(f"\n=== build unified realm '{realm}' on {kc}  [{mode}] ===", fg="cyan", bold=True)

    with httpx.Client(verify=False, timeout=60.0) as c:
        c.headers["Authorization"] = f"Bearer {_token(c, kc, admin_user, pw)}"
        base = f"{kc}/admin/realms"

        # 1. realm
        exists = c.get(f"{base}/{realm}").status_code == 200
        if not exists:
            if not create:
                typer.secho(f"❌ realm '{realm}' does not exist (pass --create for a new sandbox realm)", fg="red")
                raise typer.Exit(1)
            if apply:
                c.post(base, json={"realm": realm, "enabled": True, "displayName": realm}).raise_for_status()
                _did(f"created realm {realm}")
            else:
                _plan(f"create realm {realm}")
        else:
            _same(f"realm {realm} exists")

        # if dry-run on a not-yet-created realm, we can't query sub-resources — stop cleanly
        if not exists and not apply:
            typer.secho("\n(DRY-RUN on a realm that doesn't exist yet — re-run with --apply --create to build it,"
                        "\n or point at an existing realm to preview the top-up.)", fg="yellow")
            return

        typer.secho("\n-- clients --", fg="cyan")
        have_clients = {x["clientId"] for x in c.get(f"{base}/{realm}/clients", params={"max": 500}).json()}
        for spec in CLIENTS:
            cid = spec["id"]
            if cid in have_clients:
                _same(f"client {cid}")
                continue
            body = {"clientId": cid, "enabled": True, "protocol": "openid-connect"}
            if spec.get("pub"):
                body.update(publicClient=True, standardFlowEnabled=True, directAccessGrantsEnabled=True,
                            redirectUris=[f"https://{base_domain}/*"], webOrigins=["+"])
            elif spec.get("confidential"):
                body.update(publicClient=False, standardFlowEnabled=False, serviceAccountsEnabled=True)
            elif spec.get("svc"):
                body.update(publicClient=False, standardFlowEnabled=False, serviceAccountsEnabled=True,
                            bearerOnly=False)
            if apply:
                c.post(f"{base}/{realm}/clients", json=body).raise_for_status()
                _did(f"client {cid}")
            else:
                _plan(f"create client {cid}")

        typer.secho("\n-- roles (tiers + app) --", fg="cyan")
        have_roles = {x["name"] for x in c.get(f"{base}/{realm}/roles", params={"max": 500}).json()}
        for role in TIER_ROLES + APP_ROLES:
            if role in have_roles:
                _same(f"role {role}")
                continue
            tier = " (tier)" if role in TIER_ROLES else ""
            if apply:
                c.post(f"{base}/{realm}/roles", json={"name": role}).raise_for_status()
                _did(f"role {role}{tier}")
            else:
                _plan(f"create role {role}{tier}")

        typer.secho("\n-- default role: member --", fg="cyan")
        # add `member` to the realm's default-roles-<realm> composite so self-registrants get it
        dr = f"default-roles-{realm}"
        drr = c.get(f"{base}/{realm}/roles/{dr}")
        if drr.status_code == 200:
            comp = c.get(f"{base}/{realm}/roles/{dr}/composites").json()
            if any(x["name"] == "member" for x in comp):
                _same("member already in default-roles")
            elif apply and "member" in (have_roles | set(TIER_ROLES)):
                member = c.get(f"{base}/{realm}/roles/member").json()
                c.post(f"{base}/{realm}/roles/{dr}/composites", json=[member]).raise_for_status()
                _did("added member to default-roles (self-registrants get member)")
            else:
                _plan("add member to default-roles composite")
        else:
            _plan(f"(default-roles role {dr} not found yet — will exist after realm create)")

        typer.secho("\n-- groups (shops) --", fg="cyan")
        have_groups = {g["name"] for g in c.get(f"{base}/{realm}/groups", params={"max": 500}).json()}
        for g in GROUPS:
            if g in have_groups:
                _same(f"group {g}")
            elif apply:
                c.post(f"{base}/{realm}/groups", json={"name": g}).raise_for_status()
                _did(f"group {g}")
            else:
                _plan(f"create group {g}")

    typer.secho(f"\n{'✅ applied' if apply else 'DRY-RUN complete — re-run with --apply to write'}.",
                fg="green" if apply else "yellow", bold=True)


if __name__ == "__main__":
    app()
