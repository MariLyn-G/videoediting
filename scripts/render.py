#!/usr/bin/env python3
"""Render a reel from an edit file. See references/edit-format.md.

    python3 render.py edit.json [--work work/render] [--preview]

--preview renders at 540x960 with a fast preset for a quick look.
Paths inside edit.json are relative to the edit file's folder.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "..", "assets", "fonts"))
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Layout geometry as fractions of the frame (measured from the reference reel).
SPLIT_CARD_H = 0.46      # presenter card height in split layout
SPLIT_MEDIA_BOX = (0.86, 0.40, 0.25)  # media box w, h, center y
FULL_MEDIA_BOX = (0.90, 0.50, 0.40)
CAPTION_Y = {"talk": 0.68, "split": 0.495, "full": 0.70, "broll": 0.68, "card": 0.70}
DEFAULT_CAPTION = {"talk": "sans", "split": "sans", "full": "serif", "broll": "serif",
                   "card": "none"}
PUNCH_IN = 1.15
POP = "\\fscx86\\fscy86\\t(0,90,\\fscx100\\fscy100)"  # caption pop-in


def run(cmd, quiet=True):
    if quiet:
        cmd = [cmd[0], "-hide_banner", "-v", "error"] + cmd[1:]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit("ffmpeg failed: " + " ".join(cmd))


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def hex_rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def is_light(c):
    r, g, b = hex_rgb(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 140


def ass_color(c, alpha=0):
    r, g, b = hex_rgb(c)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def ass_time(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_text(s):
    return s.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", "\\N")


class Reel:
    def __init__(self, edit_path, work, preview):
        self.base = os.path.dirname(os.path.abspath(edit_path))
        self.e = json.load(open(edit_path))
        self.work = work
        self.W, self.H = self.e.get("size", [1080, 1920])
        if preview:
            self.W, self.H = self.W // 2, self.H // 2
        self.fps = self.e.get("fps", 30)
        self.preview = preview
        self.x264 = ["-c:v", "libx264", "-preset", "ultrafast" if preview else "medium",
                     "-crf", "23" if preview else "17", "-pix_fmt", "yuv420p"]
        self.face_y = self.e.get("face_y", 0.35)
        cut = json.load(open(self.path(self.e["cut"])))
        self.keep, self.words = cut["keep"], cut["words"]
        self.duration = sum(e - s for s, e in self.keep)

    def path(self, p):
        return p if os.path.isabs(p) else os.path.join(self.base, p)

    # ---- step 1: trimmed, reframed presenter track -------------------------------
    def build_aroll(self):
        out = os.path.join(self.work, "aroll.mp4")
        parts, labels = [], []
        for i, (s, e) in enumerate(self.keep):
            d = e - s
            fd = min(0.012, d / 4)
            parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];"
                         f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d={fd},afade=t=out:st={d - fd:.4f}:d={fd}[a{i}];")
            labels.append(f"[v{i}][a{i}]")
        fc = "".join(parts) + "".join(labels) + f"concat=n={len(self.keep)}:v=1:a=1[cv][ca];" \
            f"[cv]fps={self.fps},scale={self.W}:{self.H}:force_original_aspect_ratio=increase," \
            f"crop={self.W}:{self.H},setsar=1[v]"
        script = os.path.join(self.work, "aroll.filter")
        open(script, "w").write(fc)
        run(["ffmpeg", "-y", "-i", self.path(self.e["source"]),
             "-filter_complex_script", script, "-map", "[v]", "-map", "[ca]",
             *self.x264, "-c:a", "pcm_s16le", out.replace(".mp4", ".mov")])
        self.aroll = out.replace(".mp4", ".mov")

    # ---- step 2: one clip per shot -----------------------------------------------
    def shots(self):
        shots, t, talk_n = [], 0.0, 0
        raw = self.e["shots"]
        for i, s in enumerate(raw):
            s = dict(s)
            end = s.get("end")
            end = self.duration if end is None or i == len(raw) - 1 else min(end, self.duration)
            if end - t < 1.0 / self.fps:
                print(f"warning: shot {i} ({s.get('layout')}) has no length, skipped")
                continue
            s["start"], s["end"] = t, end
            s.setdefault("layout", "talk")
            if s["layout"] == "talk" and "zoom" not in s:
                s["zoom"] = 1.0 if talk_n % 2 == 0 else PUNCH_IN
            if s["layout"] == "talk":
                talk_n += 1
            s.setdefault("caption", DEFAULT_CAPTION[s["layout"]])
            s.setdefault("bg", "#0d1117" if s["layout"] == "broll" else "#ffffff")
            shots.append(s)
            t = end
        if self.duration - t > 1.0 / self.fps:
            shots.append({"layout": "talk", "start": t, "end": self.duration, "zoom": 1.0,
                          "caption": "sans", "bg": "#ffffff"})
        return shots

    def card_mask(self):
        out = os.path.join(self.work, "card_mask.png")
        ch = int(self.H * SPLIT_CARD_H) // 2 * 2
        r, f = int(self.W * 0.045), int(self.H * 0.035)
        corner = (f"if(lt(X,{r})*lt(Y,{r}),clip({r}-hypot(X-{r},Y-{r})+0.5,0,1),"
                  f"if(gt(X,W-{r})*lt(Y,{r}),clip({r}-hypot(X-(W-{r}),Y-{r})+0.5,0,1),1))")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s={self.W}x{ch}",
             "-vf", f"format=gray,geq=lum='255*{corner}*clip(Y/{f},0,1)'",
             "-frames:v", "1", out])
        return out, ch

    def media_input(self, s, dur):
        m = self.path(s["media"])
        if os.path.splitext(m)[1].lower() in IMAGE_EXT:
            return ["-loop", "1", "-framerate", str(self.fps), "-t", f"{dur:.3f}", "-i", m]
        return ["-stream_loop", "-1", "-ss", str(s.get("media_start", 0)),
                "-t", f"{dur:.3f}", "-i", m]

    def fit_media(self, s, box_w, box_h):
        anim = s.get("anim", "pop")
        f = (f"[1:v]fps={self.fps},scale={box_w}:{box_h}:force_original_aspect_ratio=decrease,"
             "format=rgba")
        if anim == "pop":
            f += (",scale=w='trunc(iw*(0.86+0.14*min(1,t/0.22)))':h=-1:eval=frame,"
                  "fade=t=in:st=0:d=0.12:alpha=1")
        return f + "[m];"

    def render_shot(self, i, s):
        W, H, fps = self.W, self.H, self.fps
        f0 = round(s["start"] * fps)
        frames = round(s["end"] * fps) - f0
        dur = frames / fps
        out = os.path.join(self.work, f"shot_{i:03d}.mp4")
        inputs = ["-ss", f"{f0 / fps:.4f}", "-t", f"{dur + 0.1:.3f}", "-i", self.aroll]
        lay = s["layout"]
        bg = f"color=c={s['bg']}:s={W}x{H}:r={fps}:d={dur + 0.1:.3f}"

        if lay == "talk":
            z = s.get("zoom", 1.0)
            fc = (f"[0:v]scale=trunc(iw*{z}/2)*2:-2,"
                  f"crop={W}:{H}:(iw-ow)/2:(ih-oh)*{self.face_y}[v]")
        elif lay == "split":
            bw, bh, cy = SPLIT_MEDIA_BOX
            ch = self.mask_h
            # Card shows the presenter from just above the head down.
            top = f"max(0,min(ih-{ch},ih*{self.face_y}-{ch}*0.45))"
            fc = f"{bg}[bg];"
            if s.get("media"):
                inputs += self.media_input(s, dur + 0.1)
                fc += self.fit_media(s, int(W * bw), int(H * bh))
                fc += f"[bg][m]overlay=x=(W-w)/2:y={int(H * cy)}-h/2:shortest=1[bg2];"
            else:
                fc += "[bg]null[bg2];"
            inputs += ["-loop", "1", "-i", self.mask]
            mi = 2 if s.get("media") else 1
            fc += (f"[0:v]crop={W}:{ch}:0:'{top}',format=rgba[card];"
                   f"[{mi}:v]format=gray,scale={W}:{ch}[mask];"
                   f"[card][mask]alphamerge[cardA];"
                   f"[bg2][cardA]overlay=0:{H - ch}:shortest=1[v]")
        elif lay == "full":
            bw, bh, cy = FULL_MEDIA_BOX
            inputs += self.media_input(s, dur + 0.1)
            fc = (f"{bg}[bg];" + self.fit_media(s, int(W * bw), int(H * bh)) +
                  f"[bg][m]overlay=x=(W-w)/2:y={int(H * cy)}-h/2:shortest=1[v]")
        elif lay == "broll":
            inputs += self.media_input(s, dur + 0.1)
            dim = s.get("dim", 0.0)
            fc = (f"[1:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H},setsar=1")
            fc += f",drawbox=t=fill:c=black@{dim}[v]" if dim else "[v]"
        elif lay == "card":
            fc = f"{bg}[v]"
        else:
            sys.exit(f"unknown layout {lay!r}")

        run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]",
             "-frames:v", str(frames), "-r", str(fps), *self.x264, "-an", out])
        return out

    # ---- step 3: captions as ASS ---------------------------------------------------
    def chunks(self, shots):
        cap = self.e.get("captions", {})
        max_words, max_chars = cap.get("max_words", 2), cap.get("max_chars", 14)
        hide = [(c["start"], c.get("end", self.duration)) for c in self.ctas()]
        out = []

        def shot_at(t):
            for s in shots:
                if s["start"] <= t < s["end"]:
                    return s
            return shots[-1]

        cur = []
        for w in self.words:
            if any(a <= w["start"] < b for a, b in hide):
                continue
            if cur:
                text = " ".join(x["w"] for x in cur + [w])
                if (len(cur) >= max_words or len(text) > max_chars
                        or w["start"] - cur[-1]["end"] > 0.25
                        or cur[-1]["w"][-1:] in ".,!?;:"
                        or shot_at(w["start"]) is not shot_at(cur[0]["start"])):
                    out.append(cur)
                    cur = []
            cur.append(w)
        if cur:
            out.append(cur)

        res = []
        for i, c in enumerate(out):
            start = c[0]["start"]
            nxt = out[i + 1][0]["start"] if i + 1 < len(out) else self.duration
            end = min(nxt, c[-1]["end"] + 0.35)
            s = shot_at(start)
            end = min(end, s["end"])
            text = " ".join(x["w"] for x in c)
            res.append((start, end, text, s))
        return res

    def ctas(self):
        c = self.e.get("cta")
        return [c] if isinstance(c, dict) else (c or [])

    def write_ass(self, shots):
        W, H = self.W, self.H
        k = H / 1920
        sans = int(78 * k)
        serif = int(128 * k)
        fonts = self.e.get("fonts", {})
        f_sans = fonts.get("sans", "Inter ExtraBold")
        f_heavy = fonts.get("heavy", "Inter Black")
        f_serif = fonts.get("serif", "Instrument Serif")
        styles = [
            # name, font, size, bold, italic, primary, back, outline, shadow
            ("Sans", f_sans, sans, 0, 0, "#ffffff", 0x70, 0, 2.5 * k),
            ("SansDark", f_sans, sans, 0, 0, "#111111", 0xFF, 0, 0),
            ("Serif", f_serif, serif, 0, 1, "#ffffff", 0x80, 0, 2 * k),
            ("SerifDark", f_serif, serif, 0, 1, "#111111", 0xFF, 0, 0),
            ("CardTitle", f_heavy, int(190 * k), 0, 0, "#111111", 0xFF, 0, 0),
            ("CardSub", f_sans, int(64 * k), 0, 0, "#6b6b6b", 0xFF, 0, 0),
            ("CtaSmall", f_serif, int(96 * k), 0, 1, "#ffffff", 0x80, 0, 2 * k),
            ("CtaBig", f_heavy, int(150 * k), 0, 0, "#ffffff", 0xFF, 0, 0),
        ]
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
                 "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                 "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
                 "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
                 "MarginR, MarginV, Encoding"]
        for n, font, size, b, it, col, back, ol, sh in styles:
            lines.append(f"Style: {n},{font},{size},{ass_color(col)},{ass_color(col)},"
                         f"&H00000000,&H{back:02X}000000,{b},{-1 if it else 0},0,0,100,100,0,0,1,"
                         f"{ol},{sh:.1f},5,40,40,0,1")
        lines += ["", "[Events]",
                  "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

        def ev(start, end, style, x, y, text, layer=1, tags=""):
            lines.append(f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style},,0,0,0,,"
                         f"{{\\an5\\pos({x},{y}){tags}}}{text}")

        for start, end, text, s in self.chunks(shots):
            mode = s["caption"]
            if mode == "none" or s.get("text") is not None:
                continue
            on_light = s["layout"] in ("split", "full", "card") and is_light(s["bg"])
            y = int(H * CAPTION_Y[s["layout"]])
            if mode == "serif":
                ev(start, end, "SerifDark" if on_light else "Serif", W // 2, y,
                   ass_text(text.upper()), tags=POP)
            else:
                ev(start, end, "SansDark" if on_light else "Sans", W // 2, y,
                   ass_text(text), tags=POP)

        for s in shots:
            light = is_light(s["bg"])
            if s.get("text") is not None:
                y = int(H * CAPTION_Y[s["layout"]])
                on_light = s["layout"] in ("split", "full", "card") and light
                st = ("SerifDark" if on_light else "Serif") if s["caption"] == "serif" \
                    else ("SansDark" if on_light else "Sans")
                t = s["text"].upper() if s["caption"] == "serif" else s["text"]
                ev(s["start"], s["end"], st, W // 2, y, ass_text(t), tags=POP)
            if s["layout"] == "card":
                col = "" if light else "\\c&HFFFFFF&"
                title = s.get("title", "")
                # Shrink long titles so they stay on one line (Inter Black averages ~0.58em per char).
                size = min(int(190 * k), int(W * 0.88 / max(1, len(title)) / 0.58))
                ev(s["start"], s["end"], "CardTitle", W // 2, int(H * 0.44),
                   ass_text(title), tags=POP + col + f"\\fs{size}")
                if s.get("sub"):
                    ev(s["start"], s["end"], "CardSub", W // 2, int(H * 0.44) + size,
                       ass_text(s["sub"]), tags=col)

        for c in self.ctas():
            st, en = c["start"], c.get("end", self.duration)
            r, g, b = hex_rgb(c.get("glow", "#ff7a1a"))
            glow = f"&H{b:02X}{g:02X}{r:02X}&"
            y = int(H * c.get("y", 0.66))
            ev(st, en, "CtaSmall", W // 2, y - int(110 * k), ass_text(c.get("small", "")), tags=POP)
            big = ass_text(c.get("big", ""))
            glow_tags = f"\\1a&HFF&\\bord{int(14 * k)}\\blur{int(18 * k)}\\3c{glow}"
            ev(st, en, "CtaBig", W // 2, y, big, layer=1, tags=POP + glow_tags)
            ev(st, en, "CtaBig", W // 2, y, big, layer=2,
               tags=POP + f"\\bord{int(3 * k)}\\blur{int(4 * k)}\\3c{glow}")

        out = os.path.join(self.work, "captions.ass")
        open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        return out

    # ---- step 4: assemble ------------------------------------------------------------
    def assemble(self, clips, ass):
        lst = os.path.join(self.work, "clips.txt")
        open(lst, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
        out = self.path(self.e.get("output", "reel.mp4"))
        if self.preview:
            out = out.replace(".mp4", "_preview.mp4")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

        inputs = ["-f", "concat", "-safe", "0", "-i", lst, "-i", self.aroll]
        afc = "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[voice];"
        mix = ["[voice]"]
        n = 2
        music = self.e.get("music")
        if music:
            inputs += ["-stream_loop", "-1", "-i", self.path(music["file"])]
            afc += (f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                    f"atrim=0:{self.duration:.3f},volume={music.get('volume', 0.12)},"
                    f"afade=t=out:st={max(0, self.duration - 1.5):.3f}:d=1.5[mus];")
            if music.get("duck", True):
                afc = afc.replace("[voice];", "[voice0];") + \
                    "[voice0]asplit[voice][vkey];[mus][vkey]sidechaincompress=" \
                    "threshold=0.03:ratio=6:attack=20:release=300[musd];"
                mix.append("[musd]")
            else:
                mix.append("[mus]")
            n += 1
        for j, fx in enumerate(self.e.get("sfx", [])):
            inputs += ["-i", self.path(fx["file"])]
            ms = int(fx["at"] * 1000)
            afc += (f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                    f"volume={fx.get('volume', 0.5)},adelay={ms}|{ms}[fx{j}];")
            mix.append(f"[fx{j}]")
            n += 1
        lufs = self.e.get("loudness", -14)
        if len(mix) > 1:
            afc += "".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0,"
        else:
            afc += "[voice]"
        afc += f"loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000[a]"

        esc = lambda p: p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        fonts_dir = self.e.get("fonts", {}).get("dir")
        fonts_dir = self.path(fonts_dir) if fonts_dir else FONTS
        vfc = f"[0:v]ass='{esc(ass)}':fontsdir='{esc(fonts_dir)}'[v]"
        run(["ffmpeg", "-y", *inputs, "-filter_complex", vfc + ";" + afc,
             "-map", "[v]", "-map", "[a]", *self.x264, "-r", str(self.fps),
             "-c:a", "aac", "-b:a", "192k", "-t", f"{self.duration:.3f}",
             "-movflags", "+faststart", out])
        return out

    def render(self):
        os.makedirs(self.work, exist_ok=True)
        print("1/4 trimming presenter track")
        self.build_aroll()
        shots = self.shots()
        self.mask, self.mask_h = self.card_mask()
        print(f"2/4 rendering {len(shots)} shots")
        clips = [self.render_shot(i, s) for i, s in enumerate(shots)]
        print("3/4 captions")
        ass = self.write_ass(shots)
        print("4/4 assembling")
        out = self.assemble(clips, ass)
        print(f"done: {out}  ({probe_duration(out):.2f}s)")
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("--work", default=None)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    work = a.work or os.path.join(os.path.dirname(os.path.abspath(a.edit)), "work", "render")
    Reel(a.edit, work, a.preview).render()


if __name__ == "__main__":
    main()
