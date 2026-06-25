#!/usr/bin/env python3
"""Configure SMTP on a Keycloak realm so Banco can email login-setup links.

This is the gate for the "self-set password" path (HR ▸ Staff ▸ 📧 Email setup link).
Until a realm has SMTP, Keycloak can't send the UPDATE_PASSWORD / VERIFY_EMAIL email, so
Banco falls back to Felix typing a counter-password. Run this ONCE per realm to open the
email path. It's a deliberate auth-config change — run it on purpose, with your own creds.

Why a script and not an app button: SMTP config is realm-wide (the POS realm is shared
across dev/staging/prod), so it must NOT live behind an always-on endpoint. One operator,
one deliberate run. (CLAUDE.md rule 11: Python + Typer + getpass, not bash.)

Examples
--------
  # Gmail app-password (recommended for a quick start):
  python scripts/configure_kc_smtp.py \
      --kc-url https://auth.lapiazza.app --realm kc-pos-realm-dev \
      --host smtp.gmail.com --port 587 --starttls \
      --from no-reply@lapiazza.app --from-name "Banco" \
      --smtp-user angel.kenel@gmail.com --auth

  # Show what's currently set, change nothing:
  python scripts/configure_kc_smtp.py --kc-url ... --realm ... --show

  # Send a test email after configuring (uses KC's own test-connection):
  python scripts/configure_kc_smtp.py --kc-url ... --realm ... --show --test you@inbox.com
"""
from __future__ import annotations

import getpass
import sys

import httpx
import typer

app = typer.Typer(add_completion=False, help=__doc__)


def _admin_token(client: httpx.Client, kc_url: str, admin_user: str, admin_pass: str) -> str:
    r = client.post(
        f"{kc_url.rstrip('/')}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli",
              "username": admin_user, "password": admin_pass},
    )
    if r.status_code != 200:
        typer.secho(f"✗ Admin login failed ({r.status_code}): {r.text[:200]}", fg="red")
        raise typer.Exit(1)
    return r.json()["access_token"]


@app.command()
def main(
    kc_url: str = typer.Option(..., "--kc-url", help="Keycloak base URL, e.g. https://auth.lapiazza.app"),
    realm: str = typer.Option(..., "--realm", help="Realm to configure, e.g. kc-pos-realm-dev"),
    admin_user: str = typer.Option("admin", "--admin-user", help="KC master-realm admin username"),
    show: bool = typer.Option(False, "--show", help="Print the realm's current SMTP config and exit (unless other flags set it)"),
    host: str = typer.Option(None, "--host", help="SMTP server host"),
    port: int = typer.Option(587, "--port", help="SMTP port (587 STARTTLS / 465 SSL / 25 plain)"),
    from_addr: str = typer.Option(None, "--from", help="From address shown on the email"),
    from_name: str = typer.Option("Banco", "--from-name", help="From display name"),
    reply_to: str = typer.Option(None, "--reply-to", help="Optional Reply-To address"),
    starttls: bool = typer.Option(False, "--starttls", help="Use STARTTLS (port 587)"),
    ssl: bool = typer.Option(False, "--ssl", help="Use SSL (port 465)"),
    auth: bool = typer.Option(False, "--auth", help="SMTP requires username/password (prompts for password)"),
    smtp_user: str = typer.Option(None, "--smtp-user", help="SMTP username (with --auth)"),
    test: str = typer.Option(None, "--test", help="After saving, send a Keycloak test email to this address"),
):
    """Read or set a realm's SMTP server settings via the Keycloak admin API."""
    admin_pass = getpass.getpass(f"Keycloak admin password for '{admin_user}': ")

    with httpx.Client(timeout=30) as client:
        token = _admin_token(client, kc_url, admin_user, admin_pass)
        h = {"Authorization": f"Bearer {token}"}
        base = f"{kc_url.rstrip('/')}/admin/realms/{realm}"

        r = client.get(base, headers=h)
        if r.status_code != 200:
            typer.secho(f"✗ Could not read realm '{realm}' ({r.status_code})", fg="red")
            raise typer.Exit(1)
        realm_cfg = r.json()
        current = realm_cfg.get("smtpServer") or {}

        # Pure read?
        setting_anything = any([host, from_addr])
        if show and not setting_anything:
            typer.secho(f"Current SMTP on '{realm}':", fg="cyan")
            if not current:
                typer.echo("  (none configured)")
            for k, v in current.items():
                typer.echo(f"  {k} = {'********' if k == 'password' else v}")
            if not test:
                raise typer.Exit(0)

        if setting_anything:
            if not host or not from_addr:
                typer.secho("✗ Need both --host and --from to set SMTP.", fg="red")
                raise typer.Exit(1)
            smtp = {
                "host": host,
                "port": str(port),
                "from": from_addr,
                "fromDisplayName": from_name,
                "ssl": "true" if ssl else "false",
                "starttls": "true" if starttls else "false",
                "auth": "true" if auth else "false",
            }
            if reply_to:
                smtp["replyTo"] = reply_to
            if auth:
                smtp["user"] = smtp_user or typer.prompt("SMTP username")
                smtp["password"] = getpass.getpass("SMTP password (app password): ")

            realm_cfg["smtpServer"] = smtp
            pr = client.put(base, headers=h, json=realm_cfg)
            if pr.status_code not in (200, 204):
                typer.secho(f"✗ Save failed ({pr.status_code}): {pr.text[:200]}", fg="red")
                raise typer.Exit(1)
            typer.secho(f"✓ SMTP saved on realm '{realm}' (host={host}:{port}, from={from_addr})", fg="green")

        # Optional live test through Keycloak's own test-connection endpoint.
        if test:
            smtp_for_test = realm_cfg.get("smtpServer") or current
            if not smtp_for_test:
                typer.secho("✗ No SMTP configured to test.", fg="red")
                raise typer.Exit(1)
            payload = dict(smtp_for_test)
            tr = client.post(f"{base}/testSMTPConnection", headers=h, data={"config": _json(payload), "to": test})
            # Older KC versions use /testSMTPConnection with form 'config'; newer accept JSON.
            if tr.status_code in (200, 204):
                typer.secho(f"✓ Test email sent to {test} — check the inbox.", fg="green")
            else:
                typer.secho(f"✗ Test send failed ({tr.status_code}): {tr.text[:200]}", fg="yellow")
                typer.echo("  (Config is saved; the test path varies by KC version — try the Staff ▸ 📧 button.)")


def _json(d: dict) -> str:
    import json
    return json.dumps(d)


if __name__ == "__main__":
    app()
