#!/usr/bin/env python3
"""Azure Neural Voice clips for Sijhou Junior High's Listening Challenge words.

One mp3 per word and per example sentence, named by a hash of the text, so the
same sentence is never recorded twice and a reworded one gets a new name (safe
to serve with immutable caching).

Pipeline: Azure Speech REST (en-US neural voice) -> ffmpeg (trim silence,
normalise loudness, mono 48kbps) -> learn/audio/, same as tools/gen_audio.py.

    set -a; . ~/.config/changhua/azure-tts.env; set +a
    python3 tools/gen_sijhou_listening_audio.py
    python3 tools/upload_audio_r2.py --dir learn/audio   # REQUIRED to publish

The clips live in R2 only (learn/audio/ is not in git and not in the Pages
artifact) and worker/worker.js serves /learn/audio/<hash>.mp3 from there.
The hash map is written to tools/data/sijhou-listening-audio.json so the page
can reference the files and a rerun can tell what changed.
"""
import hashlib, json, os, pathlib, shutil, subprocess, sys, urllib.request

VOICE = "en-US-JennyNeural"      # same voice as the Guosheng weekly sentences
WORD_RATE = "-15%"               # single words: slow enough to copy
SENTENCE_RATE = "-5%"
OUT_DIR = pathlib.Path("learn/audio")
MAP_FILE = pathlib.Path("tools/data/sijhou-listening-audio.json")

# Issue 01 — "Teacher Morgan Gets a Scooter License" (test taken 2026-10-02).
# Eight words chosen to cover all five questions; the first example of each is
# the line from the recording, the second is campus life at Sijhou.
WORDS = [
    {"w": "license", "zh": "駕照", "pos": "n.", "ipa": "[ˈlaɪsəns]", "q": "Q1 · Q3",
     "ex": [("I have spent most of my time studying for the scooter license test.",
             "我大部分的時間都在準備機車駕照考試。"),
            ("In Taiwan, you must be eighteen to get a scooter license.",
             "在台灣，要滿十八歲才能考機車駕照。")]},
    {"w": "scooter", "zh": "機車", "pos": "n.", "ipa": "[ˈskutɚ]", "q": "Q1",
     "ex": [("At scooter school, we practiced riding scooters.",
             "在駕訓班，我們練習騎機車。"),
            ("Many teachers ride a scooter to Sijhou Junior High every morning.",
             "很多老師每天早上騎機車來溪州國中。")]},
    {"w": "practice", "zh": "練習", "pos": "v.", "ipa": "[ˈpræktɪs]", "q": "—",
     "ex": [("We would practice riding scooters every evening.",
             "我們每天晚上練習騎機車。"),
            ("The basketball team practices on the court after school.",
             "籃球隊放學後在球場練習。")]},
    {"w": "nervous", "zh": "緊張的", "pos": "adj.", "ipa": "[ˈnɝvəs]", "q": "Q2",
     "ex": [("The day of the test, I was a little bit nervous.",
             "考試那天，我有一點點緊張。"),
            ("I feel nervous before the English listening test.",
             "英語聽力測驗前，我會很緊張。")]},
    {"w": "confident", "zh": "有信心的", "pos": "adj.", "ipa": "[ˈkɑnfədənt]", "q": "Q2",
     "ex": [("I was a little bit nervous, but mostly confident.",
             "我有一點點緊張，但更多的是自信。")
            ,("Practice every day, and you will feel confident in English.",
             "每天練習，你對英文就會有信心。")]},
    {"w": "pass", "zh": "通過（考試）", "pos": "v.", "ipa": "[pæs]", "q": "Q3",
     "ex": [("I took the test, and I passed!",
             "我去考試，結果通過了！"),
            ("Study hard, and you will pass the exam.",
             "用功讀書，你就會通過考試。")]},
    {"w": "visit", "zh": "造訪、去玩", "pos": "v.", "ipa": "[ˈvɪzɪt]", "q": "Q4",
     "ex": [("I really want to visit Sun Moon Lake.",
             "我很想去日月潭。"),
            ("American teachers visit Sijhou Junior High every year.",
             "美國老師每年都會來溪州國中。")]},
    {"w": "travel", "zh": "旅行", "pos": "v.", "ipa": "[ˈtrævəl]", "q": "Q5",
     "ex": [("I plan to travel with my friends all across Taiwan.",
             "我打算和朋友們一起環遊台灣。"),
            ("In summer, many students travel with their families.",
             "暑假時，很多學生和家人一起去旅行。")]},
]


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def synth(text: str, rate: str, dest: pathlib.Path) -> None:
    key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION")
    if not key or not region:
        sys.exit("Set AZURE_SPEECH_KEY / AZURE_SPEECH_REGION "
                 "(set -a; . ~/.config/changhua/azure-tts.env; set +a)")
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
            f'<voice name="{VOICE}"><prosody rate="{rate}">{xml_escape(text)}</prosody>'
            f'</voice></speak>')
    req = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": key,
                 "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                 "User-Agent": "changhua-bilingual-tts/1.0"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())


def post(raw: pathlib.Path, out: pathlib.Path) -> None:
    """Trim silence at both ends, normalise loudness, encode mono 48k."""
    trim = ("silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
            "areverse,"
            "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
            "areverse")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
         "-af", f"{trim},loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.15",
         "-ac", "1", "-ar", "44100", "-b:a", "48k", str(out)],
        check=True)


def main() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT_DIR / ".sijhou-raw"
    raw_dir.mkdir(exist_ok=True)

    jobs = []                                   # (text, rate)
    for item in WORDS:
        jobs.append((item["w"], WORD_RATE))
        jobs += [(en, SENTENCE_RATE) for en, _zh in item["ex"]]

    mapping, made = {}, 0
    for i, (text, rate) in enumerate(jobs, 1):
        h = text_hash(text)
        mapping[text] = h
        dest = OUT_DIR / f"{h}.mp3"
        if dest.exists():
            print(f"[{i:>2}/{len(jobs)}] exists {h}  {text[:60]}")
            continue
        raw = raw_dir / f"{h}.raw.mp3"
        synth(text, rate, raw)
        post(raw, dest)
        raw.unlink()
        made += 1
        print(f"[{i:>2}/{len(jobs)}] made   {h}  {dest.stat().st_size:>6,}B  {text[:60]}")

    shutil.rmtree(raw_dir, ignore_errors=True)
    MAP_FILE.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"\n{made} new clip(s), {len(mapping)} total -> {MAP_FILE}")
    print("\n*** The clips are only on this machine. Publish them: ***")
    print("    python3 tools/upload_audio_r2.py --dir learn/audio\n")


if __name__ == "__main__":
    main()
