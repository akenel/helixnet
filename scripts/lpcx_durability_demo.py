#!/usr/bin/env python3
"""LPCX durability demo -- prove the v2 claim: kill the consumer mid-flight and
NOTHING is lost. Durable queue + persistent messages + manual ack => unacked jobs
requeue on crash and complete on restart. At-least-once, but one spend per job.

Run:  python scripts/lpcx_durability_demo.py            # 60 jobs
      python scripts/lpcx_durability_demo.py --n 80 --user angel

Doubles as a durability regression test (exit 1 if any job is lost or double-charged).
"""
import asyncio
import subprocess
import time

import httpx
import typer

app = typer.Typer(add_completion=False)

BASE = "https://helix.local"
KC = "https://keycloak.helix.local"
REALM = "kc-camper-service-realm-dev"
CLIENT = "camper_service_web"
CONSUMER = "lpcx-consumer"
DB = ["docker", "exec", "postgres", "psql", "-U", "helix_user", "-d", "helix_db", "-tAc"]


def sh(*args) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout.strip()


JOB_IDS: list[str] = []   # set after submit -- all counts scope to THIS batch


def db_status_counts() -> dict:
    where = ""
    if JOB_IDS:
        ids = ",".join(f"'{j}'" for j in JOB_IDS)
        where = f" where id in ({ids})"
    out = sh(*DB, f"select status, count(*) from compute_jobs{where} group by status")
    d = {}
    for line in out.splitlines():
        if "|" in line:
            s, c = line.split("|"); d[s] = int(c)
    return d


def rabbit() -> dict:
    out = sh("docker", "exec", "rabbitmq", "rabbitmqctl", "list_queues",
             "name", "messages_ready", "messages_unacknowledged", "consumers")
    for line in out.splitlines():
        p = line.split("\t")
        if p and p[0] == "lpcx.jobs":
            return {"ready": int(p[1]), "unacked": int(p[2]), "consumers": int(p[3])}
    return {"ready": 0, "unacked": 0, "consumers": 0}


def show(label: str):
    c = db_status_counts(); r = rabbit()
    done, run, q = c.get("done", 0), c.get("running", 0), c.get("queued", 0)
    typer.secho(f"  {label}", fg="cyan")
    print(f"     DB:     done={done}  running={run}  queued={q}  "
          f"(killed={c.get('killed',0)} failed={c.get('failed',0)})")
    print(f"     RabbitMQ lpcx.jobs:  ready={r['ready']}  unacked={r['unacked']}  consumers={r['consumers']}")
    return c, r


async def get_token(user: str, password: str) -> str:
    async with httpx.AsyncClient(verify=False, timeout=15) as c:
        r = await c.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
            "grant_type": "password", "client_id": CLIENT,
            "username": user, "password": password, "scope": "openid",
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def submit_jobs(token: str, n: int) -> list[str]:
    async with httpx.AsyncClient(verify=False, timeout=30) as c:
        async def one():
            r = await c.post(f"{BASE}/api/v1/compute/jobs",
                             json={"template": "print-card", "brain_mode": "shared"},
                             headers={"Authorization": f"Bearer {token}"})
            return r.json().get("id")
        return [j for j in await asyncio.gather(*[one() for _ in range(n)]) if j]


def ledger_spend_rows(job_ids: list[str]) -> int:
    """Count SPEND ledger entries for these jobs -- must be exactly one each."""
    ids = ",".join(f"'{j}'" for j in job_ids)
    out = sh(*DB, f"select count(*) from compute_ledger where kind='spend' and job_id in ({ids})")
    return int(out or 0)


@app.command()
def main(n: int = 60, user: str = "angel", password: str = "helix_pass", down_secs: int = 4):
    typer.secho("\n=== LPCX DURABILITY DEMO -- kill the consumer mid-flight ===\n", fg="magenta", bold=True)
    token = asyncio.run(get_token(user, password))

    typer.secho(f"[1] Submitting {n} jobs as @{user}...", fg="white", bold=True)
    job_ids = asyncio.run(submit_jobs(token, n))
    JOB_IDS.clear(); JOB_IDS.extend(job_ids)   # scope all counts to this batch
    print(f"    {len(job_ids)} accepted.")

    # wait until a healthy batch is in-flight (running/unacked)
    for _ in range(20):
        time.sleep(0.4)
        if db_status_counts().get("running", 0) >= min(n, 20):
            break
    print()
    before, rb = show("[2] MID-FLIGHT (jobs running, messages unacked):")
    in_flight = before.get("running", 0) + before.get("queued", 0)

    typer.secho(f"\n[3] *** docker stop -t 0 {CONSUMER}  (hard kill, mid-flight) ***", fg="red", bold=True)
    sh("docker", "stop", "-t", "0", CONSUMER)
    time.sleep(2.0)
    after_kill, rk = show("[4] CONSUMER DEAD (unacked returned to ready, consumers=0):")
    requeued = rk["ready"]

    typer.secho(f"\n[5] Consumer down for {down_secs}s... (orphaned 'running' rows are the transient)", fg="yellow")
    time.sleep(down_secs)

    typer.secho(f"\n[6] *** docker start {CONSUMER}  (recover) ***", fg="green", bold=True)
    sh("docker", "start", CONSUMER)

    # poll until everything is terminal
    typer.secho("\n[7] Recovering -- redelivered jobs completing:", fg="cyan")
    deadline = time.time() + 60
    while time.time() < deadline:
        time.sleep(1.5)
        c = db_status_counts()
        terminal = c.get("done", 0) + c.get("killed", 0) + c.get("failed", 0)
        print(f"     done={c.get('done',0)} running={c.get('running',0)} queued={c.get('queued',0)} "
              f"| terminal={terminal}/{len(job_ids)}")
        if terminal >= len(job_ids) and c.get("running", 0) == 0 and c.get("queued", 0) == 0:
            break

    print()
    final = db_status_counts()
    done = final.get("done", 0)
    spends = ledger_spend_rows(job_ids)

    typer.secho("=== VERDICT ===", fg="magenta", bold=True)
    lost = len(job_ids) - (final.get("done", 0) + final.get("killed", 0) + final.get("failed", 0))
    ok_lost = lost == 0
    ok_charge = spends == len([j for j in job_ids])  # one spend per job
    typer.secho(f"  submitted        : {len(job_ids)}", fg="white")
    typer.secho(f"  completed (done) : {done}", fg="green" if done == len(job_ids) else "yellow")
    typer.secho(f"  requeued on kill : {requeued}", fg="cyan")
    typer.secho(f"  JOBS LOST        : {lost}", fg="green" if ok_lost else "red")
    typer.secho(f"  spend entries    : {spends}  (expect {len(job_ids)} -- one per job, no double-charge)",
                fg="green" if ok_charge else "red")
    if ok_lost and ok_charge:
        typer.secho("\n  DURABLE: nothing lost, nothing double-charged. The queue held. \U0001F43A", fg="green", bold=True)
    else:
        typer.secho("\n  FAILED durability check.", fg="red", bold=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
