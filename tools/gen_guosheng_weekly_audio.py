#!/usr/bin/env python3
"""Generate Azure Neural Voice clips for Guosheng's Weekly Sentence page."""

import asyncio
import hashlib
import pathlib
import shutil
import subprocess
import sys

VOICE = "en-US-JennyNeural"
RATE = "-10%"
OUT_DIR = pathlib.Path("learn/audio")

PHRASES = (
    "Put the trash in the bin.",
    "Let's throw away the trash.",
    "Let's sort the trash.",
    "Can I turn on the AC or fan?",
    "Can I open the window?",
    "Can I drink some water?",
    "Can I use the iPad?",
    "I can't log in.",
    "Can you help me with this?",
    "I'm excited for vacation.",
    "See you next school year.",
    "I will help at home.",
    "I will learn something new.",
    "trash",
    "bin",
    "throw away",
    "sort",
    "turn on",
    "AC",
    "fan",
    "open",
    "window",
    "drink",
    "water",
    "use",
    "iPad",
    "can't",
    "log in",
    "help",
    "this",
    "excited",
    "vacation",
    "see you",
    "school year",
    "home",
    "learn",
    "something new",
)


def phrase_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def post_process(raw: pathlib.Path, output: pathlib.Path) -> None:
    filters = (
        "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
        "areverse,"
        "silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,"
        "areverse,loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.15"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
            "-af", filters, "-ac", "1", "-ar", "44100", "-b:a", "48k",
            str(output),
        ],
        check=True,
    )


async def main() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT_DIR / ".guosheng-weekly-raw"
    raw_dir.mkdir(exist_ok=True)

    for index, phrase in enumerate(PHRASES, 1):
        stem = phrase_hash(phrase)
        output = OUT_DIR / f"{stem}.mp3"
        if output.exists():
            print(f"[{index:>2}/{len(PHRASES)}] exists {stem}  {phrase}")
            continue

        raw = raw_dir / f"{stem}.mp3"
        subprocess.run(
            [
                "edge-tts", "--voice", VOICE, "--rate", RATE,
                "--text", phrase, "--write-media", str(raw),
            ],
            check=True,
        )
        post_process(raw, output)
        raw.unlink()
        print(f"[{index:>2}/{len(PHRASES)}] made   {stem}  {phrase}")

    raw_dir.rmdir()
    print(f"\n{len(PHRASES)} Azure clips ready in {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
