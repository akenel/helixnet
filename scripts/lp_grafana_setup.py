#!/usr/bin/env python3
"""Wire Grafana to the La Piazza data -- the BUSINESS view (jobs flowing, the economy).

Idempotent: creates a Postgres datasource over the LPCX tables and an "LPCX -- La
Piazza Compute Exchange" dashboard. Zero app instrumentation -- it just queries
compute_jobs / compute_ledger that already exist. (Prometheus = the RESOURCE view,
a separate layer for the overload guardrail.)

Run on dev:  python scripts/lp_grafana_setup.py
Run on box:  python scripts/lp_grafana_setup.py --grafana http://localhost:3000 ...

CLAUDE.md rule 11: Python-first, httpx + Typer.
"""
import httpx
import typer

app = typer.Typer(add_completion=False)


def panel(title, sql, ptype, x, y, w, h, ds_uid, unit=None):
    p = {
        "title": title, "type": ptype,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": {"type": "postgres", "uid": ds_uid},
        "targets": [{"format": "table", "rawSql": sql, "rawQuery": True, "refId": "A",
                     "datasource": {"type": "postgres", "uid": ds_uid}}],
        "fieldConfig": {"defaults": {}, "overrides": []},
    }
    if unit:
        p["fieldConfig"]["defaults"]["unit"] = unit
    if ptype == "timeseries":
        p["targets"][0]["format"] = "time_series"
    return p


@app.command()
def main(
    grafana: str = typer.Option("http://admin:admin@127.0.0.1:3000",
                                help="Grafana base URL incl. admin creds"),
    pg_host: str = typer.Option("postgres:5432"),
    pg_db: str = typer.Option("helix_db"),
    pg_user: str = typer.Option("helix_user"),
    pg_pass: str = typer.Option("helix_pass"),
):
    base = grafana.rstrip("/")
    with httpx.Client(timeout=20.0, verify=False) as c:
        # 1) datasource (idempotent) ------------------------------------------
        r = c.get(f"{base}/api/datasources/name/lp-postgres")
        if r.status_code == 200:
            ds_uid = r.json()["uid"]
            typer.secho(f"  = datasource lp-postgres exists ({ds_uid})", fg="bright_black")
        else:
            r = c.post(f"{base}/api/datasources", json={
                "name": "lp-postgres", "type": "postgres", "access": "proxy",
                "url": pg_host, "database": pg_db, "user": pg_user,
                "secureJsonData": {"password": pg_pass},
                "jsonData": {"sslmode": "disable", "postgresVersion": 1700},
            })
            r.raise_for_status()
            ds_uid = r.json()["datasource"]["uid"]
            typer.secho(f"  + datasource lp-postgres created ({ds_uid})", fg="green")

        # 2) dashboard --------------------------------------------------------
        panels = [
            panel("Jobs by status", "select status as metric, count(*) as value "
                  "from compute_jobs group by status", "piechart", 0, 0, 8, 8, ds_uid),
            panel("Queue depth (now)", "select count(*) as value from compute_jobs "
                  "where status='queued'", "stat", 8, 0, 4, 4, ds_uid),
            panel("Tokens consumed (total)", "select coalesce(sum(tokens),0) as value "
                  "from compute_jobs", "stat", 8, 4, 4, 4, ds_uid),
            panel("Jobs per node", "select node as metric, count(*) as value "
                  "from compute_jobs group by node order by value desc", "barchart",
                  12, 0, 12, 8, ds_uid),
            panel("Who earned what (credits per node)", "select node as metric, "
                  "sum(credits_burned) as value from compute_jobs where status='done' "
                  "group by node order by value desc", "barchart", 0, 8, 12, 8, ds_uid),
            panel("Jobs over time", "select date_trunc('minute',created_at) as time, "
                  "count(*) as jobs from compute_jobs where $__timeFilter(created_at) "
                  "group by 1 order by 1", "timeseries", 12, 8, 12, 8, ds_uid),
            panel("Credits spent over time", "select date_trunc('hour',created_at) as time, "
                  "sum(case when kind='spend' then -amount else 0 end) as credits_spent "
                  "from compute_ledger where $__timeFilter(created_at) group by 1 order by 1",
                  "timeseries", 0, 16, 24, 7, ds_uid),
        ]
        dash = {
            "dashboard": {
                "uid": "lpcx-business", "title": "LPCX -- La Piazza Compute Exchange",
                "tags": ["la-piazza", "lpcx"], "timezone": "browser",
                "refresh": "10s", "schemaVersion": 39, "panels": panels,
                "time": {"from": "now-2d", "to": "now"},
            },
            "overwrite": True,
        }
        r = c.post(f"{base}/api/dashboards/db", json=dash)
        r.raise_for_status()
        url = r.json().get("url")
        typer.secho(f"\n✅ Dashboard ready: {url}", fg="cyan", bold=True)


if __name__ == "__main__":
    app()
