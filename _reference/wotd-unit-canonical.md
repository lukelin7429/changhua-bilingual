# WOTD Unit Page — Canonical Reference

**Single source of truth for any school's Word-of-the-Day unit page.**

## ⚠️ READ THIS FIRST

Don't author a WOTD page from scratch. Don't extend from memory. **Copy 大莊 (`schools/dajuang/lessons/word/unit-1/`) and swap content**.

Track record of regressions when this rule was ignored:
- 豐洲 (fces) — emoji buttons replacing video; English-only examples
- 萬來 (wanlai) — Web Speech buttons; single example sentence
- 泰和 (taihe) — inverted grid (outer 1-col, inner 2-col head|video)

Each time Luke had to escalate. Each time the fix was "look at 大莊 and copy".

## The non-negotiables

### Outer container `.vocabs` (note plural -s)

```css
.vocabs{
  display:grid;
  grid-template-columns:1fr;
  gap:32px;
  margin:40px 0 30px;
}
@media (min-width:880px){
  .vocabs{
    grid-template-columns:repeat(2,1fr);  /* TWO CARDS PER ROW */
    gap:36px;
  }
}
```

### Inner card `.vc` (stacked, not gridded)

```css
.vc{
  background:#fff;
  border:1px solid var(--line);
  border-radius:20px;
  box-shadow:var(--shadow-sm);
  overflow:hidden;
  display:flex;           /* NOT grid */
  flex-direction:column;  /* head → video → body, top to bottom */
}
```

### Card sections (the three sacred parts)

1. `.vc__head` — `.vc__num` (Word 01) + `.vc__term` + `.vc__pos` (italic, smaller) + `.vc__zh`
2. `.vc__video` — YouTube iframe ALWAYS visible inline, 16:9 via padding-bottom trick
3. `.vc__body > .vc__exs > .vc__ex × 2` — each `.vc__ex` has `.en` (with `<b>` keyword) AND `.zh`

```css
.vc__video{
  position:relative;
  width:100%;
  padding-bottom:56.25%;
  background:#000;
}
.vc__video iframe{
  position:absolute;
  top:0; left:0;
  width:100%;
  height:100%;
  border:0;
  display:block;
}
```

### HTML skeleton

```html
<div class="vocabs">
  <article class="vc">
    <div class="vc__head">
      <div class="vc__num">Word 01</div>
      <div class="vc__term">term <span class="vc__pos">(pos)</span></div>
      <div class="vc__zh">中文</div>
    </div>
    <div class="vc__video">
      <iframe src="https://www.youtube-nocookie.com/embed/<id>?rel=0" ...></iframe>
    </div>
    <div class="vc__body">
      <div class="vc__exs">
        <div class="vc__ex">
          <div class="en">English sentence with <b>term</b>.</div>
          <span class="zh">中文翻譯。</span>
        </div>
        <div class="vc__ex">
          <div class="en">Second English sentence.</div>
          <span class="zh">第二句中文翻譯。</span>
        </div>
      </div>
    </div>
  </article>
  <!-- next .vc card... -->
</div>
```

## Forbidden patterns

- ❌ `<button>🔊 Say it</button>` or any Web Speech / click-to-play UI
- ❌ `target="_blank"` on video links (must be inline iframe)
- ❌ Single example sentence
- ❌ English-only examples (no `.zh`)
- ❌ Outer container as `flex` column
- ❌ Inner `.vc` as grid with `grid-template-columns: 1fr 1fr` (head left, video right)

## Verification gate

Before pushing any new/modified WOTD page:

1. **CSS diff against 大莊** — paste output proving you ran:
   ```bash
   diff <(grep -A2 '\.vocabs\|\.vc[\s_]' schools/dajuang/lessons/word/unit-1/index.html) \
        <(grep -A2 '\.vocabs\|\.vc[\s_]' schools/<new-school>/lessons/word/unit-1/index.html)
   ```

2. **Chrome screenshot** — at viewport ≥1080px, take a screenshot of the wrapped WOTD page that shows:
   - Two cards visible side-by-side (proves outer 2-col)
   - Each card's video iframe visible inline (proves no buttons / no new-tab)
   - At least one `.vc__ex` showing both `.en` and `.zh` text

Skip either step → expect another escalation from Luke. There has been a pattern.

## See also

- Memory: `reference_dajuang_wotd_category_design.md` (also lists the regression history)
- WOTD data pipeline: `project_wotd_pipeline` memory
- Designer baseline: `feedback_school_site_typography`
