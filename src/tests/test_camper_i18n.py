"""
Test: Camper & Tour i18n dictionary consistency.
Verifies every IT key has an EN counterpart and vice versa.
Run: pytest src/tests/test_camper_i18n.py -v
"""
import json
import re
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parents[1] / "static" / "camper-i18n.js"


def _js_to_json(js_text: str) -> str:
    """Convert a JavaScript object literal to valid JSON.

    Handles:
    - Single-line // comments
    - Multi-line /* */ comments
    - Single-quoted strings -> double-quoted
    - Trailing commas before } or ]
    - Unquoted object keys
    """
    # Remove single-line comments (but not inside strings)
    text = re.sub(r'//[^\n]*', '', js_text)
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Convert single-quoted strings to double-quoted
    # Walk char by char to handle escapes correctly
    result = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            # Start of single-quoted string -- convert to double-quoted
            result.append('"')
            i += 1
            while i < len(text) and text[i] != "'":
                if text[i] == '\\' and i + 1 < len(text):
                    next_ch = text[i + 1]
                    if next_ch == "'":
                        # \' in JS single-quoted string -> just ' in double-quoted
                        result.append("'")
                        i += 2
                    elif next_ch in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                        # Valid JSON escapes -- keep as-is
                        result.append(text[i])
                        result.append(next_ch)
                        i += 2
                    else:
                        # Unknown escape -- drop the backslash
                        result.append(next_ch)
                        i += 2
                elif text[i] == '"':
                    # Escape double quotes inside the string
                    result.append('\\"')
                    i += 1
                else:
                    result.append(text[i])
                    i += 1
            result.append('"')
            i += 1  # skip closing '
        elif ch == '"':
            # Already double-quoted string -- pass through
            result.append(ch)
            i += 1
            while i < len(text) and text[i] != '"':
                if text[i] == '\\' and i + 1 < len(text):
                    result.append(text[i])
                    result.append(text[i + 1])
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            if i < len(text):
                result.append(text[i])
                i += 1
        else:
            result.append(ch)
            i += 1

    text = ''.join(result)

    # Quote unquoted object keys: word_chars followed by :
    text = re.sub(r'(?<=[\{,\n])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r' "\1":', text)

    # Remove trailing commas (before } or ])
    text = re.sub(r',\s*([}\]])', r'\1', text)

    return text


def _load_dictionary() -> dict:
    """Parse the JS dictionary file in pure Python (no Node.js needed)."""
    raw = DICT_PATH.read_text(encoding='utf-8')

    # Extract the object literal: everything between first { and last }
    first_brace = raw.index('{')
    last_brace = raw.rindex('}')
    obj_text = raw[first_brace:last_brace + 1]

    json_text = _js_to_json(obj_text)
    data = json.loads(json_text)

    # Flatten nested dicts into dotted key paths
    def collect_keys(obj, prefix=''):
        keys = []
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(collect_keys(v, path))
            else:
                keys.append({
                    'path': path,
                    'type': 'array' if isinstance(v, list) else type(v).__name__,
                    'value': str(v),
                })
        return keys

    return {
        'langs': list(data.keys()),
        'it': collect_keys(data.get('it', {})),
        'en': collect_keys(data.get('en', {})),
    }


def test_dictionary_parses():
    """The JS dictionary file can be parsed without Node.js."""
    data = _load_dictionary()
    assert "it" in data["langs"]
    assert "en" in data["langs"]


def test_it_and_en_have_same_keys():
    """Every IT key exists in EN and vice versa."""
    data = _load_dictionary()
    it_keys = {e["path"] for e in data["it"]}
    en_keys = {e["path"] for e in data["en"]}

    missing_in_en = it_keys - en_keys
    missing_in_it = en_keys - it_keys

    errors = []
    if missing_in_en:
        errors.append(f"Keys in IT but missing in EN ({len(missing_in_en)}):\n  " +
                      "\n  ".join(sorted(missing_in_en)))
    if missing_in_it:
        errors.append(f"Keys in EN but missing in IT ({len(missing_in_it)}):\n  " +
                      "\n  ".join(sorted(missing_in_it)))

    assert not errors, "\n".join(errors)


def test_no_empty_translations():
    """No translation value should be an empty string."""
    data = _load_dictionary()
    empties = []
    for lang in ["it", "en"]:
        for entry in data[lang]:
            if entry["type"] == "str" and entry["value"].strip() == "":
                empties.append(f"{lang}.{entry['path']}")

    assert not empties, f"Empty translations found:\n  " + "\n  ".join(empties)


def test_en_differs_from_it():
    """At least some EN values differ from IT (i.e. not just a copy)."""
    data = _load_dictionary()
    it_map = {e["path"]: e["value"] for e in data["it"] if e["type"] == "str"}
    en_map = {e["path"]: e["value"] for e in data["en"] if e["type"] == "str"}

    common = set(it_map) & set(en_map)
    different = sum(1 for k in common if it_map[k] != en_map[k])
    total = len(common)

    ratio = different / total if total else 0
    assert ratio > 0.5, (
        f"Only {different}/{total} ({ratio:.0%}) strings differ between IT and EN. "
        f"Expected >50% to be different translations."
    )


def test_minimum_key_count():
    """Dictionary should have a reasonable number of keys (guards against truncation)."""
    data = _load_dictionary()
    it_count = len(data["it"])
    en_count = len(data["en"])

    assert it_count >= 400, f"IT has only {it_count} keys, expected 400+"
    assert en_count >= 400, f"EN has only {en_count} keys, expected 400+"
