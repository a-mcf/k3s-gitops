"""Merge pronunciation overrides into misaki's British lexicons in place.

Background: https://github.com/a-mcf/kokoro-alba/issues/1
Remove when Kokoro-FastAPI supports custom lexicon entries.

After writing, the lexicons are loaded the way the server loads them. If that
fails, the original files are restored and the script exits non-zero.
"""

import json
import pathlib
import sys

import misaki.data

DATA = pathlib.Path(misaki.data.__file__).parent
FILES = ("gb_gold.json", "gb_silver.json")

# Whole-word replacements, gold lexicon only.
WORDS = {"yeah": "jˈɛ"}

# Word-final ə becomes ʌ unless the spelling ends in r/re. Function words and
# abbreviations (Dr., Mr., No.) keep their stock pronunciation. The
# replacement must be in misaki's GB_VOCAB or the gold lexicon fails to load.
FINAL_SCHWA = "ʌ"
SKIP = {"the", "a", "to"}


def final_schwa(word, ps):
    """Return ps with a word-final ə replaced, where the rule applies."""
    if word.lower() in SKIP or word.endswith(".") or word.lower().endswith(("r", "re")):
        return ps
    if isinstance(ps, dict):
        return {tag: final_schwa(word, p) for tag, p in ps.items()}
    if ps and ps.endswith("ə"):
        return ps[:-1] + FINAL_SCHWA
    return ps


def rewrite(name, words):
    """Apply the rule and the word overrides to one lexicon file."""
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


def main():
    """Rewrite the lexicons, then prove misaki still loads them."""
    originals = {name: (DATA / name).read_bytes() for name in FILES}
    try:
        rewrite("gb_gold.json", WORDS)
        rewrite("gb_silver.json", {})
        from misaki.en import Lexicon  # pylint: disable=import-outside-toplevel

        Lexicon(british=True)
    except Exception as err:  # pylint: disable=broad-exception-caught
        for name, data in originals.items():
            (DATA / name).write_bytes(data)
        sys.exit(f"lexicon overrides: rejected, originals restored: {err!r}")


if __name__ == "__main__":
    main()
