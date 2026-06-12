# Tests for the Today "breakdowns" task helpers in bottega_router (pure, no DB/HTTP):
# the crew sanitizer, the append-only history log, and the task->view serializer.
import json
from types import SimpleNamespace

from src.routes import bottega_router as br


# --- _clean_collaborators: the crew list normaliser --------------------------------------

def test_clean_collaborators_accepts_strings_and_dicts_drops_empties():
    out = br._clean_collaborators(
        ["Tesla", {"who": "Da Vinci", "role": "the paintings"}, {"who": ""}, 5, {"role": "x"}])
    assert out == [{"who": "Tesla", "role": ""},
                   {"who": "Da Vinci", "role": "the paintings"}]


def test_clean_collaborators_caps_and_handles_none():
    assert br._clean_collaborators(None) == []
    out = br._clean_collaborators([{"who": f"m{i}"} for i in range(50)])
    assert len(out) == 20


# --- _log_history: a little version control ----------------------------------------------

def test_log_history_appends_on_change_and_skips_noop():
    t = SimpleNamespace(history=None)
    br._log_history(t, "title", "a", "a", by="x")      # unchanged -> nothing
    assert t.history is None
    br._log_history(t, "title", "a", "b", by="angel")
    h = json.loads(t.history)
    assert len(h) == 1
    row = h[0]
    assert (row["field"], row["from"], row["to"], row["by"]) == ("title", "a", "b", "angel")
    assert "at" in row


def test_log_history_is_bounded_to_the_cap():
    t = SimpleNamespace(history=None)
    for i in range(60):
        br._log_history(t, "sort_order", i, i + 1, by="x")
    h = json.loads(t.history)
    assert len(h) == br._HISTORY_CAP == 50
    assert h[-1]["to"] == 60        # newest kept
    assert h[0]["to"] == 11         # oldest 10 dropped


# --- _task_view: the wire shape ----------------------------------------------------------

def _fake_task(**kw):
    base = dict(id="abc", day="2026-06-12", section="top10", title="x", notes=None,
                status="open", sort_order=3, parent_id=None, estimate_min=None,
                assignee=None, house=None, collaborators=None, project=None,
                task_key=None, history=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_task_view_exposes_all_breakdown_fields():
    t = _fake_task(estimate_min=90, assignee="angel", house="The Atelier",
                   collaborators=json.dumps([{"who": "Tesla", "role": "the idea"}]),
                   project="bottega", task_key="BOTTEGA-1",
                   history=json.dumps([{"field": "house", "from": None, "to": "The Atelier"}]))
    v = br._task_view(t)
    assert v["estimate_min"] == 90
    assert v["assignee"] == "angel"
    assert v["house"] == "The Atelier"
    assert v["collaborators"] == [{"who": "Tesla", "role": "the idea"}]
    assert (v["project"], v["task_key"]) == ("bottega", "BOTTEGA-1")
    assert v["parent_id"] is None
    assert len(v["history"]) == 1


def test_task_view_survives_corrupt_json_blobs():
    t = _fake_task(collaborators="{not json", history="garbage")
    v = br._task_view(t)
    assert v["collaborators"] == [] and v["history"] == []


# --- _board_facts: the grounded brief Cleo nudges from (A — the living crew) --------------

def test_board_facts_separates_done_open_and_tbd():
    tasks = [
        {"title": "Ship it", "status": "done", "task_key": "BOTTEGA-1", "assignee": "angel"},
        {"title": "Run Sheet", "status": "open", "house": "The Forge"},      # open, has a House
        {"title": "Floating", "status": "open"},                              # open + unassigned -> TBD
        {"title": "a step", "status": "done", "parent_id": "x"},              # sub-task, not a top line
    ]
    f = br._board_facts(tasks, "2026-06-12")
    assert "DONE (1):" in f and "Ship it" in f
    assert "OPEN (2):" in f and "Run Sheet" in f and "House: The Forge" in f
    assert "WAITING / unassigned: Floating" in f
    assert "Breakdown steps: 1 of 1 done" in f


def test_board_facts_empty_board_invites_a_first_win():
    f = br._board_facts([], "2026-06-12")
    assert "board is empty" in f.lower()
