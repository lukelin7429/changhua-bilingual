#!/usr/bin/env python3
"""For each hub-platform school, compare the topbar in its index.html (home)
against the topbar in a sample festival page. Report exact-match status,
mismatched nav items, missing items, and class-name mismatches."""
import re, json
from pathlib import Path
REPO = Path.home() / "Documents/Claude/repos/changhua-bilingual"
PALETTES = json.loads((REPO / "scripts/_taihe_pilot_palettes.json").read_text())

TOPBAR_PATTERNS = [
    r'<nav class="subnav">.*?</nav>',
    r'<div[^>]*class="[^"]*ymj-topbar[^"]*"[^>]*>.*?</div>\s*</div>',
    r'<header[^>]*class="[^"]*ymj-topbar[^"]*"[^>]*>.*?</header>',
    r'<nav class="topbar"[^>]*>.*?</nav>',
    r'<div\s+class="topbar">.*?<nav[^>]*>.*?</nav>\s*</div>\s*</div>',
    r'<div\s+class="topbar"[^>]*>\s*<div class="topbar__inner">.*?</div>\s*</div>',
]

def extract_topbar(html):
    for pat in TOPBAR_PATTERNS:
        m = re.search(pat, html, re.DOTALL)
        if m: return m.group(0)
    nav_matches = re.findall(r'<nav[^>]*>.*?</nav>', html, re.DOTALL)
    for nav in nav_matches:
        if len(re.findall(r'<a[^>]*href="[^"]*"', nav)) >= 3:
            return nav
    return None

def extract_nav_items(topbar):
    """Returns list of (text, href) tuples for each <a> in topbar."""
    items = []
    for m in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', topbar, re.DOTALL):
        href, content = m.group(1), m.group(2)
        text = re.sub(r'<[^>]+>', '', content).strip()
        # Skip brand/logo anchors (usually no text or just image)
        if not text: continue
        items.append((text, href))
    return items

def normalize_class(topbar):
    m = re.search(r'class="([^"]+)"', topbar)
    return m.group(1) if m else ""

def fix_relative(href, folder):
    """Same normalization as wrap script — for comparing apples to apples."""
    if href.startswith(('http://','https://','/','#','mailto:','tel:','javascript:')):
        return href
    if not href.strip() or href in ('./','.'):
        return f'/schools/{folder}/'
    return f"/schools/{folder}/{href.lstrip('./')}"

print(f"{'slug':18} {'class match':12} {'items match':12} {'notes'}")
print("-" * 100)
for slug, meta in PALETTES.items():
    folder = meta["folder"]
    home_html = (REPO / "schools" / folder / "index.html").read_text()
    fest_path = REPO / "schools" / folder / "festivals" / "easter" / "index.html"
    if not fest_path.exists():
        # try other festivals
        for cand in ["chinese-new-year","christmas","new-years-day"]:
            p = REPO / "schools" / folder / "festivals" / cand / "index.html"
            if p.exists():
                fest_path = p; break
    if not fest_path.exists():
        print(f"{slug:18} N/A          N/A          (no wrapped festival page found)"); continue
    fest_html = fest_path.read_text()

    home_topbar = extract_topbar(home_html)
    fest_topbar = extract_topbar(fest_html)
    if not home_topbar:
        print(f"{slug:18} ✗ no home topbar"); continue
    if not fest_topbar:
        print(f"{slug:18} ✗ no festival topbar"); continue

    home_class = normalize_class(home_topbar)
    fest_class = normalize_class(fest_topbar)
    class_ok = home_class == fest_class

    # Compare nav items — apply same URL normalization to home items, and strip is-active from fest items
    home_items = [(t, fix_relative(h, folder)) for t, h in extract_nav_items(home_topbar)]
    fest_items_raw = extract_nav_items(fest_topbar)
    fest_items = [(t, h) for t, h in fest_items_raw if t != 'Home' or h != '/schools/'+folder+'/']  # placeholder, just use as-is

    # Compare: same text+href tuples in same order. But festival pages MAY have an EXTRA Festivals link appended.
    home_set = home_items
    fest_set = fest_items_raw

    notes = []
    if not class_ok:
        notes.append(f"class: home='{home_class}' fest='{fest_class}'")

    # Compare item lists
    if home_set == fest_set:
        items_ok = "✓ exact"
    else:
        items_ok = "✗ differ"
        # Items in home but not in fest (with normalized href)
        missing = [t for t,h in home_set if (t,h) not in fest_set]
        extra = [t for t,h in fest_set if (t,h) not in home_set]
        if missing: notes.append(f"missing in fest: {missing}")
        if extra: notes.append(f"extra in fest: {extra}")

    class_status = "✓" if class_ok else "✗"
    print(f"{slug:18} {class_status:12} {items_ok:12} {'; '.join(notes) if notes else 'OK'}")
