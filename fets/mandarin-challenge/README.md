# Mandarin Challenge — question bank

Three levels for foreign English teachers, each in its own JSON file under `data/`.
The page (`index.html`) is a shell; all content lives in the banks, so adding
questions never means touching HTML.

The page has two views, switched by the tabs under the level selector:

- **Practice area 練習區** (default) — *every* question in the level laid out
  openly, grouped under the nine meeting-round headings. **Answers are hidden
  until the reader asks for them**: each question has its own "Show answer 看答案"
  button, and a toolbar switch reveals all of them at once. Listening items keep
  their characters covered until revealed. Search (matches Chinese, pinyin and
  English), filter by question type, toggle pinyin.
  This is the main thing FETs use; the quiz is secondary.
- **Quiz 測驗** — practice quiz (random draw, not recorded) or a meeting round
  (fixed 20, identical for everyone, written to the Google Sheet).

## Target size

| Level | Questions | Rounds filled |
|---|---|---|
| `beginner.json` | 180 | M1–M9 |
| `intermediate.json` | 180 | M1–M9 |
| `advanced.json` | 180 | M1–M9 |

180 per level = 9 meeting rounds × 20 questions. Anything added beyond 180
appears in the practice area under "Extra practice 備用題".

Answer distribution is kept exactly even (45 each on A/B/C/D) by
`merge_banks.py`, which rotates each question's options so the correct one lands
on an assigned letter — rotation reorders the options but never changes which is
correct. Advanced carries 54 成語 items (30%).

## Meeting rounds

Round **M*n*** is questions `[(n-1)*20, n*20)` of the bank, in file order —
so **the order of questions in the file is the order of the meeting rounds.**
The practice area uses the same slicing for its round headings; anything past
the ninth round shows under "Extra practice 備用題", and the quiz's round
selector greys out rounds the bank cannot fill yet. While a level is short of
180 questions the practice area prints an explicit note saying which rounds are
still being written — no silent gaps.

Round labels live in `window.__MC_CONFIG__.meetings` in `index.html`
(first meeting September 2026). Change the calendar there, not in the JS.

## Question schema

```json
{
  "id": "B001",
  "type": "word",
  "zh": "老師，我要去廁所",
  "py": "lǎoshī, wǒ yào qù cèsuǒ",
  "q": "A young student urgently says 老師，我要去廁所. They need —",
  "opts": ["a tissue", "the bathroom", "some water", "the school nurse"],
  "ok": 1,
  "why": "廁所 (cèsuǒ) = toilet / restroom. The full sentence 我要去廁所 …"
}
```

- `id` — `B`/`I`/`A` + three digits, unique within the level.
- `type` — `word` · `listen` · `expression` · `dialogue` · `situation` · `measure` · `idiom`.
  `listen` items hide `zh` until the question is graded; the learner only gets the 🔊.
- `zh` — **the full phrase that is spoken and displayed.** It must contain every
  Chinese run that appears in `q`, otherwise the learner sees characters with no
  pinyin beside them. Bare characters inside `q` or `opts` that aren't in `zh`
  need their own inline gloss, e.g. `個 (gè)`.
- `py` — tone-marked pinyin for the whole of `zh`. Hand-written, never auto-generated
  (多音字 make automatic conversion unreliable).
- `ok` — 0-based index of the correct option. **Keep A/B/C/D roughly even across
  each bank** — check before committing (see below).
- `why` — English explanation for a foreign teacher, with the Chinese term and its
  pinyin in parentheses. This is the teaching moment; it is worth more than the question.

## Checks before committing

```bash
python3 - <<'PY'
import json, collections, re
CJK = re.compile(r'[一-鿿][一-鿿，。？！、]*')
for f in ['beginner','intermediate','advanced']:
    d = json.load(open(f'data/{f}.json'))
    qs = d['questions']
    ids = [q['id'] for q in qs]
    assert len(set(ids)) == len(ids), f'duplicate id in {f}'
    for q in qs:
        assert len(q['opts']) == 4 and 0 <= q['ok'] < 4, q['id']
        for k in ('zh','py','q','why','type'):
            assert q.get(k), (q['id'], k)
        for run in CJK.findall(q['q']):
            run = run.strip('，。？！、')
            if run and run not in q['zh'] and f'{run} (' not in q['q']:
                print(f"{q['id']}: {run!r} in stem has no pinyin")
    c = collections.Counter(q['ok'] for q in qs)
    print(f, len(qs), 'ABCD =', [c[i] for i in range(4)])
PY
```

## Scoring pipeline

Practice runs are **not** recorded. Meeting rounds POST to the shared Apps Script
web app (`apps-script/Code.gs`) with `quiz: "fet-mandarin-<level>"`, which writes to
the `mandarin_beginner` / `mandarin_intermediate` / `mandarin_advanced` tabs of the
FET spreadsheet.

**After editing `Code.gs` you must redeploy** (Apps Script → 管理部署 → 編輯 →
版本選新版本 → 部署) or the new tabs will never be created.
