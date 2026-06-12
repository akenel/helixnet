# Tests for the keystone (#107) discussion-thread CORE:
#  - the router-side thread assembly (a chain of bottega_sessions rows -> the engine transcript)
#  - the persona-param engine turn (concierge.thread_reply) -- the masters-as-tools seam where the
#    persona (a master's definition) is data, not hardcoded.
# Pure + monkeypatched brain; no DB, no HTTP. asyncio_mode=auto runs the async tests directly.
import json
from types import SimpleNamespace

import pytest

from src.compute import concierge as cc
from src.routes import bottega_router as br


def _row(output, inputs):
    return SimpleNamespace(output=output, inputs=json.dumps(inputs))


# --- router: rows -> transcript ----------------------------------------------------------
def test_turn_author_uses_explicit_role():
    a, r = br._turn_author(_row("hi", {"author": "Cleopatra", "role": "master"}), owner="angel")
    assert (a, r) == ("Cleopatra", "master")


def test_turn_author_infers_member_from_owner():
    a, r = br._turn_author(_row("hi", {"author": "angel"}), owner="angel")
    assert (a, r) == ("angel", "member")


def test_turn_author_legacy_nudge_row_reads_as_master():
    # legacy _deliver_message rows carry only {from, read} -- a nudge is the master speaking
    a, r = br._turn_author(_row("nudge", {"from": "Cleopatra", "read": False}), owner="angel")
    assert (a, r) == ("Cleopatra", "master")


def test_turn_author_survives_corrupt_inputs():
    a, r = br._turn_author(SimpleNamespace(output="x", inputs="{bad json"), owner="angel")
    assert a == "" and r == "master"   # no author -> not the owner -> master


def test_thread_transcript_maps_roles_in_order():
    rows = [
        _row("Welcome -- here's your board", {"author": "Cleopatra", "role": "master"}),
        _row("what should I do first?", {"author": "angel", "role": "member"}),
    ]
    t = br._thread_transcript(rows, owner="angel")
    assert [x["role"] for x in t] == ["master", "member"]
    assert t[1]["content"] == "what should I do first?"
    assert t[0]["author"] == "Cleopatra"


# --- concierge: the persona-param engine turn (author = master_id seam) -------------------
@pytest.mark.asyncio
async def test_thread_reply_passes_persona_and_strips_think(monkeypatch):
    captured = {}

    async def fake_brain(system, user, **kw):
        captured["system"] = system
        captured["user"] = user
        return "<think>scheming</think>Rise, and tell me more."

    monkeypatch.setattr(cc, "_brain_chat", fake_brain)
    transcript = [{"role": "member", "content": "I want to start over at 60"}]
    out = await cc.thread_reply(transcript, record={"goal": "reinvent myself"},
                                persona="PERSONA-X", language="en")
    assert out == "Rise, and tell me more."             # <think> stripped
    assert captured["system"].startswith("PERSONA-X")    # persona is DATA -- the master plugs in here
    assert "reinvent myself" in captured["user"]         # grounded by the member's record


@pytest.mark.asyncio
async def test_thread_reply_defaults_to_cleopatra(monkeypatch):
    captured = {}

    async def fake_brain(system, user, **kw):
        captured["system"] = system
        return "Welcome to the court."

    monkeypatch.setattr(cc, "_brain_chat", fake_brain)
    await cc.thread_reply([{"role": "member", "content": "hello"}], record={})
    assert captured["system"].startswith(cc.BRAIN[:40])   # default persona = Cleopatra's BRAIN


# --- integration: the keystone loop on the real spine (SQLite fixture) --------------------
from src.db.models.bottega_model import BottegaSessionModel   # noqa: E402


# NOTE: the conftest in-memory DB is shared across a file (drop_all fails on an unrelated FK cycle),
# so each integration test uses a UNIQUE owner to stay isolated on the leaky shared DB.
async def _nudge_root(db, owner="angel", body="Welcome -- 2 of 5 done. Next: the Run Sheet."):
    root = BottegaSessionModel(
        username=owner, slug="message", title="Cleopatra", parent_id=None,
        inputs=json.dumps({"from": "Cleopatra", "read": False}),
        output=body, output_type="text", tags="message")
    db.add(root)
    await db.commit()
    return root


@pytest.mark.asyncio
async def test_reply_loop_persists_both_turns_and_grounds_the_engine(db_session, monkeypatch):
    root = await _nudge_root(db_session, owner="angel_loop")
    seen = {}

    async def fake_thread_reply(transcript, record, persona="", language=""):
        seen["transcript"] = transcript
        seen["persona"] = persona
        return "A fine question. Start with the smallest stone."

    monkeypatch.setattr(br.cg, "thread_reply", fake_thread_reply)

    resp = await br.reply_to_thread(
        str(root.id), br.ThreadReply(message="Where do I start?"),
        current_user={"username": "angel_loop"}, db=db_session)

    # response: root + member + master, in order; the master's reply surfaced
    assert [t["role"] for t in resp["turns"]] == ["master", "member", "master"]
    assert resp["turns"][1]["body"] == "Where do I start?"   # turn VIEWS expose body
    assert resp["reply"]["author"] == "Cleopatra"
    assert resp["reply"]["body"].startswith("A fine question")

    # the engine saw the whole thread, member's turn last, persona = Cleopatra (author=master_id)
    assert [t["role"] for t in seen["transcript"]] == ["master", "member"]
    assert seen["transcript"][-1]["content"] == "Where do I start?"
    assert seen["persona"] == br.cg.BRAIN

    # persisted: two child rows under the root; root now read
    root2, children = await br._load_thread(db_session, root.id, "angel_loop")
    assert len(children) == 2
    assert json.loads(root2.inputs)["read"] is True


@pytest.mark.asyncio
async def test_reply_rejects_a_thread_that_isnt_yours(db_session, monkeypatch):
    root = await _nudge_root(db_session, owner="someone_else")
    monkeypatch.setattr(br.cg, "thread_reply",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call brain")))
    with pytest.raises(br.HTTPException) as ei:
        await br.reply_to_thread(str(root.id), br.ThreadReply(message="hi"),
                                 current_user={"username": "angel"}, db=db_session)
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_inbox_shows_roots_only_with_reply_counts(db_session, monkeypatch):
    root = await _nudge_root(db_session, owner="angel_inbox")

    async def fake_thread_reply(transcript, record, persona="", language=""):
        return "Indeed."

    monkeypatch.setattr(br.cg, "thread_reply", fake_thread_reply)
    await br.reply_to_thread(str(root.id), br.ThreadReply(message="ok"),
                             current_user={"username": "angel_inbox"}, db=db_session)

    inbox = await br.me_inbox(current_user={"username": "angel_inbox"}, db=db_session)
    msgs = [i for i in inbox["items"] if i["kind"] == "message"]
    assert len(msgs) == 1                       # the two reply turns do NOT show as loose items
    assert msgs[0]["replies"] == 2              # member + master turns counted under the root
