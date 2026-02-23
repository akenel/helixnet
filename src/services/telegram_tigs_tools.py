# File: src/services/telegram_tigs_tools.py
"""
Tool functions for Tigs Telegram Bot.
These are callable by Claude via tool_use to query HelixNet status.
All queries go directly to Postgres (same Docker network).
"""
import os
import logging
import asyncpg
import aiohttp

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "ASYNC_DATABASE_URL",
    "postgresql://helix_user:helix_pass@postgres:5432/helix_db"
)
# asyncpg wants postgresql:// not postgresql+asyncpg://
PG_DSN = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

PLATFORM_HEALTH_URL = os.environ.get(
    "PLATFORM_HEALTH_URL",
    "http://helix-platform:8000/health/healthz"
)


async def _get_pg_connection():
    return await asyncpg.connect(PG_DSN)


async def check_bugs() -> str:
    """Get QA bug summary: total, open, critical counts."""
    try:
        conn = await _get_pg_connection()
        try:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status IN ('open', 'in_progress')) AS open_bugs,
                    COUNT(*) FILTER (WHERE severity = 'critical' AND status IN ('open', 'in_progress')) AS critical
                FROM qa_bug_reports
            """)
            return (
                f"Bug Summary: {row['total']} total, "
                f"{row['open_bugs']} open, "
                f"{row['critical']} critical"
            )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"check_bugs failed: {e}")
        return f"Error querying bugs: {e}"


async def get_bug_detail(bug_number: int) -> str:
    """Get details for a specific bug by number (e.g. BUG-010)."""
    try:
        conn = await _get_pg_connection()
        try:
            bug = await conn.fetchrow("""
                SELECT bug_number, title, description, severity, status,
                       assigned_to, git_sha, reported_by,
                       created_at, updated_at
                FROM qa_bug_reports
                WHERE bug_number = $1
            """, bug_number)

            if not bug:
                return f"BUG-{bug_number:03d} not found."

            # Get linked commits
            commits = await conn.fetch("""
                SELECT sha, message, committed_at
                FROM qa_bug_commits
                WHERE bug_id = (SELECT id FROM qa_bug_reports WHERE bug_number = $1)
                ORDER BY committed_at
            """, bug_number)

            lines = [
                f"BUG-{bug['bug_number']:03d}: {bug['title']}",
                f"Status: {bug['status']} | Severity: {bug['severity']}",
                f"Assigned: {bug['assigned_to'] or 'unassigned'}",
                f"Reported by: {bug['reported_by']} on {bug['created_at'].strftime('%Y-%m-%d')}",
            ]

            if bug['description']:
                desc = bug['description'][:200]
                if len(bug['description']) > 200:
                    desc += "..."
                lines.append(f"Description: {desc}")

            if commits:
                lines.append(f"\nCommits ({len(commits)}):")
                for c in commits:
                    lines.append(
                        f"  {c['sha'][:7]} {c['message'][:50]} "
                        f"({c['committed_at'].strftime('%Y-%m-%d')})"
                    )
            else:
                lines.append("No commits linked.")

            return "\n".join(lines)
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"get_bug_detail failed: {e}")
        return f"Error querying bug {bug_number}: {e}"


async def server_status() -> str:
    """Check if the HelixNet platform is healthy."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PLATFORM_HEALTH_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return f"Platform: HEALTHY -- {data.get('status', 'OK')}"
                else:
                    return f"Platform: UNHEALTHY (HTTP {resp.status})"
    except Exception as e:
        logger.error(f"server_status failed: {e}")
        return f"Platform: UNREACHABLE ({e})"


# Tool definitions for Claude's tool_use API
TOOL_DEFINITIONS = [
    {
        "name": "check_bugs",
        "description": "Get QA bug summary showing total, open, and critical bug counts from the HelixNet QA dashboard.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_bug_detail",
        "description": "Get details for a specific bug report by its number (e.g. bug 10 = BUG-010). Returns title, status, severity, description, assigned person, and linked git commits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bug_number": {
                    "type": "integer",
                    "description": "The bug number (e.g. 10 for BUG-010)",
                }
            },
            "required": ["bug_number"],
        },
    },
    {
        "name": "server_status",
        "description": "Check if the HelixNet platform server is healthy and running.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# Map tool names to functions
TOOL_HANDLERS = {
    "check_bugs": lambda **kwargs: check_bugs(),
    "get_bug_detail": lambda **kwargs: get_bug_detail(kwargs["bug_number"]),
    "server_status": lambda **kwargs: server_status(),
}
