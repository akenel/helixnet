#!/usr/bin/env python3
"""LPCX load harness -- simulate concurrent users hammering the shared brain to
find where and why it blows. Python-first (CLAUDE.md rule 11): asyncio + httpx + Typer.

Two modes, one tool:
  * DEMO   -- a few named personas (mike,sally,rossa,lp), light burst -> watch the
              gauge climb across browser tabs.
  * STRESS -- crank --users / --burst until the ceiling rejects + latency degrades.

Examples:
  python scripts/lpcx_loadtest.py --users angel,nino,sebastino --burst 30
  python scripts/lpcx_loadtest.py --users mike,sally,rossa,lp --burst 8 --rounds 3
  python scripts/lpcx_loadtest.py --users angel --burst 200          # solo flood

The shared-brain ceiling counts CONCURRENT SLOTS, so even one user firing a big
burst trips it. Lower the cap server-side for a sharper wall: LPCX_BRAIN_CAP=10.
"""
import asyncio
import statistics
import time
from dataclasses import dataclass, field

import httpx
import typer

app = typer.Typer(add_completion=False, help="LPCX concurrent load harness")


@dataclass
class Result:
    user: str
    ok: bool
    http_status: int
    job_status: str | None
    reject_reason: str | None
    latency_ms: float
    error: str | None = None


@dataclass
class Tally:
    results: list[Result] = field(default_factory=list)

    def add(self, r: Result):
        self.results.append(r)


async def get_token(client: httpx.AsyncClient, kc: str, realm: str, client_id: str,
                    user: str, password: str) -> str | None:
    url = f"{kc}/realms/{realm}/protocol/openid-connect/token"
    try:
        r = await client.post(url, data={
            "grant_type": "password",
            "client_id": client_id,
            "username": user,
            "password": password,
            "scope": "openid",
        })
        if r.status_code != 200:
            typer.secho(f"  auth FAIL {user}: {r.status_code} {r.text[:120]}", fg="red")
            return None
        return r.json().get("access_token")
    except Exception as e:  # noqa: BLE001
        typer.secho(f"  auth ERROR {user}: {e}", fg="red")
        return None


async def submit_one(client: httpx.AsyncClient, base: str, user: str, token: str,
                     brain_mode: str, byo_endpoint: str | None) -> Result:
    body = {"template": "pdf-render", "node": "lp-loadtest", "brain_mode": brain_mode}
    if brain_mode == "byo" and byo_endpoint:
        body["byo_endpoint"] = byo_endpoint
    t0 = time.perf_counter()
    try:
        r = await client.post(
            f"{base}/api/v1/compute/jobs",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        dt = (time.perf_counter() - t0) * 1000
        if r.status_code in (200, 201):
            d = r.json()
            return Result(user, True, r.status_code, d.get("status"), d.get("reject_reason"), dt)
        return Result(user, False, r.status_code, None, None, dt, error=r.text[:120])
    except Exception as e:  # noqa: BLE001
        dt = (time.perf_counter() - t0) * 1000
        return Result(user, False, 0, None, None, dt, error=str(e)[:120])


async def read_brain(client: httpx.AsyncClient, base: str, token: str) -> dict:
    try:
        r = await client.get(f"{base}/api/v1/compute/brain",
                             headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            return r.json()
    except Exception:  # noqa: BLE001
        pass
    return {}


async def run(base: str, kc: str, realm: str, client_id: str, users: list[str],
              password: str, burst: int, rounds: int, brain_mode: str,
              byo_endpoint: str | None, max_conc: int | None):
    tally = Tally()
    limits = httpx.Limits(max_connections=max_conc or 1000, max_keepalive_connections=max_conc or 1000)
    async with httpx.AsyncClient(verify=False, timeout=30.0, limits=limits) as client:
        typer.secho(f"\nAuthenticating {len(users)} users...", fg="cyan")
        tokens = await asyncio.gather(*[
            get_token(client, kc, realm, client_id, u, password) for u in users
        ])
        live = [(u, t) for u, t in zip(users, tokens) if t]
        if not live:
            typer.secho("No users authenticated. Check realm/client/roles + Direct Access Grants.", fg="red")
            raise typer.Exit(1)
        typer.secho(f"  {len(live)}/{len(users)} authenticated.", fg="green")

        total = burst * len(live) * rounds
        typer.secho(f"\nFiring {total} concurrent submits "
                    f"({burst}/user x {len(live)} users x {rounds} rounds, brain={brain_mode})...",
                    fg="cyan")

        t_start = time.perf_counter()
        for rnd in range(rounds):
            tasks = [submit_one(client, base, u, t, brain_mode, byo_endpoint)
                     for (u, t) in live for _ in range(burst)]
            for r in await asyncio.gather(*tasks):
                tally.add(r)
            if rounds > 1:
                typer.secho(f"  round {rnd+1}/{rounds} done", fg="bright_black")
        wall = time.perf_counter() - t_start

        # let in-flight jobs run, then read the brain ceiling state
        await asyncio.sleep(1.0)
        brain = await read_brain(client, base, live[0][1])

    report(tally, brain, wall)


def report(tally: Tally, brain: dict, wall: float):
    rs = tally.results
    n = len(rs)
    ok = [r for r in rs if r.ok]
    accepted = [r for r in ok if r.job_status in ("queued", "running", "done")]
    rejected = [r for r in ok if r.job_status == "rejected"]
    http_err = [r for r in rs if not r.ok]
    lats = [r.latency_ms for r in rs]

    def pct(p):
        if not lats:
            return 0.0
        s = sorted(lats)
        return s[min(len(s) - 1, int(len(s) * p))]

    typer.secho("\n" + "=" * 58, fg="cyan")
    typer.secho(" LPCX LOAD REPORT -- where and why it blows", fg="cyan", bold=True)
    typer.secho("=" * 58, fg="cyan")
    print(f"  submits fired      : {n}")
    print(f"  wall clock         : {wall:.2f}s  ({n/wall:.0f} submits/s)")
    typer.secho(f"  accepted (queued)  : {len(accepted)}", fg="green")
    typer.secho(f"  REJECTED (ceiling) : {len(rejected)}  <- shared brain said no",
                fg="yellow" if rejected else "bright_black")
    typer.secho(f"  HTTP errors        : {len(http_err)}", fg="red" if http_err else "bright_black")
    print(f"  latency p50 / p95  : {pct(0.50):.0f}ms / {pct(0.95):.0f}ms")
    print(f"  latency max        : {max(lats):.0f}ms" if lats else "  latency max        : -")

    if http_err:
        codes = {}
        for r in http_err:
            key = r.error.split(":")[0] if r.http_status == 0 else f"HTTP {r.http_status}"
            codes[key] = codes.get(key, 0) + 1
        typer.secho("\n  failure breakdown:", fg="red")
        for k, v in sorted(codes.items(), key=lambda x: -x[1]):
            print(f"    {v:4d}  {k}")

    if brain:
        typer.secho("\n  shared brain @ end:", fg="cyan")
        print(f"    cap                : {brain.get('cap')} slots")
        print(f"    peak slots used    : {brain.get('peak')}")
        print(f"    total rejections   : {brain.get('rejections')}")
        print(f"    jobs served        : {brain.get('jobs_served')}")
        print(f"    tokens consumed    : {brain.get('tokens_total')}")

    typer.secho("\n  verdict:", fg="cyan", bold=True)
    if http_err and any(r.http_status == 0 for r in http_err):
        typer.secho("    BLEW on the transport -- connection/socket/pool exhaustion "
                    "before the app could answer. Lower --burst or raise server limits.", fg="red")
    elif http_err:
        typer.secho("    BLEW in the app -- 5xx under load (likely DB session pool: "
                    "DB_POOL_SIZE + DB_MAX_OVERFLOW). That's the real ceiling to tune.", fg="red")
    elif rejected:
        typer.secho("    HELD -- the brain ceiling did its job: excess load was REJECTED "
                    "cleanly, not crashed. This is the wall working as designed.", fg="green")
    else:
        typer.secho("    HELD -- everything accepted. Crank --burst higher to find the wall.", fg="green")
    print()


@app.command()
def main(
    users: str = typer.Option("angel,nino,sebastino", help="Comma list of usernames (must exist + have camper-qa role)"),
    password: str = typer.Option("helix_pass", help="Shared test password"),
    burst: int = typer.Option(20, help="Concurrent submits per user per round"),
    rounds: int = typer.Option(1, help="Number of bursts"),
    brain_mode: str = typer.Option("shared", help="shared | byo"),
    byo_endpoint: str = typer.Option(None, help="BYO brain endpoint (brain_mode=byo)"),
    base: str = typer.Option("https://helix.local", help="App base URL"),
    kc: str = typer.Option("https://keycloak.helix.local", help="Keycloak base URL"),
    realm: str = typer.Option("kc-camper-service-realm-dev", help="Keycloak realm"),
    client_id: str = typer.Option("camper_service_web", help="Keycloak client id"),
    max_concurrency: int = typer.Option(None, help="Cap client connections (default unlimited -- we WANT to flood)"),
):
    user_list = [u.strip() for u in users.split(",") if u.strip()]
    asyncio.run(run(base, kc, realm, client_id, user_list, password, burst, rounds,
                    brain_mode, byo_endpoint, max_concurrency))


if __name__ == "__main__":
    app()
