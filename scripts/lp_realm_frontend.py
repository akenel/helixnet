#!/usr/bin/env python3
"""Pin a realm's frontendUrl so it keeps users on its OWN domain through Keycloak.

One Keycloak serves both lapiazza.app (marketplace) and bottega.lapiazza.app
(the workshop). KC_HOSTNAME_URL pins the server to lapiazza.app, which drags the
bottega login flow back there. Setting the La Piazza realm's frontendUrl to
bottega.lapiazza.app overrides that for this realm only -- surgical, no server change.

  python scripts/lp_realm_frontend.py  (run inside helix-platform: reaches keycloak:8080)
"""
import httpx
import typer

app = typer.Typer(add_completion=False)


@app.command()
def main(kc: str = typer.Option("http://keycloak:8080"),
         realm: str = typer.Option("lapiazza-realm-dev"),
         front: str = typer.Option("https://bottega.lapiazza.app"),
         admin_user: str = typer.Option("helix_user"),
         admin_pass: str = typer.Option("helix_pass")):
    with httpx.Client(verify=False, timeout=25.0) as c:
        tok = c.post(f"{kc}/realms/master/protocol/openid-connect/token",
                     data={"grant_type": "password", "client_id": "admin-cli",
                           "username": admin_user, "password": admin_pass}).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        rep = c.get(f"{kc}/admin/realms/{realm}", headers=h).json()
        rep.setdefault("attributes", {})["frontendUrl"] = front
        c.put(f"{kc}/admin/realms/{realm}", headers=h, json=rep).raise_for_status()
        chk = c.get(f"{kc}/admin/realms/{realm}", headers=h).json().get("attributes", {}).get("frontendUrl")
        typer.secho(f"frontendUrl now: {chk}", fg="green" if chk == front else "red")


if __name__ == "__main__":
    app()
