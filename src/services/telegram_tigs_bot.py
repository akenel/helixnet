# File: src/services/telegram_tigs_bot.py
"""
Tigs Telegram Bot -- Angel's personal AI co-pilot.

Handles text, voice messages, and slash commands.
Bridges Telegram <-> Claude API with CLAUDE.md context.
Voice transcription via faster-whisper (local, no API).

Usage:
  python -m src.services.telegram_tigs_bot

Required env vars:
  TELEGRAM_BOT_TOKEN        -- from @BotFather
  TELEGRAM_AUTHORIZED_USER_ID -- Angel's Telegram user ID
  ANTHROPIC_API_KEY         -- from console.anthropic.com

"Casa e dove parcheggi." - Home is where you park it.
"""
import asyncio
import json
import logging
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
import anthropic

from src.services.telegram_tigs_tools import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    check_bugs,
    get_bug_detail,
    server_status,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_USER_ID = int(os.environ.get("TELEGRAM_AUTHORIZED_USER_ID", "0"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_HISTORY = int(os.environ.get("TIGS_MAX_HISTORY", "30"))
DB_PATH = os.environ.get("TIGS_DB_PATH", "/data/tigs_memory.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("tigs-bot")

# ---------------------------------------------------------------------------
# System prompt -- loaded from CLAUDE.md at startup
# ---------------------------------------------------------------------------
def load_system_prompt() -> str:
    """Load CLAUDE.md as system context, with bot-specific instructions prepended."""
    bot_instructions = (
        "You are Tigs (Tiger), Angel's personal AI co-pilot, running inside a Telegram bot.\n"
        "You have access to tools that can check the HelixNet QA bug dashboard and server health.\n"
        "Keep responses concise -- Telegram messages should be short and scannable.\n"
        "Use plain text, not markdown (Telegram doesn't render markdown well in all clients).\n"
        "When Angel sends voice messages, they arrive as transcribed text -- respond naturally.\n"
        "You know Angel personally. You are the Tiger, the second arrow. Be direct, helpful, real.\n"
        "No emojis unless Angel asks for them.\n\n"
        "--- CLAUDE.MD CONTEXT BELOW ---\n\n"
    )
    claude_md_path = Path("/app/CLAUDE.md")
    if not claude_md_path.exists():
        # Fallback for local dev
        claude_md_path = Path(__file__).parent.parent.parent / "CLAUDE.md"

    if claude_md_path.exists():
        context = claude_md_path.read_text(encoding="utf-8")
        # Trim to ~8000 chars to keep costs reasonable
        if len(context) > 8000:
            context = context[:8000] + "\n\n[... truncated for token efficiency ...]"
        return bot_instructions + context
    else:
        logger.warning("CLAUDE.md not found, using minimal system prompt")
        return bot_instructions + "No CLAUDE.md context available."


SYSTEM_PROMPT = load_system_prompt()

# ---------------------------------------------------------------------------
# Conversation memory (SQLite)
# ---------------------------------------------------------------------------
class ConversationMemory:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add(self, user_id: int, role: str, content: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        conn.commit()
        conn.close()

    def get_history(self, user_id: int, limit: int = 30) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Whisper (lazy-loaded)
# ---------------------------------------------------------------------------
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' (first voice message)...")
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return _whisper_model


def transcribe_audio(file_path: str) -> str:
    model = get_whisper_model()
    segments, info = model.transcribe(file_path, beam_size=5)
    text = " ".join(segment.text for segment in segments).strip()
    logger.info(f"Transcribed ({info.language}, {info.duration:.1f}s): {text[:80]}...")
    return text


# ---------------------------------------------------------------------------
# Claude client
# ---------------------------------------------------------------------------
claude_client = None

def get_claude():
    global claude_client
    if claude_client is None:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return claude_client


async def chat_with_claude(user_message: str, history: list[dict]) -> str:
    """Send message to Claude with history and tool support."""
    client = get_claude()

    messages = history + [{"role": "user", "content": user_message}]

    # First call -- may request tool use
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOL_DEFINITIONS,
        messages=messages,
    )

    # Handle tool use loop (Claude may call tools)
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                logger.info(f"Claude wants tool: {tool_name}({tool_input})")

                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    result = await handler(**tool_input)
                else:
                    result = f"Unknown tool: {tool_name}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # Send tool results back to Claude
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

    # Extract final text response
    text_parts = [block.text for block in response.content if hasattr(block, "text")]
    return "\n".join(text_parts) if text_parts else "(No response from Claude)"


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()
memory = ConversationMemory(DB_PATH)


def is_authorized(message: types.Message) -> bool:
    if message.from_user and message.from_user.id == AUTHORIZED_USER_ID:
        return True
    logger.warning(f"Unauthorized access attempt from user {message.from_user.id if message.from_user else 'unknown'}")
    return False


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_authorized(message):
        return
    await message.answer(
        "Tigs online. Text me, send voice, or use commands:\n\n"
        "/bugs - QA bug summary\n"
        "/bug 10 - Details for BUG-010\n"
        "/status - Server health\n"
        "/clear - Reset conversation\n"
    )


@dp.message(Command("bugs"))
async def cmd_bugs(message: types.Message):
    if not is_authorized(message):
        return
    await message.answer("Checking bugs...")
    result = await check_bugs()
    await message.answer(result)


@dp.message(Command("bug"))
async def cmd_bug(message: types.Message):
    if not is_authorized(message):
        return
    # Parse bug number from "/bug 10" or "/bug10"
    text = message.text or ""
    parts = text.strip().split()
    bug_num = None
    if len(parts) >= 2:
        try:
            bug_num = int(parts[1])
        except ValueError:
            pass
    if bug_num is None:
        # Try parsing from "/bug10"
        try:
            bug_num = int(text.replace("/bug", "").strip())
        except ValueError:
            await message.answer("Usage: /bug 10")
            return

    await message.answer(f"Looking up BUG-{bug_num:03d}...")
    result = await get_bug_detail(bug_num)
    await message.answer(result)


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if not is_authorized(message):
        return
    await message.answer("Checking server...")
    result = await server_status()
    await message.answer(result)


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not is_authorized(message):
        return
    memory.clear(message.from_user.id)
    await message.answer("Conversation cleared. Fresh start.")


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    if not is_authorized(message):
        return

    await message.answer("Transcribing...")

    try:
        # Download voice file
        file_info = await bot.get_file(message.voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        await bot.download_file(file_info.file_path, tmp_path)

        # Transcribe
        transcript = await asyncio.get_event_loop().run_in_executor(
            None, transcribe_audio, tmp_path
        )

        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        if not transcript:
            await message.answer("Could not transcribe the voice message.")
            return

        # Show what was heard
        await message.answer(f"Heard: {transcript}")

        # Send to Claude
        history = memory.get_history(message.from_user.id, MAX_HISTORY)
        response_text = await chat_with_claude(transcript, history)

        # Store in memory
        memory.add(message.from_user.id, "user", transcript)
        memory.add(message.from_user.id, "assistant", response_text)

        # Telegram has a 4096 char limit per message
        if len(response_text) > 4000:
            for i in range(0, len(response_text), 4000):
                await message.answer(response_text[i:i + 4000])
        else:
            await message.answer(response_text)

    except Exception as e:
        logger.error(f"Voice handling error: {e}", exc_info=True)
        await message.answer(f"Voice error: {e}")


@dp.message(F.text)
async def handle_text(message: types.Message):
    if not is_authorized(message):
        return

    user_text = message.text or ""
    if not user_text.strip():
        return

    try:
        history = memory.get_history(message.from_user.id, MAX_HISTORY)
        response_text = await chat_with_claude(user_text, history)

        # Store in memory
        memory.add(message.from_user.id, "user", user_text)
        memory.add(message.from_user.id, "assistant", response_text)

        # Telegram 4096 char limit
        if len(response_text) > 4000:
            for i in range(0, len(response_text), 4000):
                await message.answer(response_text[i:i + 4000])
        else:
            await message.answer(response_text)

    except Exception as e:
        logger.error(f"Text handling error: {e}", exc_info=True)
        await message.answer(f"Error: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Exiting.")
        return
    if not AUTHORIZED_USER_ID:
        logger.error("TELEGRAM_AUTHORIZED_USER_ID not set. Exiting.")
        return
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Exiting.")
        return

    logger.info(f"Tigs bot starting (model: {CLAUDE_MODEL}, history: {MAX_HISTORY} msgs)")
    logger.info(f"Authorized user: {AUTHORIZED_USER_ID}")
    logger.info(f"System prompt: {len(SYSTEM_PROMPT)} chars loaded")

    # Long-polling -- no webhook needed, works behind any NAT/firewall
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
