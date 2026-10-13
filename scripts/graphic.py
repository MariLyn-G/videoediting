#!/usr/bin/env python3
"""Make a transparent PNG sticker/card from a template, via headless Chrome.

    python3 graphic.py '{"type": "receipt", "title": "Video editor", "lines": [["1 video", "$150"]]}' -o out.png
    python3 graphic.py spec.json -o out.png

Templates (sizes are designed for a 1080-wide frame):
  tag        title, sub                 dark label, e.g. "CapCut" / "video editor"
  receipt    label, title, lines        paper invoice with a torn edge; lines = [[item, price], ...]
  price      amount, sub                red LED price, e.g. "$750" / "EVERY SINGLE VIDEO"
  note       text, arrow, color         handwritten note with a curved arrow
                                        arrow: up-left, up-right, down-left, down-right, none
  checklist  title, chip, items         white app card with green ticks
  comment    text, placeholder          comment bar with a typed word, e.g. "EDIT"
  stat       value, unit, label         big serif number with a round badge, e.g. 100 / % / edited
  pill       text, icon                 white pill with an emoji/letter icon, e.g. a brand name
  timeline   tracks, playhead           editing-app timeline (colored clips, waveform, playhead)
  windowbar  title, brand, width        title bar of an app window (traffic lights, file name)
tag takes strike: true (red line through it). checklist takes done: N (first N ticked,
the rest grey) so a sequence of cards can tick off one by one. comment takes reply
and reply_name for a reply bubble under the bar.
Every template also takes: rotate (degrees), scale (1.0), color/accent overrides.

Needs Chrome or Chromium. Set CHROME=/path/to/chrome if it isn't found.
"""
import argparse
import glob
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "..", "assets", "fonts"))
CANVAS = 1400

FONT_FACES = {
    "Inter Black": "Inter-Black.ttf", "Inter ExtraBold": "Inter-ExtraBold.ttf",
    "Inter Medium": "Inter-Medium.ttf", "Caveat": "Caveat-Bold.ttf",
    "Plex Mono": "IBMPlexMono-Medium.ttf", "Plex Mono Bold": "IBMPlexMono-Bold.ttf",
    "Instrument Serif": "InstrumentSerif-Regular.ttf",
    "Instrument Serif Italic": "InstrumentSerif-Italic.ttf",
}


def find_chrome():
    cands = [os.environ.get("CHROME", ""),
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    cands += [shutil.which(n) or "" for n in
              ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")]
    cands += sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))
    cands += sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium-*/chrome-linux/chrome")))
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome/Chromium not found; set CHROME=/path/to/chrome")


def e(s):
    return html.escape(str(s))


ARROWS = {
    # path from the text toward the target, drawn in a 160x120 box
    "up-right": ("M10 110 C 40 40, 90 20, 150 15", "150,15", -20),
    "up-left": ("M150 110 C 120 40, 70 20, 10 15", "10,15", 200),
    "down-right": ("M10 10 C 40 80, 90 100, 150 105", "150,105", 20),
    "down-left": ("M150 10 C 120 80, 70 100, 10 105", "10,105", 160),
}


def arrow_svg(kind, color):
    if kind not in ARROWS:
        return ""
    path, tip, ang = ARROWS[kind]
    tx, ty = map(float, tip.split(","))
    return (f'<svg width="160" height="120" viewBox="0 0 160 120" style="overflow:visible">'
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="6" '
            f'stroke-linecap="round"/>'
            f'<g transform="translate({tx},{ty}) rotate({ang})">'
            f'<path d="M0 0 L -22 -12 M0 0 L -22 12" stroke="{color}" stroke-width="6" '
            f'stroke-linecap="round" fill="none"/></g></svg>')


def body(spec):
    t = spec["type"]
    acc = spec.get("accent", "#f3d46a")
    if t == "tag":
        strike = (f'<div style="position:absolute;left:-14px;right:-14px;top:46%;height:9px;'
                  f'background:#e5352b;border-radius:5px;transform:rotate(-7deg);'
                  f'box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>' if spec.get("strike") else "")
        return (f'<div class="card" style="position:relative;background:{spec.get("bg", "#151515")};'
                f'border:2px solid #2c2c2c;border-radius:16px;padding:18px 30px 16px;'
                f'box-shadow:0 14px 30px rgba(0,0,0,.45);text-align:center">'
                f'<div style="font:64px \'Inter Black\';color:#fff;letter-spacing:-1px;'
                f'line-height:1">{e(spec.get("title", ""))}</div>'
                f'<div style="font:24px \'Plex Mono\';color:#b9b9b9;margin-top:8px">'
                f'{e(spec.get("sub", ""))}</div>{strike}</div>')
    if t == "receipt":
        rows = "".join(
            f'<div style="display:flex;align-items:baseline;gap:12px;font:34px \'Plex Mono\';'
            f'color:#222;margin-top:10px"><span>{e(a)}</span>'
            f'<span style="flex:1;border-bottom:3px dotted #9a9a9a;transform:translateY(-8px)">'
            f'</span><span style="font:36px \'Plex Mono Bold\';color:{spec.get("price_color", "#d93a2b")}">'
            f'{e(b)}</span></div>' for a, b in spec.get("lines", []))
        return (f'<div class="card" style="background:#f7f5ef;padding:26px 32px 40px;'
                f'min-width:420px;box-shadow:0 16px 30px rgba(0,0,0,.45);'
                f'-webkit-mask:linear-gradient(#000 0 0) top/100% calc(100% - 18px) no-repeat,'
                f'conic-gradient(from 135deg at top,#0000,#000 1deg 89deg,#0000 90deg) '
                f'bottom/36px 18px repeat-x">'
                f'<div style="font:26px \'Plex Mono\';color:#7d7d7d;letter-spacing:3px">'
                f'{e(spec.get("label", "INVOICE"))}</div>'
                f'<div style="font:52px \'Inter Black\';color:#111;letter-spacing:-1px;'
                f'margin-top:4px">{e(spec.get("title", ""))}</div>'
                f'<div style="border-top:3px dashed #bdbdbd;margin:14px 0 4px"></div>{rows}</div>')
    if t == "price":
        return (f'<div class="card" style="text-align:center">'
                f'<div style="background:#1c1c1c;border-radius:14px;padding:10px 34px;'
                f'box-shadow:0 12px 28px rgba(0,0,0,.5),inset 0 0 0 3px #2d2d2d">'
                f'<div style="font:96px \'Plex Mono Bold\';color:{spec.get("color", "#ff3b30")};'
                f'letter-spacing:6px;text-shadow:0 0 18px {spec.get("color", "#ff3b30")}aa">'
                f'{e(spec.get("amount", ""))}</div></div>'
                + (f'<div style="display:inline-block;background:#e9e6df;color:#222;'
                   f'font:24px \'Plex Mono\';letter-spacing:3px;padding:4px 14px;margin-top:-4px">'
                   f'{e(spec["sub"])}</div>' if spec.get("sub") else "") + '</div>')
    if t == "note":
        color = spec.get("color", acc)
        arrow = spec.get("arrow", "up-right")
        txt = (f'<div style="font:76px \'Caveat\';color:{color};white-space:nowrap;'
               f'text-shadow:0 3px 10px rgba(0,0,0,.55);transform:rotate(-6deg)">'
               f'{e(spec.get("text", ""))}</div>')
        a = arrow_svg(arrow, color)
        if arrow.endswith("left"):
            parts = (a, txt) if arrow.startswith("up") else (a, txt)
            inner = f'<div style="display:flex;align-items:flex-end;gap:4px">{parts[0]}{parts[1]}</div>'
        else:
            inner = f'<div style="display:flex;align-items:flex-end;gap:4px">{txt}{a}</div>'
        if arrow.startswith("down"):
            inner = inner.replace("flex-end", "flex-start")
        return f'<div class="card">{inner}</div>'
    if t == "checklist":
        done = spec.get("done", len(spec.get("items", [])))
        items = "".join(
            f'<div style="display:flex;align-items:center;gap:16px;font:32px \'Inter Medium\';'
            f'color:{"#222" if n < done else "#b5b5b5"};margin-top:14px">'
            f'<span style="width:34px;height:34px;border-radius:50%;box-sizing:border-box;'
            f'background:{"#2f8f4e" if n < done else "transparent"};'
            f'border:{"none" if n < done else "3px solid #cfcfcf"};'
            f'display:inline-flex;align-items:center;justify-content:center;'
            f'color:#fff;font:24px \'Inter Black\'">{"&#10003;" if n < done else ""}</span>'
            f'{e(i)}</div>'
            for n, i in enumerate(spec.get("items", [])))
        chip = (f'<span style="background:#d9534a;color:#fff;font:26px \'Plex Mono\';'
                f'padding:3px 14px;border-radius:999px">{e(spec["chip"])}</span>'
                if spec.get("chip") else "")
        return (f'<div class="card" style="background:#fff;border-radius:22px;padding:24px 34px 28px;'
                f'min-width:440px;box-shadow:0 18px 40px rgba(0,0,0,.35)">'
                f'<div style="display:flex;align-items:center;gap:14px;font:30px \'Inter Medium\';'
                f'color:#666"><span style="color:#d97757;font:36px \'Inter Black\'">&#10033;</span>'
                f'{e(spec.get("title", ""))} {chip}</div>'
                f'<div style="border-top:4px solid #2f8f4e;margin:16px 0 4px;border-radius:2px"></div>'
                f'{items}</div>')
    if t == "comment":
        reply = (f'<div style="margin:16px 0 0 70px;background:#fff;border-radius:22px;'
                 f'padding:14px 22px;display:inline-block;box-shadow:0 10px 24px rgba(0,0,0,.4)">'
                 f'<div style="font:26px \'Inter ExtraBold\';color:#111">'
                 f'{e(spec.get("reply_name", "you"))}</div>'
                 f'<div style="font:30px \'Inter Medium\';color:#333;margin-top:2px">'
                 f'{e(spec["reply"])}</div>'
                 f'<div style="display:inline-block;margin-top:10px;background:{acc};color:#111;'
                 f'font:26px \'Inter ExtraBold\';padding:6px 16px;border-radius:999px">'
                 f'&#128279; {e(spec.get("reply_button", "Open link"))}</div></div>'
                 if spec.get("reply") else "")
        return (f'<div class="card"><div style="display:flex;align-items:center;gap:18px;'
                f'background:rgba(22,22,22,.88);border:4px solid {acc};border-radius:999px;'
                f'padding:14px 18px 14px 16px;min-width:620px;'
                f'box-shadow:0 12px 30px rgba(0,0,0,.45)">'
                f'<span style="width:54px;height:54px;border-radius:50%;background:#d6d6d6;'
                f'display:inline-block"></span>'
                f'<span style="flex:1;font:46px \'Inter Black\';color:{acc}">'
                f'{e(spec.get("text", ""))}</span>'
                f'<span style="width:50px;height:50px;border-radius:50%;background:{acc};'
                f'color:#222;display:inline-flex;align-items:center;justify-content:center;'
                f'font:32px \'Inter Black\'">&#8593;</span></div>{reply}</div>')
    if t == "stat":
        return (f'<div class="card" style="position:relative;padding-right:60px">'
                f'<div style="font:190px \'Instrument Serif\';color:{spec.get("color", "#111")};'
                f'line-height:.9">{e(spec.get("value", ""))}</div>'
                f'<div style="font:60px \'Instrument Serif Italic\';color:{spec.get("color", "#111")};'
                f'margin-top:-6px">{e(spec.get("label", ""))}</div>'
                + (f'<div style="position:absolute;right:0;top:40px;width:96px;height:96px;'
                   f'border-radius:50%;background:#d9534a;color:#fff;display:flex;'
                   f'align-items:center;justify-content:center;font:52px \'Instrument Serif\'">'
                   f'{e(spec["unit"])}</div>' if spec.get("unit") else "") + '</div>')
    if t == "pill":
        return (f'<div class="card" style="display:inline-flex;align-items:center;gap:14px;'
                f'background:#fff;border-radius:999px;padding:12px 30px 12px 14px;'
                f'box-shadow:0 10px 24px rgba(0,0,0,.35)">'
                f'<span style="width:56px;height:56px;border-radius:50%;background:#111;color:#fff;'
                f'display:inline-flex;align-items:center;justify-content:center;'
                f'font:30px \'Inter Black\'">{e(spec.get("icon", (spec.get("text") or "?")[0]))}</span>'
                f'<span style="font:44px \'Inter ExtraBold\';color:#111">{e(spec.get("text", ""))}'
                f'</span></div>')
    if t == "timeline":
        colors = ["#2fb3a0", "#7b6be0", "#d9b24c", "#3aa6d9", "#e07a6b"]
        tracks = spec.get("tracks", 4)
        rows = ""
        import random
        rnd = random.Random(spec.get("seed", 3))
        for r in range(tracks):
            label = ["V2", "V1", "T1", "A1", "A2"][r % 5]
            clips, x = "", 0
            while x < 820:
                w = rnd.randint(90, 230)
                gap = rnd.choice([0, 0, 12, 40])
                c = colors[(r + len(clips)) % len(colors)] if label != "A1" else "#2fb3a0"
                wave = ("background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.35)"
                        " 0 2px,transparent 2px 6px);" if label.startswith("A") else "")
                clips += (f'<div style="position:absolute;left:{x + gap}px;width:{min(w, 820 - x - gap)}px;'
                          f'top:4px;bottom:4px;background:{c};border-radius:8px;{wave}'
                          f'opacity:.92"></div>')
                x += w + gap
            rows += (f'<div style="display:flex;align-items:center;gap:14px;height:52px">'
                     f'<span style="width:44px;font:22px \'Plex Mono\';color:#9aa">{label}</span>'
                     f'<div style="position:relative;width:820px;height:100%">{clips}</div></div>')
        ph = spec.get("playhead", 0.4)
        return (f'<div class="card" style="position:relative;background:rgba(20,22,26,.92);'
                f'border:2px solid #2c3036;border-radius:18px;padding:18px 22px;'
                f'box-shadow:0 18px 40px rgba(0,0,0,.5)">'
                f'<div style="font:20px \'Plex Mono\';color:#7c8590;margin:0 0 8px 58px;'
                f'letter-spacing:2px">00:00&nbsp;&nbsp;&nbsp;&nbsp;00:01&nbsp;&nbsp;&nbsp;&nbsp;'
                f'00:02&nbsp;&nbsp;&nbsp;&nbsp;00:03&nbsp;&nbsp;&nbsp;&nbsp;00:04&nbsp;&nbsp;&nbsp;'
                f'&nbsp;00:05</div>{rows}'
                f'<div style="position:absolute;top:40px;bottom:14px;left:{80 + 820 * ph:.0f}px;'
                f'width:3px;background:#fff"></div></div>')
    if t == "windowbar":
        w = spec.get("width", 640)
        return (f'<div class="card" style="width:{w}px;box-sizing:border-box;background:#fbfaf7;'
                f'border-radius:22px 22px 0 0;padding:14px 22px;display:flex;align-items:center;'
                f'gap:10px;border-bottom:2px solid #e6e2d8">'
                f'<span style="width:16px;height:16px;border-radius:50%;background:#ee6a5f"></span>'
                f'<span style="width:16px;height:16px;border-radius:50%;background:#f5be4f"></span>'
                f'<span style="width:16px;height:16px;border-radius:50%;background:#62c554"></span>'
                f'<span style="flex:1;text-align:center;font:26px \'Plex Mono\';color:#333">'
                f'&#9655; {e(spec.get("title", "reel.mp4"))}</span>'
                f'<span style="font:26px \'Inter ExtraBold\';color:#222">'
                f'<span style="color:#d97757">&#10033;</span> {e(spec.get("brand", "Claude"))}'
                f'</span></div>')
    sys.exit(f"unknown graphic type {t!r}")


def page(spec):
    faces = "".join(f"@font-face{{font-family:'{n}';src:url('file://{os.path.join(FONTS, f)}')}}"
                    for n, f in FONT_FACES.items())
    tr = f"rotate({spec.get('rotate', 0)}deg) scale({spec.get('scale', 1)})"
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{faces}"
            f"html,body{{margin:0;background:transparent}}"
            f"#wrap{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) {tr}}}"
            f"</style></head><body><div id='wrap'>{body(spec)}</div></body></html>")


def trim(png, out, margin=6):
    """Crop a PNG to its non-transparent pixels."""
    import numpy as np
    w = h = CANVAS
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-f", "rawvideo",
                          "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(h, w, 4)[:, :, 3]
    ys, xs = np.nonzero(a > 4)
    if not len(xs):
        sys.exit("graphic rendered empty")
    x0, x1 = max(0, xs.min() - margin), min(w, xs.max() + margin)
    y0, y1 = max(0, ys.min() - margin), min(h, ys.max() + margin)
    cw, ch = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf",
                    f"crop={cw}:{ch}:{x0}:{y0}", out], check=True)
    return cw, ch


def make(spec, out):
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as tmp:
        h = os.path.join(tmp, "g.html")
        open(h, "w", encoding="utf-8").write(page(spec))
        shot = os.path.join(tmp, "g.png")
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--hide-scrollbars", "--default-background-color=00000000",
                        "--force-device-scale-factor=1", f"--window-size={CANVAS},{CANVAS}",
                        "--virtual-time-budget=2000", f"--screenshot={shot}", "file://" + h],
                       capture_output=True, check=True)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        return trim(shot, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="JSON string or path to a .json file")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec)) if os.path.exists(a.spec) else json.loads(a.spec)
    w, h = make(spec, a.out)
    print(f"{a.out} ({w}x{h})")


if __name__ == "__main__":
    main()
