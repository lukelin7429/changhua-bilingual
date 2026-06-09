#!/usr/bin/env python3
"""Extract each hub-platform school's brand palette from their index.html :root block.
Picks 3 colors per school: primary, secondary (accent), deep (for hero gradient)."""
import re
import yaml
from pathlib import Path

REPO = Path.home() / "Documents/Claude/repos/changhua-bilingual"

SLUG_FOLDER_FIX = {"beidou-jh":"beidou-jhs","fusing-jh":"fusing-jhs"}

with open(REPO / "data/schools.yml") as f:
    data = yaml.safe_load(f)

hub_schools = [s for s in data["schools"] if s.get("platform") == "hub"]

def extract_root_vars(html):
    """Return dict of CSS custom property name → hex color string, e.g. {'red-deep': '#a52836'}"""
    # Find first :root{...} block
    m = re.search(r':root\s*\{([^}]+)\}', html, re.DOTALL)
    if not m:
        return {}
    body = m.group(1)
    vars_ = {}
    for line in re.finditer(r'--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;', body):
        vars_[line.group(1)] = line.group(2).lower()
    return vars_

def pick_palette(vars_, slug):
    """Pick (primary_deep, primary_light, accent) from the school's :root vars.
    Heuristic: prefer *-deep names, fall back to first available."""
    keys = list(vars_.keys())

    # Find primary deep: prefer keys ending in -deep that aren't blue/grey/ink
    deep_candidates = [k for k in keys if k.endswith("-deep")]
    primary_deep = None
    for k in deep_candidates:
        if any(x in k for x in ("ink", "shadow", "line")): continue
        primary_deep = vars_[k]
        primary_key = k
        break
    if not primary_deep and deep_candidates:
        primary_deep = vars_[deep_candidates[0]]
        primary_key = deep_candidates[0]

    # Find a SECOND deep color for hero gradient (different hue than primary)
    secondary_deep = None
    for k in deep_candidates:
        if k == primary_key: continue
        if any(x in k for x in ("ink", "shadow", "line")): continue
        secondary_deep = vars_[k]
        break

    # Find accent (gold/sun/olive — for eyebrow and CTA)
    accent = None
    for k in keys:
        if any(x in k for x in ("gold", "sun", "olive", "yellow")):
            if not k.endswith(("-soft", "-deep")):
                accent = vars_[k]
                break
    if not accent:
        # fall back to any non-deep, non-soft color that's not the primary
        for k in keys:
            v = vars_[k]
            if v in (primary_deep, secondary_deep): continue
            if any(x in k for x in ("ink", "shadow", "line", "cream", "soft")): continue
            accent = v
            break

    # Fallbacks
    if not primary_deep:  primary_deep = "#a52836"
    if not secondary_deep: secondary_deep = "#1f3a6e"
    if not accent: accent = "#d89a3c"

    return primary_deep, secondary_deep, accent

print(f"{'slug':18} {'primary':9} {'secondary':9} {'accent':9}  vars_count")
print("-" * 70)

palettes = {}
for s in hub_schools:
    yslug = s["slug"]
    folder = SLUG_FOLDER_FIX.get(yslug, yslug)
    html = (REPO / "schools" / folder / "index.html").read_text()
    vars_ = extract_root_vars(html)
    p1, p2, acc = pick_palette(vars_, yslug)
    palettes[yslug] = (p1, p2, acc, folder, s["name"], s["zh"])
    print(f"{yslug:18} {p1:9} {p2:9} {acc:9}  ({len(vars_)} vars)")

import json
out = REPO / "scripts/_taihe_pilot_palettes.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({k: {"primary": v[0], "secondary": v[1], "accent": v[2],
                              "folder": v[3], "name": v[4], "zh": v[5]} for k, v in palettes.items()}, indent=2, ensure_ascii=False))
print(f"\nSaved palettes → {out.relative_to(REPO)}")
