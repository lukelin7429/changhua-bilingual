#!/usr/bin/env python3
"""Strip the over-the-top emoji wiggle from .pillar__icon site-wide.

Removes two patterns from each schools/*/style.css:
  1. `.pillar:hover .pillar__icon{transform:scale(1.18) rotate(-7deg);}` (the wiggle)
  2. `;transition:transform .28s cubic-bezier(.2,.7,.2,1)` inside `.pillar__icon{...}`
     (orphan transition left behind once the hover animation is gone)

The card itself (.pillar:hover) keeps its lift / colour-shadow — only the
icon's scale+rotate animation is removed. Run from anywhere; auto-locates repo.
"""
import re
from pathlib import Path

REPO = Path.home() / "Documents/Claude/repos/changhua-bilingual"
sheets = sorted((REPO / "schools").glob("*/style.css"))

RE_HOVER = re.compile(
    r'\.pillar:hover\s+\.pillar__icon\{transform:scale\(1\.18\)\s+rotate\(-7deg\);?\}\s*\n?'
)
RE_TRANS = re.compile(
    r';transition:transform\s+\.28s\s+cubic-bezier\(\.2,\.7,\.2,1\)'
)

changed = []
for f in sheets:
    text = f.read_text()
    orig = text
    text = RE_HOVER.sub('', text)
    text = RE_TRANS.sub('', text)
    if text != orig:
        f.write_text(text)
        changed.append(f.relative_to(REPO))

print(f"Stripped emoji wiggle from {len(changed)} stylesheets:")
for c in changed:
    print(f"  ✓ {c}")
