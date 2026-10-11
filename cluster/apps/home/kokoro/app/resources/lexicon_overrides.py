"""Merge pronunciation overrides into misaki's British lexicons in place.

Background: https://github.com/a-mcf/kokoro-alba/issues/1
Remove when Kokoro-FastAPI supports custom lexicon entries.
"""

import json
import pathlib

import misaki.data

DATA = pathlib.Path(misaki.data.__file__).parent

# Whole-word replacements, gold lexicon only.
WORDS = {"yeah": "jˈɛ"}

# Word-final ə becomes ɐ unless the spelling ends in r/re. Function words and
# abbreviations (Dr., Mr., No.) keep their stock pronunciation.
SKIP = {"the", "a", "to"}


def final_schwa(word, ps):
    if word.lower() in SKIP or word.endswith(".") or word.lower().endswith(("r", "re")):
        return ps
    if isinstance(ps, dict):
        return {tag: final_schwa(word, p) for tag, p in ps.items()}
    if ps and ps.endswith("ə"):
        return ps[:-1] + "ɐ"
    return ps


for name, words in (("gb_gold.json", WORDS), ("gb_silver.json", {})):
    path = DATA / name
    lex = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for word, ps in lex.items():
        new = final_schwa(word, ps)
        if new != ps:
            lex[word] = new
            changed += 1
    lex.update(words)
    path.write_text(json.dumps(lex, ensure_ascii=False), encoding="utf-8")
    print(f"lexicon overrides: {name}: {changed} final-schwa, {len(words)} word(s)")
