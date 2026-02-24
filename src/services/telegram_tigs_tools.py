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


async def check_backlog() -> str:
    """Get backlog summary: total, pending, in_progress, blocked, done."""
    try:
        conn = await _get_pg_connection()
        try:
            rows = await conn.fetch("""
                SELECT status, COUNT(*) AS cnt
                FROM backlog_items
                WHERE status != 'archived'
                GROUP BY status
            """)
            counts = {r['status']: r['cnt'] for r in rows}
            total = sum(counts.values())
            return (
                f"Backlog: {total} items\n"
                f"  Pending: {counts.get('pending', 0)}\n"
                f"  In Progress: {counts.get('in_progress', 0)}\n"
                f"  Blocked: {counts.get('blocked', 0)}\n"
                f"  Done: {counts.get('done', 0)}"
            )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"check_backlog failed: {e}")
        return f"Error querying backlog: {e}"


async def get_backlog_item_detail(item_number: int) -> str:
    """Get details for a backlog item by number (e.g. BL-005)."""
    try:
        conn = await _get_pg_connection()
        try:
            item = await conn.fetchrow("""
                SELECT item_number, title, description, item_type, status,
                       priority, assigned_to, due_date, tags,
                       blocked_reason, created_by, created_at, updated_at
                FROM backlog_items
                WHERE item_number = $1
            """, item_number)

            if not item:
                return f"BL-{item_number:03d} not found."

            lines = [
                f"BL-{item['item_number']:03d}: {item['title']}",
                f"Type: {item['item_type']} | Status: {item['status']} | Priority: {item['priority']}",
                f"Assigned: {item['assigned_to'] or 'unassigned'}",
                f"Created by: {item['created_by']} on {item['created_at'].strftime('%Y-%m-%d')}",
            ]
            if item['due_date']:
                lines.append(f"Due: {item['due_date']}")
            if item['tags']:
                lines.append(f"Tags: {item['tags']}")
            if item['blocked_reason']:
                lines.append(f"BLOCKED: {item['blocked_reason']}")
            if item['description']:
                desc = item['description'][:200]
                if len(item['description']) > 200:
                    desc += "..."
                lines.append(f"Description: {desc}")
            return "\n".join(lines)
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"get_backlog_item_detail failed: {e}")
        return f"Error querying backlog item {item_number}: {e}"


async def update_backlog_status(item_number: int, new_status: str) -> str:
    """Change the status of a backlog item."""
    valid = ('pending', 'in_progress', 'blocked', 'done', 'archived')
    if new_status not in valid:
        return f"Invalid status '{new_status}'. Must be one of: {', '.join(valid)}"
    try:
        conn = await _get_pg_connection()
        try:
            item = await conn.fetchrow(
                "SELECT id, item_number, title, status FROM backlog_items WHERE item_number = $1",
                item_number,
            )
            if not item:
                return f"BL-{item_number:03d} not found."

            old_status = item['status']
            if old_status == new_status:
                return f"BL-{item_number:03d} is already {new_status}."

            await conn.execute(
                "UPDATE backlog_items SET status = $1, updated_at = NOW() WHERE item_number = $2",
                new_status, item_number,
            )
            # Log activity
            await conn.execute("""
                INSERT INTO backlog_activities (id, item_id, activity_type, actor, old_value, new_value, created_at)
                VALUES (gen_random_uuid(), $1, 'status_change', 'Tigs', $2, $3, NOW())
            """, item['id'], old_status, new_status)

            return f"BL-{item_number:03d} ({item['title']}): {old_status} -> {new_status}"
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"update_backlog_status failed: {e}")
        return f"Error updating BL-{item_number:03d}: {e}"


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
    {
        "name": "check_backlog",
        "description": "Get backlog summary showing item counts by status (pending, in_progress, blocked, done).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_backlog_item_detail",
        "description": "Get details for a specific backlog item by number (e.g. 5 for BL-005). Returns title, type, status, priority, description, and assigned person.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_number": {
                    "type": "integer",
                    "description": "The backlog item number (e.g. 5 for BL-005)",
                }
            },
            "required": ["item_number"],
        },
    },
    {
        "name": "update_backlog_status",
        "description": "Change the status of a backlog item. Valid statuses: pending, in_progress, blocked, done, archived.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_number": {
                    "type": "integer",
                    "description": "The backlog item number (e.g. 5 for BL-005)",
                },
                "new_status": {
                    "type": "string",
                    "description": "New status: pending, in_progress, blocked, done, or archived",
                    "enum": ["pending", "in_progress", "blocked", "done", "archived"],
                },
            },
            "required": ["item_number", "new_status"],
        },
    },
]

# Map tool names to functions
TOOL_HANDLERS = {
    "check_bugs": lambda **kwargs: check_bugs(),
    "get_bug_detail": lambda **kwargs: get_bug_detail(kwargs["bug_number"]),
    "server_status": lambda **kwargs: server_status(),
    "check_backlog": lambda **kwargs: check_backlog(),
    "get_backlog_item_detail": lambda **kwargs: get_backlog_item_detail(kwargs["item_number"]),
    "update_backlog_status": lambda **kwargs: update_backlog_status(kwargs["item_number"], kwargs["new_status"]),
}
