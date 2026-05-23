"""Fill in missing keyword_zh + sentence_*_zh in wotd.csv.

Translations done manually (Luke trusts Claude's translation quality).
For the 2 all-empty-sentences videos (lobby, CPR), generate plausible
classroom-flavoured example sentences in EN + ZH.
"""
import csv, re
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "wotd.csv"

# keyword (raw, as in CSV — including POS tag) → keyword_zh
KEYWORD_ZH = {
    "QR code": "QR 碼",
    "QR code (n)": "QR 碼",
    "lobby": "大廳",
    "carry (v)": "搬運",
    "serve (v)": "供應",
    "inflate (v)": "充氣",
    "soccer (n)": "足球",
    "sink (n)": "水槽",
    "fitness club (n)": "健身社",
    "goat (n)": "山羊",
    "paper puppet (n)": "紙偶",
    "newspaper (n)": "報紙",
    "tablet (n)": "平板電腦",
    "compost (n)": "堆肥",
    "wipe": "擦拭",
    "wipe (v)": "擦拭",
    "artwork (n)": "藝術作品",
    "card game": "紙牌遊戲",
    "conductor (n)": "指揮",
    "skit (n)": "短劇",
    "costume (n)": "戲服",
    "dancer (n)": "舞者",
    "violin (n)": "小提琴",
    "bulletin board (n)": "公佈欄",
    "badminton (n)": "羽球",
    "water dispenser (n)": "飲水機",
    "origami (n)": "摺紙",
    "measure (v)": "測量",
    "worksheet": "學習單",
    "worksheet (n)": "學習單",
    "iPad (n)": "iPad",
    "professional development (n)": "專業進修",
    "map (n)": "地圖",
    "art project (n)": "美術作品",
    "read aloud competition (n)": "朗讀比賽",
    "pancake (n)": "鬆餅",
    "tour bus (n)": "遊覽車",
    "coach (n)": "教練",
    "magnet (n)": "磁鐵",
    "height (n)": "身高",
    "broom (n)": "掃把",
    "virtual (adj)": "虛擬的",
    "blackboard eraser cleaner (n)": "板擦清潔機",
    "remote control (n)": "遙控器",
    "tear-off calendar (n)": "撕日曆",
    "air conditioner (n)": "冷氣",
    "curtain (n)": "窗簾",
    "textbook (n)": "課本",
    "raise your hand": "舉手",
    "cleaning cloth (n)": "抹布",
    "TV screen": "電視螢幕",
    "laptop (n)": "筆記型電腦",
    "roller-skate": "直排輪",
    "roller-skate (v)": "溜直排輪",
    "long jump": "跳遠",
    "test (n)": "考試",
    "end of the school day": "放學",
    "air quality (n)": "空氣品質",
    "security guard (n)": "警衛",
    "school lunch (n)": "營養午餐",
    "mop (v)": "拖地",
    "award presentation (n)": "頒獎",
    "contest (n)": "比賽",
    "volleyball (n)": "排球",
    "agility ladder (n)": "敏捷梯",
    "marathon (n)": "馬拉松",
    "dance exercise (n)": "韻律舞",
    "anniversary (n)": "週年紀念",
    "calligraphy (n)": "書法",
    "tennis (n)": "網球",
    "rake (v)": "耙",
    "draw (v)": "畫畫",
    "Christmas (n)": "聖誕節",
    "turn on/off": "開關",
    "cleats (n)": "釘鞋",
    "potted plant (n)": "盆栽",
    "seesaw (n)": "蹺蹺板",
    "pitcher (n)": "投手",
    "track team (n)": "田徑隊",
    "baton (n)": "接力棒",
    "Word of the Day shot put (n)": "鉛球",
    "dance (v)": "跳舞",
    "marshmallow (n)": "棉花糖",
    "high jump (n)": "跳高",
    "tug of war (n)": "拔河",
    "put (v)": "放",
    "listen (v)": "聽",
    "climb (v)": "爬",
    "library (n)": "圖書館",
    "swing (v)": "盪鞦韆",
    "Chinese yo-yo (n)": "扯鈴",
    "cross (v)": "跨越",
    "announce (v)": "宣布",
    "pom-pom (n)": "啦啦球",
    "mask (n)": "口罩",
    "spring couplet (n)": "春聯",
    "scan (v)": "掃描",
    "pole (n)": "桿",
    "school anniversary (n)": "校慶",
    "balloon (n)": "氣球",
    "drum (n)": "鼓",
    "hay (n)": "乾草",
    "unicycle (n)": "獨輪車",
    "bake (v)": "烘焙",
    "karate (n)": "空手道",
    "lion dance (n)": "舞獅",
    "sweep (v)": "掃地",
    "scarecrow (n)": "稻草人",
}

# Two videos with no sentences at all in description — fabricate
# classroom-flavoured examples (Luke OK'd "just translate").
ALL_EMPTY_SENTENCES = {
    "Zd78mFEma5w": {  # lobby
        "keyword_zh": "大廳",
        "sentence_1": "Students wait for their parents in the school lobby.",
        "sentence_1_zh": "學生們在學校大廳等家長。",
        "sentence_2": "The lobby is decorated with student artwork.",
        "sentence_2_zh": "大廳上掛著學生們的美術作品。",
    },
    "PeDgndCapnA": {  # CPR (n)
        "keyword_zh": "心肺復甦術",
        "sentence_1": "The students learn how to perform CPR in health class.",
        "sentence_1_zh": "學生們在健康課上學習如何施行心肺復甦術。",
        "sentence_2": "CPR can save someone's life in an emergency.",
        "sentence_2_zh": "心肺復甦術在緊急情況下能救人一命。",
    },
}

# carry (v) appears for both 北斗國中 + 明禮國小 with different sentences —
# need to disambiguate by video_id since base translation differs.
PER_VIDEO_OVERRIDES = {
    # ftdFRP5LeBA | carry (v) | 彰化縣北斗鎮北斗國中
    "ftdFRP5LeBA": {"keyword_zh": "攜帶"},
    # V4OtzTKX_Jg | carry (v) | 彰化縣田中鎮明禮國小
    "V4OtzTKX_Jg": {"keyword_zh": "搬運"},
    # 8ZhGCGJfyho | soccer (n) | 東芳國小  /  fFKsmRWxLCo | soccer (n) | 螺陽國小
    # both 足球; covered by KEYWORD_ZH.
}


def main():
    with CSV_PATH.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        fields = rdr.fieldnames

    kw_patched = 0
    sent_patched = 0
    no_translation = []

    for r in rows:
        vid_m = re.search(r"v=([A-Za-z0-9_-]{11})", r["youtube"])
        vid = vid_m.group(1) if vid_m else ""

        # Fill sentences for the two all-empty videos
        if vid in ALL_EMPTY_SENTENCES:
            payload = ALL_EMPTY_SENTENCES[vid]
            for k, v in payload.items():
                if not r[k].strip():
                    r[k] = v
            sent_patched += 1

        # Per-video override (highest priority)
        if vid in PER_VIDEO_OVERRIDES:
            for k, v in PER_VIDEO_OVERRIDES[vid].items():
                if not r[k].strip():
                    r[k] = v

        # Generic keyword translation
        if not r["keyword_zh"].strip():
            kz = KEYWORD_ZH.get(r["keyword"].strip())
            if kz:
                r["keyword_zh"] = kz
                kw_patched += 1
            else:
                no_translation.append((vid, r["keyword"]))

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"keyword_zh patched: {kw_patched}")
    print(f"sentence rows patched: {sent_patched}")
    if no_translation:
        print(f"\nNo translation found for {len(no_translation)} keyword(s):")
        for vid, kw in no_translation:
            print(f"  {vid} | {kw}")


if __name__ == "__main__":
    main()
