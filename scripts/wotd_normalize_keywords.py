"""Normalize wotd.csv keyword column:
1. Strip junk prefixes / duplicated suffixes ("Word of the Day xxx", "EQ class EQ", ":swimming class", etc.)
2. Convert legacy POS tags `(n)` `(v)` `(adj)` → `(n.)` `(v.)` `(adj.)` `(adv.)` etc.
3. For keywords with no POS at all, infer + append correct tag.

This is idempotent — run again on the same file produces no further changes.
"""
import csv
import re
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "wotd.csv"

# 1. Data cleanup — patterns that strip / collapse to a clean head keyword.
JUNK_FIX = {
    # leading garbage
    ":swimming class": "swimming class",
    "warm up )n)": "warm up",
    # duplicated trailing tag (e.g., "100 meter dash 100")
    "100 meter dash 100": "100 meter dash",
    "3D movie 3D": "3D movie",
    "EQ class EQ": "EQ class",
    "SH150 program SH150": "SH150 program",
    "ICRT radio station ICRT": "ICRT radio station",
    "HIV AIDS": "HIV/AIDS",
    "three on three basketball": "3-on-3 basketball",
    "3 on 3 basketball game": "3-on-3 basketball game",
    "Word of the Day Christmas": "Christmas",
    "Word of the Day Christmas tree": "Christmas tree",
    "Word of the Day Mother's Day card": "Mother's Day card",
    "Word of the Day PE class": "PE class",
    "Word of the Day Taiwanese opera": "Taiwanese opera",
    "Word of the Day art camp": "art camp",
    "Word of the Day bottle rocket": "bottle rocket",
    "Word of the Day care": "care",
    "Word of the Day egg hunt": "egg hunt",
    "Word of the Day evacuation drill": "evacuation drill",
    "Word of the Day exercise": "exercise",
    "Word of the Day gate": "gate",
    "Word of the Day hairstylist": "hairstylist",
    "Word of the Day ice rice dumpling": "ice rice dumpling",
    "Word of the Day mop": "mop",
    "Word of the Day mouthwash": "mouthwash",
    "Word of the Day professional development": "professional development",
    "Word of the Day read aloud competition": "read aloud competition",
    "Word of the Day run": "run",
    "Word of the Day scrimmage": "scrimmage",
    "Word of the Day shot put (n)": "shot put",
    "Word of the Day test": "test",
    "Word of the Day ukulele": "ukulele",
    "Word of the Day wash: your hands": "wash your hands",
    "Word of the Day-team": "team",
    "Chinese yo yo": "Chinese yo-yo",
    "rock-paper-scissors": "rock-paper-scissors",
    "rock paper scissors": "rock-paper-scissors",
    "leaf / leaves": "leaf",
    "Halo halo": "halo-halo",
    "eco pond": "eco-pond",
    "icebreaker game": "ice-breaker game",
    "ice breaker games": "ice-breaker game",
    "after school program": "after-school program",
    "Mother's Day cards": "Mother's Day card",
    "dance performances": "dance performance",
    "rice balls": "rice ball",
    "spring couplets": "spring couplet",
    "Mid Autumn Festival": "Mid-Autumn Festival",
    "Mother Language Day": "Mother Language Day",
    "self assessment": "self-assessment",
    "Pacer Test": "PACER test",
    "PaGamO": "PaGamO",
    # Malformed parens / duplicated tag tails
    "HSR (high speed rail ) station": "HSR station",
    "IQ light (n) IQ": "IQ light",
    "vote (n) (": "vote",
    "healthy (a)": "healthy (adj.)",
    "worksheet (": "worksheet",
    "fire station (n )": "fire station",
    "3D movie (n) 3D": "3D movie",
    "table (n).": "table",
}

# 2. Legacy POS form → new period form.
POS_LEGACY_RE = re.compile(r"\((n|v|adj|adv|prep|conj|pron|art|num|interj)\)$")

def add_dot_to_pos(kw):
    """Replace trailing `(n)` with `(n.)` (and v/adj/adv/etc.)."""
    return POS_LEGACY_RE.sub(lambda m: f"({m.group(1)}.)", kw)


# 3. POS inference for keywords with no POS at all.
#    Default = noun; explicit verb / adjective / adverb sets cover exceptions.

VERBS = {
    "assemble", "bake", "baking", "brush teeth", "brush your teeth", "celebrate",
    "check in", "check out", "check-in", "clean the floor", "climbing trees",
    "color in", "cook", "cross", "cross stitch", "cut out", "dance", "doodle",
    "draw", "drop off", "dye", "enter the field", "exercise", "experience",
    "farm", "farming", "fly kites", "go over", "go to school", "grow vegetables",
    "hiking", "hiking trip", "jump", "learn", "learn English", "make believe",
    "make kites", "mark", "observe", "paint", "pass", "perform a dance", "play",
    "play catch", "play the guitar", "point", "practice", "raise your hand",
    "rake", "read", "relax", "report the news", "roller-skate", "rollerblade",
    "rub", "scoop up", "serve", "shoot", "shoot hoops", "stay active", "stretch",
    "sweep", "swing", "take a nap", "take a walk", "tells a story", "throw",
    "tie shoelaces", "turn on/off", "wash hands", "wash your hands", "wipe",
    "work together", "write", "tell time", "rock climb", "spring", "color",
    "go", "team", "match",
}

ADJECTIVES = {
    "bilingual", "outdoor", "horizontal plane",
}

ADVERBS = {
    "step by step",
}


def infer_pos(kw):
    """Return 'n.' / 'v.' / 'adj.' / 'adv.' for a cleaned keyword without POS."""
    if kw in VERBS:
        return "v."
    if kw in ADJECTIVES:
        return "adj."
    if kw in ADVERBS:
        return "adv."
    return "n."


SPACE_BEFORE_POS_RE = re.compile(r"(\S)(\([nva][a-z]*\.?\))")
DOUBLE_OPEN_PAREN_RE = re.compile(r"\(+(\([nva][a-z]*\.\)\s*)$")

def fix_spacing(kw):
    # "word(n.)" → "word (n.)"
    kw = SPACE_BEFORE_POS_RE.sub(r"\1 \2", kw)
    # "word ((n.)" → "word (n.)"
    kw = re.sub(r"\(\((n|v|adj|adv|prep|conj|pron)\.\)", r"(\1.)", kw)
    return kw

def normalize_keyword(raw):
    """Clean + add POS tag. Returns (new_kw, action) where action ∈ {clean, addpos, dotpos, noop}."""
    kw = raw.strip()

    # Step 1: junk cleanup
    cleaned = JUNK_FIX.get(kw, kw)
    if cleaned != kw:
        kw = cleaned

    # Step 1.5: fix spacing/double-parens (e.g., "memorize(v.)" → "memorize (v.)")
    kw = fix_spacing(kw)

    # Step 2: legacy POS form
    new_kw = add_dot_to_pos(kw)
    if new_kw != kw:
        return new_kw, "dotpos"

    # Step 3: missing POS entirely
    if "(" not in kw:
        pos = infer_pos(kw)
        return f"{kw} ({pos})", "addpos"

    # Spacing/cleanup-only path
    if kw != raw.strip():
        return kw, "clean"
    return kw, "noop"


def main():
    with CSV_PATH.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        fields = rdr.fieldnames

    counts = {"clean": 0, "addpos": 0, "dotpos": 0, "noop": 0}
    for r in rows:
        new_kw, action = normalize_keyword(r["keyword"])
        if new_kw != r["keyword"]:
            r["keyword"] = new_kw
        counts[action] += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"Total rows: {len(rows)}")
    print(f"  Cleaned junk:           {counts['clean']}")
    print(f"  Added POS:              {counts['addpos']}")
    print(f"  Converted (X) → (X.):   {counts['dotpos']}")
    print(f"  No change:              {counts['noop']}")


if __name__ == "__main__":
    main()
