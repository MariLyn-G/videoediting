#!/usr/bin/env python3
"""Word-level transcript of a talking-head clip.

    python3 transcribe.py talk.mp4 -o work/words.json [--model small.en] [--lang en]

Writes [{"w": "word", "start": 1.23, "end": 1.51}, ...] in source time.
Needs `pip install faster-whisper` and network access to Hugging Face on
first run (the model is cached afterwards).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--lang", default=None, help="e.g. en, hy, ru; default autodetect")
    a = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed: pip install faster-whisper")

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-ac", "1",
                        "-ar", "16000", wav], check=True)
        model = WhisperModel(a.model, device="auto", compute_type="int8")
        segs, info = model.transcribe(wav, word_timestamps=True, language=a.lang,
                                      vad_filter=True)
        words = []
        for s in segs:
            for w in s.words or []:
                t = w.word.strip()
                if t:
                    words.append({"w": t, "start": round(w.start, 3), "end": round(w.end, 3)})

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(words, f, indent=0, ensure_ascii=False)
    print(f"{len(words)} words, language={info.language} -> {a.out}")


if __name__ == "__main__":
    main()
