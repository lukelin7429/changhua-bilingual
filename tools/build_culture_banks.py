#!/usr/bin/env python3
"""Split the School Culture bank into the two things the app needs.

The 192 questions are not all the same kind of knowledge, so they are not all
handled the same way:

  drill.json      M1, M2, M8 — offices, calendar, workplace habits. Practical
                  recall, which spaced repetition genuinely helps.
  reference.json  M3-M7 — corporal punishment, mandatory reporting, gender
                  equity, bullying, privacy. Legal and safeguarding content.
                  Deliberately NOT drilled: a teacher's knowledge of the 24-hour
                  reporting duty must not depend on whether the scheduler
                  happened to surface that card this week, and repeated
                  multiple-choice practice breeds a false sense of mastery.
                  These are read through and searched instead.
  terms.json      The offices, roles and legal terms an FET has to recognise on
                  a door or in an email, with pinyin and audio.

Run from the repo root:  python3 tools/build_culture_banks.py
"""
import hashlib, json, pathlib

SRC = pathlib.Path("fets/school-culture/data/practice-bank.json")
OUT = pathlib.Path("culture/data")
DRILL_MODULES = (1, 2, 8)

# Hand-curated: what an FET actually needs to recognise. Auto-extracting the
# Chinese from the options pulls in sentence fragments, so this is written out.
TERMS = [
    # 處室
    ("教務處", "jiàowùchù", "Office of Academic Affairs", "office",
     "Timetables, textbooks, exams, substitute cover. Your teaching schedule lives here."),
    ("學務處", "xuéwùchù", "Office of Student Affairs", "office",
     "Discipline, health, clubs, safety. The office you deal with most outside your own classes."),
    ("總務處", "zǒngwùchù", "Office of General Affairs", "office",
     "Buildings, equipment, repairs, purchasing. Broken air conditioner? Here."),
    ("輔導室", "fǔdǎoshì", "Counselling Office", "office",
     "Student counselling and support. If you are worried about a child, this office and the 導師 are your first stop."),
    ("人事室", "rénshìshì", "Personnel Office", "office",
     "Contract, leave records, insurance, work permit. In your first week, learn who works here."),
    ("會計室", "kuàijìshì", "Accounting Office", "office",
     "Payments and reimbursements. Sometimes called 主計室 and sometimes the same person as 人事室 in a small school."),
    ("健康中心", "jiànkāng zhōngxīn", "Health Centre", "office",
     "The school nurse's room, also called 保健室. Where you send a student who is hurt or unwell."),
    ("校長室", "xiàozhǎngshì", "Principal's Office", "office",
     "Where visitors are received. You will be brought here to meet guests more often than you expect."),
    # 職稱
    ("校長", "xiàozhǎng", "Principal", "role",
     "The head of the school. 副校長 is a deputy, though many primary schools do not have one."),
    ("主任", "zhǔrèn", "Director", "role",
     "Head of one of the 處室 — 教務主任, 學務主任 and so on. Above 組長."),
    ("組長", "zǔzhǎng", "Section head", "role",
     "Runs a section within a 處室. In practice they handle most of the paperwork that reaches you."),
    ("導師", "dǎoshī", "Homeroom teacher", "role",
     "Responsible for one class's daily life. Often shortened to 班導. Your main partner for anything about a specific student."),
    ("教學組長", "jiàoxué zǔzhǎng", "Curriculum section head", "role",
     "Handles timetabling, substitute cover and teaching schedules inside 教務處."),
    ("生教組", "shēngjiàozǔ", "Student discipline section", "role",
     "The section of 學務處 that handles discipline and safety incidents."),
    ("護理師", "hùlǐshī", "School nurse", "role",
     "Staffs the 健康中心. Also referred to by the older word 護士."),
    # 制度與法規
    ("性平會", "xìngpínghuì", "Gender Equity Committee", "system",
     "Short for 性別平等教育委員會. Every school must have one, and it — not you — investigates gender-related incidents."),
    ("性別平等教育法", "xìngbié píngděng jiàoyù fǎ", "Gender Equity Education Act", "system",
     "The law behind 性平會. It sets the duty to report and the timeline schools must follow."),
    ("行事曆", "xíngshìlì", "School calendar", "system",
     "The year's schedule: exams, holidays, make-up days, events. Check it before booking any travel."),
    ("補課日", "bǔkèrì", "Make-up class day", "system",
     "A Saturday worked to bridge a long weekend. It looks like a holiday on the national calendar but is a school day."),
    ("段考", "duànkǎo", "Term exam", "system",
     "The periodic exam, usually two or three a semester. Regular lessons often pause around it."),
    ("校務會議", "xiàowù huìyì", "Whole-school staff meeting", "system",
     "The full staff meeting that approves school-wide decisions. Attendance is normally expected."),
]


def h(zh):
    return hashlib.sha1(zh.encode("utf-8")).hexdigest()[:12]


def main():
    qs = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    mods = {}
    for q in qs:
        mods.setdefault(q["m"], {"m": q["m"], "mt": q["mt"], "mz": q["mz"], "n": 0})["n"] += 1

    drill = [q for q in qs if q["m"] in DRILL_MODULES]
    ref = [q for q in qs if q["m"] not in DRILL_MODULES]

    # One deck per module rather than one big pile — a teacher can pick the
    # thing they actually need this week.
    BLURB = {
        1: ("Who does what, and what your contract and visa depend on.",
            "誰負責什麼，以及你的合約與簽證繫於哪個處室。"),
        2: ("How the year runs — the timetable, the calendar, the make-up days.",
            "一年怎麼運作——作息、行事曆、補課日。"),
        8: ("Co-teaching and the everyday habits of a Taiwanese staffroom.",
            "協同教學，以及台灣辦公室的日常默契。"),
    }
    for m in DRILL_MODULES:
        qs_m = [q for q in drill if q["m"] == m]
        (OUT / f"m{m}.json").write_text(json.dumps({
            "label": mods[m]["mt"], "labelZh": mods[m]["mz"],
            "blurb": BLURB[m][0], "blurbZh": BLURB[m][1],
            "module": m, "questions": qs_m,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    (OUT / "reference.json").write_text(json.dumps({
        "label": "Rules & Safeguarding", "labelZh": "法規與兒少保護",
        "blurb": "Discipline, reporting duties, gender equity, bullying and privacy. Read these through — they are not drilled, because knowing them has to be reliable, not lucky.",
        "blurbZh": "管教、通報義務、性平、霸凌與個資。這幾塊請完整讀過——它們不做每日抽考，因為這種知識必須是可靠的，不能靠剛好被抽到。",
        "modules": [mods[m] for m in sorted(mods) if m not in DRILL_MODULES],
        "questions": ref,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    (OUT / "terms.json").write_text(json.dumps({
        "label": "Names on doors", "labelZh": "門上的名字",
        "blurb": "The offices, roles and terms you have to recognise written down — on a door, in an email, on the calendar.",
        "blurbZh": "你必須看得懂的處室、職稱與制度用語——門牌上、信件裡、行事曆上。",
        "terms": [{"zh": zh, "py": py, "en": en, "kind": kind, "why": why, "audio": h(zh)}
                  for zh, py, en, kind, why in TERMS],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for m in DRILL_MODULES:
        print(f"m{m}.json         {len([q for q in drill if q['m']==m]):3d} questions  {mods[m]['mt']}")
    print(f"reference.json  {len(ref):3d} questions  (M" +
          ", M".join(str(m) for m in sorted(mods) if m not in DRILL_MODULES) + ")")
    print(f"terms.json      {len(TERMS):3d} terms")

    # Which term clips still need generating
    man = json.loads(pathlib.Path("learn/audio-manifest.json").read_text(encoding="utf-8"))
    have = {t[0] for t in TERMS if t[0] in man}
    print(f"\naudio: {len(have)} of {len(TERMS)} already exist; "
          f"{len(TERMS) - len(have)} to generate:")
    for zh, *_ in TERMS:
        if zh not in man:
            print(f"  {zh}  -> {h(zh)}.mp3")


main()
