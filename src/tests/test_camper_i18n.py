"""
Test: Camper & Tour i18n dictionary consistency.
Verifies every IT key has an EN counterpart and vice versa.
Run: pytest src/tests/test_camper_i18n.py -v --noconftest
"""
import json
import subprocess
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parents[2] / "src" / "static" / "camper-i18n.js"

# Small Node script that loads the JS file and dumps the structure as JSON
_NODE_SCRIPT = """
const fs = require('fs');
const code = fs.readFileSync(process.argv[1], 'utf8');
const CAMPER_STRINGS = (new Function(code + '; return CAMPER_STRINGS;'))();
function collectKeys(obj, prefix) {
    let keys = [];
    for (const [k, v] of Object.entries(obj)) {
        const path = prefix ? prefix + '.' + k : k;
        if (v && typeof v === 'object' && !Array.isArray(v)) {
            keys = keys.concat(collectKeys(v, path));
        } else {
            keys.push({path, type: Array.isArray(v) ? 'array' : typeof v, value: String(v)});
        }
    }
    return keys;
}
const result = {
    langs: Object.keys(CAMPER_STRINGS),
    it: collectKeys(CAMPER_STRINGS.it, ''),
    en: collectKeys(CAMPER_STRINGS.en, ''),
};
console.log(JSON.stringify(result));
"""


def _load_dictionary():
    """Use Node.js to parse the JS dictionary and return structured key info."""
    result = subprocess.run(
        ["node", "-e", _NODE_SCRIPT, str(DICT_PATH)],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, f"Node parse failed:\n{result.stderr}"
    return json.loads(result.stdout)


def test_dictionary_parses():
    """The JS dictionary file can be parsed by Node."""
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
            if entry["type"] == "string" and entry["value"].strip() == "":
                empties.append(f"{lang}.{entry['path']}")

    assert not empties, f"Empty translations found:\n  " + "\n  ".join(empties)


def test_en_differs_from_it():
    """At least some EN values differ from IT (i.e. not just a copy)."""
    data = _load_dictionary()
    it_map = {e["path"]: e["value"] for e in data["it"] if e["type"] == "string"}
    en_map = {e["path"]: e["value"] for e in data["en"] if e["type"] == "string"}

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
