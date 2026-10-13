#!/usr/bin/env python3
"""Render a reel from an edit file. See references/edit-format.md.

    python3 render.py edit.json [--work work/render] [--preview]

--preview renders at 540x960 with a fast preset for a quick look.
Paths inside edit.json are relative to the edit file's folder.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphic as graphic_mod  # noqa: E402
import looks as looks_mod  # noqa: E402
import sfx as sfx_mod  # noqa: E402

FONTS = os.path.normpath(os.path.join(HERE, "..", "assets", "fonts"))
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Layout geometry as fractions of the frame (measured from the reference reels).
SPLIT_CARD_H = 0.46      # presenter card height in split layout
SPLIT_MEDIA_BOX = (0.86, 0.40, 0.25)  # media box w, h, center y
FULL_MEDIA_BOX = (0.90, 0.50, 0.40)
CAPTION_Y = {"split": 0.495, "full": 0.70, "card": 0.70}
GRAPHIC_LAYOUTS = {"split", "full", "broll", "card"}
PERSON_LAYOUTS = {"talk", "cutout"}
PUNCH_IN = 1.15
POP = "\\fscx86\\fscy86\\t(0,90,\\fscx100\\fscy100)"


def run(cmd):
    r = subprocess.run([cmd[0], "-hide_banner", "-v", "error"] + cmd[1:])
    if r.returncode:
        sys.exit("ffmpeg failed: " + " ".join(cmd))


def probe(path, entries="format=duration"):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", entries, "-of", "json", path],
                         capture_output=True, text=True).stdout
    return json.loads(out)


def hex_rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def is_light(c):
    r, g, b = hex_rgb(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 140


def ass_color(c, alpha=0):
    r, g, b = hex_rgb(c)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def tag_color(c):
    r, g, b = hex_rgb(c)
    return f"&H{b:02X}{g:02X}{r:02X}&"


def ass_time(t):
    cs = int(round(max(0.0, t) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_text(s):
    return s.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def norm(w):
    return w.lower().strip(".,!?;:\"'“”‘’")


def find_phrase(words, phrases):
    """(start, end) index of the longest emphasized phrase inside `words`, or None."""
    lw = [norm(w) for w in words]
    best = None
    for p in phrases:
        pw = [norm(x) for x in p.split()]
        n = len(pw)
        for i in range(len(lw) - n + 1):
            if lw[i:i + n] == pw and (best is None or n > best[1] - best[0]):
                best = (i, i + n)
    return best


def esc_filter_path(p):
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def rounded_rect(w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} "
            f"{w - r} {h} l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0")


def circle(d):
    r = d / 2
    k = 0.5523 * r
    return (f"m {r} 0 b {r + k} 0 {d} {r - k} {d} {r} b {d} {r + k} {r + k} {d} {r} {d} "
            f"b {r - k} {d} 0 {r + k} 0 {r} b 0 {r - k} {r - k} 0 {r} 0")


class Ass:
    """Builds one .ass file from look styles."""

    def __init__(self, W, H, styles):
        self.W, self.H, self.k = W, H, H / 1920
        self.styles = styles
        self.events = []

    def header(self):
        k = self.k
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {self.W}",
                 f"PlayResY: {self.H}", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
                 "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                 "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
                 "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
                 "MarginR, MarginV, Encoding"]
        for name, s in self.styles.items():
            box = s.get("box")
            if box:
                border, outline, oc = 3, s.get("pad", 12) * k, ass_color(box)
            else:
                border, outline = 1, s.get("outline", 0) * k
                oc = ass_color(s.get("outline_color", "#000000"))
            lines.append(
                f"Style: {name},{s['font']},{int(s['size'] * k)},{ass_color(s['color'])},"
                f"{ass_color(s['color'])},{oc},&H70000000,0,{-1 if s.get('italic') else 0},"
                f"0,0,100,100,{s.get('spacing', 0) * k:.1f},0,{border},{outline:.1f},"
                f"{s.get('shadow', 0) * k:.1f},5,40,40,0,1")
        return lines + ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, "
                                        "MarginR, MarginV, Effect, Text"]

    def raw(self, start, end, style, tags, text, layer=1):
        if end - start <= 0.005:
            return
        self.events.append(f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style},,"
                           f"0,0,0,,{{{tags}}}{text}")

    def text(self, start, end, style, x, y, text, tags="", layer=1, raw=False):
        """Text centered at (x, y) pixels, with a glow layer if the style has one.

        raw=True means `text` is already escaped ASS (may contain override tags)."""
        s = self.styles[style]
        if raw or "{" in text:
            t = text
        else:
            if s.get("upper"):
                text = text.upper()
            elif s.get("lower"):
                text = text.lower()
            t = ass_text(text)
        pos = f"\\an5\\pos({int(x)},{int(y)})"
        if s.get("glow"):
            g = int(10 * self.k)
            self.raw(start, end, style, pos + tags + f"\\1a&HFF&\\bord{g}\\blur{g * 1.4:.0f}"
                     f"\\3c{tag_color(s['glow'])}\\3a&H60&\\shad0", t, layer)
        self.raw(start, end, style, pos + tags, t, layer + 1)

    def write(self, path):
        open(path, "w", encoding="utf-8").write("\n".join(self.header() + self.events) + "\n")
        return path


class Reel:
    def __init__(self, edit_path, work, preview):
        self.base = os.path.dirname(os.path.abspath(edit_path))
        self.e = json.load(open(edit_path))
        self.work = work
        self.W, self.H = self.e.get("size", [1080, 1920])
        if preview:
            self.W, self.H = self.W // 2, self.H // 2
        self.k = self.H / 1920
        self.fps = self.e.get("fps", 30)
        self.preview = preview
        self.x264 = ["-c:v", "libx264", "-preset", "ultrafast" if preview else "medium",
                     "-crf", "23" if preview else "17", "-pix_fmt", "yuv420p"]
        self.face_y = self.e.get("face_y", 0.35)
        self.look_name = self.e.get("look", "explainer")
        self.look, self.styles = looks_mod.resolve(self.look_name, self.e.get("styles"))
        self.cap = dict(self.look["captions"])
        self.cap.update(self.e.get("captions", {}))
        cut = json.load(open(self.path(self.e["cut"])))
        self.keep, self.words = cut["keep"], cut["words"]
        self.duration = sum(e - s for s, e in self.keep)
        fonts_dir = self.e.get("fonts", {}).get("dir")
        self.fonts_dir = self.path(fonts_dir) if fonts_dir else FONTS
        self._mask_cache = {}
        self._typing = []
        self._graphics = {}
        self._size_cache = {}

    def path(self, p):
        return p if os.path.isabs(p) else os.path.join(self.base, p)

    def _cached(self, name, key):
        """True if work/<name> exists and was built from the same inputs."""
        out = os.path.join(self.work, name)
        kf = out + ".key"
        h = hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest()
        if os.path.exists(out) and os.path.exists(kf) and open(kf).read() == h:
            return out, True, kf, h
        return out, False, kf, h

    # ---- step 1: trimmed, reframed, graded presenter track (+ person matte) ---------
    def build_aroll(self):
        grade = self.e.get("grade", self.look["grade"])
        key = [os.path.abspath(self.path(self.e["source"])), self.keep, self.W, self.H,
               self.fps, grade, self.preview]
        out, hit, kf, h = self._cached("aroll.mov", key)
        self.aroll, self.aroll_key = out, h
        if hit:
            print("   (reusing trimmed track)")
            return
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
            f"crop={self.W}:{self.H},setsar=1" + (f",{grade}" if grade else "") + "[v]"
        script = os.path.join(self.work, "aroll.filter")
        open(script, "w").write(fc)
        run(["ffmpeg", "-y", "-i", self.path(self.e["source"]),
             "-filter_complex_script", script, "-map", "[v]", "-map", "[ca]",
             *self.x264, "-c:a", "pcm_s16le", out])
        open(kf, "w").write(h)

    def build_matte(self):
        model = self.e.get("matte_model", "multiclass")
        out, hit, kf, h = self._cached("matte.mp4", [self.aroll_key, model])
        self.matte = out
        if hit:
            print("   (reusing person matte)")
            return
        r = subprocess.run([sys.executable, os.path.join(HERE, "matte.py"), self.aroll,
                            "-o", out, "--model", model], stderr=subprocess.DEVNULL)
        if r.returncode:
            sys.exit("person matte failed (pip install mediapipe numpy)")
        open(kf, "w").write(h)

    # ---- plan normalization ----------------------------------------------------------
    def shots(self):
        shots, t, talk_n = [], 0.0, 0
        raw = self.e["shots"]
        legacy = {"sans": "main", "serif": "alt"}
        for i, s in enumerate(raw):
            s = dict(s)
            end = s.get("end")
            end = self.duration if end is None or i == len(raw) - 1 else min(end, self.duration)
            if end - t < 1.0 / self.fps:
                print(f"warning: shot {i} ({s.get('layout')}) has no length, skipped")
                continue
            s["start"], s["end"] = t, end
            s.setdefault("layout", "talk")
            lay = s["layout"]
            if lay in PERSON_LAYOUTS:
                if "zoom" not in s:
                    s["zoom"] = 1.0 if talk_n % 2 == 0 else PUNCH_IN
                talk_n += 1
            if lay == "card":
                default_cap = "none"
            elif lay in ("full", "broll"):
                default_cap = self.look["graphic_caption"]
            else:
                default_cap = "main"
            s["caption"] = legacy.get(s.get("caption"), s.get("caption", default_cap))
            if lay == "broll":
                s.setdefault("bg", "#0d1117")
            elif lay == "cutout":
                s.setdefault("bg", self.look["brand"])
            else:
                s.setdefault("bg", "#ffffff")
            shots.append(s)
            t = end
        if self.duration - t > 1.0 / self.fps:
            shots.append({"layout": "talk", "start": t, "end": self.duration, "zoom": 1.0,
                          "caption": "main", "bg": "#ffffff"})
        return shots

    def graphic(self, spec):
        """Render a graphic spec to a PNG once; returns (path, width, height)."""
        h = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]
        if h not in self._graphics:
            out = os.path.join(self.work, "graphics", f"{spec.get('type', 'g')}_{h}.png")
            if os.path.exists(out):
                w, hh = self.media_size(out)
            else:
                w, hh = graphic_mod.make(spec, out)
            self._graphics[h] = (out, w, hh)
        return self._graphics[h]

    def overlays(self):
        out = []
        for o in self.e.get("overlays", []):
            o = dict(o)
            if "graphic" in o:
                path, gw, _ = self.graphic(o["graphic"])
                o["media"] = path
                o.setdefault("w", gw / 1080 * o.get("scale", 1.0))
                o.setdefault("radius", 0)
                o.setdefault("shadow", False)
            o.setdefault("start", 0.0)
            if o.get("end") is None:
                o["end"] = self.duration
            if "media" in o and "type" not in o:
                o["type"] = "media"
            o.setdefault("type", "text")
            o.setdefault("z", "front")
            if o["type"] == "prompt":
                o["z"] = "front"
            out.append(o)
        return out

    # ---- step 2: one clip per shot -----------------------------------------------
    def card_mask(self):
        ch = int(self.H * SPLIT_CARD_H) // 2 * 2
        r, f = int(self.W * 0.045), int(self.H * 0.035)
        return self.mask(self.W, ch, r, feather_top=f), ch

    def mask(self, w, h, r, feather_top=0):
        key = (w, h, r, feather_top)
        if key in self._mask_cache:
            return self._mask_cache[key]
        out = os.path.join(self.work, f"mask_{w}x{h}_{r}_{feather_top}.png")
        corner = (f"if(lt(X,{r})*lt(Y,{r}),clip({r}-hypot(X-{r},Y-{r})+0.5,0,1),"
                  f"if(gt(X,W-{r})*lt(Y,{r}),clip({r}-hypot(X-(W-{r}),Y-{r})+0.5,0,1),"
                  f"if(lt(X,{r})*gt(Y,H-{r}),clip({r}-hypot(X-{r},Y-(H-{r}))+0.5,0,1),"
                  f"if(gt(X,W-{r})*gt(Y,H-{r}),clip({r}-hypot(X-(W-{r}),Y-(H-{r}))+0.5,0,1),"
                  f"1))))")
        if feather_top:  # split card: only top corners rounded, soft top edge
            corner = (f"if(lt(X,{r})*lt(Y,{r}),clip({r}-hypot(X-{r},Y-{r})+0.5,0,1),"
                      f"if(gt(X,W-{r})*lt(Y,{r}),clip({r}-hypot(X-(W-{r}),Y-{r})+0.5,0,1),1))"
                      f"*clip(Y/{feather_top},0,1)")
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s={w}x{h}",
             "-vf", f"format=gray,geq=lum='255*{corner}'", "-frames:v", "1", out])
        self._mask_cache[key] = out
        return out

    def media_size(self, m):
        if m not in self._size_cache:
            s = probe(m, "stream=width,height")["streams"][0]
            self._size_cache[m] = (s["width"], s["height"])
        return self._size_cache[m]

    def media_input(self, m, dur, start=0.0):
        if os.path.splitext(m)[1].lower() in IMAGE_EXT:
            return ["-loop", "1", "-framerate", str(self.fps), "-t", f"{dur:.3f}", "-i", m]
        return ["-stream_loop", "-1", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", m]

    def fit_media(self, idx, s, box_w, box_h):
        f = (f"[{idx}:v]fps={self.fps},scale={box_w}:{box_h}:force_original_aspect_ratio="
             "decrease,format=rgba")
        if s.get("anim", "pop") == "pop":
            f += (",scale=w='trunc(iw*(0.86+0.14*min(1,t/0.22)))':h=-1:eval=frame,"
                  "fade=t=in:st=0:d=0.12:alpha=1")
        return f + "[m];"

    def zoomcrop(self, label_in, label_out, z):
        W, H = self.W, self.H
        return (f"[{label_in}]scale=trunc(iw*{z}/2)*2:-2,"
                f"crop={W}:{H}:(iw-ow)/2:(ih-oh)*{self.face_y}[{label_out}];")

    def overlay_chain(self, o, s, dur, idx, mask_idx, base, out_label):
        """Filter that overlays one media overlay `o` on [base] within shot `s`."""
        W, H = self.W, self.H
        a = o["start"] - s["start"]
        b = o["end"] - s["start"]
        m = self.path(o["media"])
        iw, ih = self.media_size(m)
        wpx = int(W * o.get("w", 0.4)) // 2 * 2
        hpx = int(wpx * ih / iw) // 2 * 2
        x, y = W * o.get("x", 0.5), H * o.get("y", 0.3)
        anim = o.get("anim", "pop")
        L = f"o{idx}"
        f = f"[{idx}:v]fps={self.fps},scale={wpx}:{hpx},format=rgba"
        if a > 0 and not os.path.splitext(m)[1].lower() in IMAGE_EXT:
            f += f",setpts=PTS+{a:.3f}/TB"
        f += f"[{L}a];"
        cur = f"{L}a"
        if mask_idx is not None:
            f += (f"[{mask_idx}:v]format=gray,scale={wpx}:{hpx}[{L}k];"
                  f"[{cur}][{L}k]alphamerge[{L}b];")
            cur = f"{L}b"
        post = []
        if anim == "pop":
            post.append(f"scale=w='trunc({wpx}*(0.86+0.14*min(1,max(0,(t-{a:.3f})/0.22)))/2)*2'"
                        f":h=-2:eval=frame")
        if anim in ("pop", "fade", "slide") and a >= 0:
            post.append(f"fade=t=in:st={a:.3f}:d=0.15:alpha=1")
        if b < dur:
            post.append(f"fade=t=out:st={max(0, b - 0.12):.3f}:d=0.12:alpha=1")
        if post:
            f += f"[{cur}]" + ",".join(post) + f"[{L}c];"
            cur = f"{L}c"
        dy = f"+{int(90 * self.k)}*(1-min(1,max(0,(t-{a:.3f})/0.25)))" if anim == "slide" else ""
        enable = f"enable='between(t,{a:.3f},{b:.3f})'"
        if o.get("shadow", self.look_name == "floating"):
            f += (f"[{cur}]split[{L}d][{L}s];[{L}s]colorchannelmixer=rr=0:gg=0:bb=0:"
                  f"aa=0.4,gblur=sigma={14 * self.k:.1f}[{L}t];"
                  f"[{base}][{L}t]overlay=x='{x:.0f}-w/2':y='{y + 14 * self.k:.0f}-h/2{dy}'"
                  f":{enable}[{L}u];")
            base, cur = f"{L}u", f"{L}d"
        f += (f"[{base}][{cur}]overlay=x='{x:.0f}-w/2':y='{y:.0f}-h/2{dy}':{enable}"
              f"[{out_label}];")
        return f

    def render_shot(self, i, s, overlays):
        W, H, fps = self.W, self.H, self.fps
        f0 = round(s["start"] * fps)
        frames = round(s["end"] * fps) - f0
        dur = frames / fps
        pad = dur + 0.1
        out = os.path.join(self.work, f"shot_{i:03d}.mp4")
        inputs = ["-ss", f"{f0 / fps:.4f}", "-t", f"{pad:.3f}", "-i", self.aroll]
        n_in = 1
        lay = s["layout"]
        bg = f"color=c={s['bg'] if s['bg'] != 'blur' else '#000000'}:s={W}x{H}:r={fps}:d={pad:.3f}"

        def add_input(args):
            nonlocal n_in
            inputs.extend(args)
            n_in += 1
            return n_in - 1

        mine = [o for o in overlays if o["type"] == "media"
                and o["start"] < s["end"] and o["end"] > s["start"]]
        behind_media = [o for o in mine if o["z"] == "behind" and lay in PERSON_LAYOUTS]
        front_media = [o for o in mine if o not in behind_media]
        behind_ass = self.shot_behind_ass(i, s, overlays) if lay in PERSON_LAYOUTS else None
        need_person = lay == "cutout" or behind_media or behind_ass

        fc = ""
        if lay in PERSON_LAYOUTS:
            z = s.get("zoom", 1.0)
            fc += "[0:v]split=2[a0][a1];" + self.zoomcrop("a0", "pz", z)
            if lay == "cutout" and s["bg"] == "blur":
                fc += f"[a1]scale=trunc(iw*{z}/2)*2:-2,crop={W}:{H},gblur=sigma={40 * self.k:.0f}," \
                      "eq=brightness=0.03:saturation=0.9[base];"
            elif lay == "cutout":
                fc += f"[a1]nullsink;{bg}[base];"
            else:
                fc += "[a1]nullsink;[pz]split=2[pz][base];"
            cur = "base"
            for j, o in enumerate(behind_media):
                mi = add_input(self.media_input(self.path(o["media"]), pad,
                                                o.get("media_start", 0) +
                                                max(0.0, s["start"] - o["start"])))
                ki = add_input(["-loop", "1", "-i", self.mask(
                    *self._media_px(o), int(o.get("radius", 28) * self.k))]) \
                    if o.get("radius", 28) else None
                fc += self.overlay_chain(o, s, dur, mi, ki, cur, f"bm{j}")
                cur = f"bm{j}"
            if behind_ass:
                fc += f"[{cur}]ass='{esc_filter_path(behind_ass)}':" \
                      f"fontsdir='{esc_filter_path(self.fonts_dir)}'[bt];"
                cur = "bt"
            if need_person:
                mt = add_input(["-ss", f"{f0 / fps:.4f}", "-t", f"{pad:.3f}", "-i", self.matte])
                fc += f"[{mt}:v]format=gray," + self.zoomcrop_inline(z) + "[mz];"
                fc += f"[pz]format=rgba[pzr];[pzr][mz]alphamerge[person];" \
                      f"[{cur}][person]overlay=0:0:shortest=1[v0];"
            else:
                fc += f"[{cur}]null[v0];[pz]nullsink;"
        elif lay == "split":
            bw, bh, cy = SPLIT_MEDIA_BOX
            ch = self.mask_h
            top = f"max(0,min(ih-{ch},ih*{self.face_y}-{ch}*0.45))"
            fc += f"{bg}[bg];"
            if s.get("media"):
                mi = add_input(self.media_input(self.path(s["media"]), pad,
                                                s.get("media_start", 0)))
                fc += self.fit_media(mi, s, int(W * bw), int(H * bh))
                fc += f"[bg][m]overlay=x=(W-w)/2:y={int(H * cy)}-h/2:shortest=1[bg2];"
            else:
                fc += "[bg]null[bg2];"
            ki = add_input(["-loop", "1", "-i", self.card])
            fc += (f"[0:v]crop={W}:{ch}:0:'{top}',format=rgba[card];"
                   f"[{ki}:v]format=gray,scale={W}:{ch}[mask];"
                   f"[card][mask]alphamerge[cardA];"
                   f"[bg2][cardA]overlay=0:{H - ch}:shortest=1[v0];")
        elif lay == "full":
            bw, bh, cy = FULL_MEDIA_BOX
            mi = add_input(self.media_input(self.path(s["media"]), pad, s.get("media_start", 0)))
            fc += (f"{bg}[bg];" + self.fit_media(mi, s, int(W * bw), int(H * bh)) +
                   f"[bg][m]overlay=x=(W-w)/2:y={int(H * cy)}-h/2:shortest=1[v0];")
        elif lay == "broll":
            mi = add_input(self.media_input(self.path(s["media"]), pad, s.get("media_start", 0)))
            dim = s.get("dim", 0.0)
            fc += (f"[{mi}:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,"
                   f"crop={W}:{H},setsar=1")
            fc += f",drawbox=t=fill:c=black@{dim}[v0];" if dim else "[v0];"
        elif lay == "card":
            fc += f"{bg}[v0];"
        else:
            sys.exit(f"unknown layout {lay!r}")
        if lay not in PERSON_LAYOUTS:
            fc = "[0:v]nullsink;" + fc if "[0:v]" not in fc else fc

        cur = "v0"
        for j, o in enumerate(front_media):
            mi = add_input(self.media_input(self.path(o["media"]), pad,
                                            o.get("media_start", 0) +
                                            max(0.0, s["start"] - o["start"])))
            ki = add_input(["-loop", "1", "-i", self.mask(
                *self._media_px(o), int(o.get("radius", 28) * self.k))]) \
                if o.get("radius", 28) else None
            fc += self.overlay_chain(o, s, dur, mi, ki, cur, f"fm{j}")
            cur = f"fm{j}"
        fc += f"[{cur}]null[v]"

        script = os.path.join(self.work, f"shot_{i:03d}.filter")
        open(script, "w").write(fc)
        run(["ffmpeg", "-y", *inputs, "-filter_complex_script", script, "-map", "[v]",
             "-frames:v", str(frames), "-r", str(fps), *self.x264, "-an", out])
        return out

    def zoomcrop_inline(self, z):
        return (f"scale=trunc(iw*{z}/2)*2:-2,"
                f"crop={self.W}:{self.H}:(iw-ow)/2:(ih-oh)*{self.face_y}")

    def _media_px(self, o):
        iw, ih = self.media_size(self.path(o["media"]))
        wpx = int(self.W * o.get("w", 0.4)) // 2 * 2
        return wpx, int(wpx * ih / iw) // 2 * 2

    # ---- step 3: text ------------------------------------------------------------
    def text_overlay(self, ass, o, t0=0.0):
        """Add a text-like overlay to `ass`, with times shifted by -t0."""
        W, H, k = self.W, self.H, self.k
        st, en = o["start"] - t0, o["end"] - t0
        typ = o["type"]
        if typ == "header":
            l1, l2 = (o.get("lines", []) + ["", ""])[:2]
            y = H * o.get("y", 0.075)
            ass.text(st, en, "header1", W / 2, y, l1, tags="\\fad(150,0)")
            ass.text(st, en, "header2", W / 2, y + 92 * k, l2, tags="\\fad(150,0)")
            return
        if typ == "prompt":
            self.prompt_box(ass, o, st, en)
            return
        style = o.get("style", {"chip": "chip", "note": "note"}.get(typ, "title"))
        x, y = W * o.get("x", 0.5), H * o.get("y", {"chip": 0.15, "note": 0.08}.get(typ, 0.2))
        tags = ""
        if "size" in o:
            tags += f"\\fs{int(o['size'] * k)}"
        if "color" in o:
            tags += f"\\c{tag_color(o['color'])}"
        anim = o.get("anim", "pop")
        text = o.get("text", "")
        if "\n" in text:
            # One event per line so stacked titles sit tight (ASS line spacing is loose).
            lines = text.split("\n")
            size = o.get("size", self.styles[style]["size"])
            lead = size * o.get("leading", 0.86) / 1920  # sizes are in 1920-high pixels
            per_char = 0.0
            if anim == "type":
                per_char = min(0.06, max(0.02, (en - st) * 0.5 / max(1, len(text))))
            done = 0
            for i, line in enumerate(lines):
                sub = dict(o, text=line, style=style,
                           y=o.get("y", 0.2) + (i - (len(lines) - 1) / 2) * lead,
                           start=o["start"] + done * per_char)
                done += len(line)
                self.text_overlay(ass, sub, t0)
            return
        if anim == "type":
            chars = list(text.upper() if self.styles[style].get("upper") else text)
            step = min(0.06, max(0.02, (en - st) * 0.5 / max(1, len(chars))))
            for n in range(1, len(chars) + 1):
                ts = st + (n - 1) * step
                te = st + n * step if n < len(chars) else en
                shown = "".join(chars[:n])
                hidden = "".join(chars[n:])
                body = ass_text(shown) + ("{\\alpha&HFF&}" + ass_text(hidden) if hidden else "")
                ass.text(ts, te, style, x, y, body, tags=tags, raw=True)
            return
        if anim == "pop":
            tags = POP + tags
        elif anim == "fade":
            tags += "\\fad(150,100)"
        elif anim == "slide":
            tags += f"\\move({int(x)},{int(y + 60 * k)},{int(x)},{int(y)},0,220)\\fad(120,0)"
        ass.text(st, en, style, x, y, text, tags=tags)

    def prompt_box(self, ass, o, st, en):
        """A chat input card at the top with the prompt typed in, like reference 1."""
        W, H, k = self.W, self.H, self.k
        bw, bh = W * o.get("w", 0.86), 120 * k
        x0, y0 = (W - bw) / 2, H * o.get("y", 0.06)
        box_c = o.get("box", "#f4f1ea")
        accent = o.get("accent", self.look["brand"] if self.look_name == "editorial"
                       else "#1c1c1c")
        ass.raw(st, en, "ui", f"\\an7\\pos({x0:.0f},{y0:.0f})\\p1\\bord0\\shad0\\fad(120,80)"
                f"\\c{tag_color(box_c)}", rounded_rect(bw, bh, 26 * k) + "{\\p0}", layer=5)
        d = 64 * k
        ass.raw(st, en, "ui", f"\\an7\\pos({x0 + bw - d - 26 * k:.0f},{y0 + (bh - d) / 2:.0f})"
                f"\\p1\\bord0\\shad0\\fad(120,80)\\c{tag_color(accent)}", circle(d) + "{\\p0}",
                layer=6)
        ass.raw(st, en, "ui", f"\\an5\\pos({x0 + bw - d / 2 - 26 * k:.0f},{y0 + bh / 2:.0f})"
                f"\\c&HFFFFFF&\\bord0\\shad0\\fs{int(38 * k)}\\fad(120,80)", "↑", layer=7)
        label = o.get("label", "")
        if label:
            ass.raw(st, en, "ui_label", f"\\an7\\pos({x0 + 30 * k:.0f},{y0 + 18 * k:.0f})"
                    f"\\bord0\\shad0\\fad(120,80)", ass_text(label.upper()), layer=7)
        text = o.get("text", "")
        cps = o.get("cps", 26)
        ty = y0 + (bh * 0.62 if label else bh / 2)
        n = len(text)
        t = st + 0.25
        for i in range(1, n + 1):
            te = t + 1 / cps if i < n else en
            cursor = "|" if i < n or int((te - t) * 2) % 2 == 0 else ""
            ass.raw(t, te, "ui", f"\\an4\\pos({x0 + 30 * k:.0f},{ty:.0f})\\bord0\\shad0",
                    ass_text(text[:i]) + cursor, layer=7)
            t = te
        self._typing.append((st + 0.25, n, cps))

    def shot_behind_ass(self, i, s, overlays):
        items = [o for o in overlays if o["type"] != "media" and o["z"] == "behind"
                 and o["start"] < s["end"] and o["end"] > s["start"]]
        if not items:
            return None
        ass = Ass(self.W, self.H, self.styles)
        for o in items:
            self.text_overlay(ass, o, t0=s["start"])
        return ass.write(os.path.join(self.work, f"behind_{i:03d}.ass"))

    def chunks(self, shots):
        cap = self.cap
        max_words, max_chars = cap.get("max_words", 2), cap.get("max_chars", 14)
        hide = [(c["start"], c.get("end", self.duration)) for c in self.ctas()]
        hide += [(o["start"], o["end"]) for o in self.overlays() if o.get("hide_captions")]

        def shot_at(t):
            for s in shots:
                if s["start"] <= t < s["end"]:
                    return s
            return shots[-1]

        bigrams = set()
        for p in cap.get("emphasis", []):
            ws = [norm(x) for x in p.split()]
            bigrams.update(zip(ws, ws[1:]))
        groups, cur = [], []
        for w in self.words:
            if any(a <= w["start"] < b for a, b in hide):
                continue
            if cur:
                text = " ".join(x["w"] for x in cur + [w])
                inside_phrase = (norm(cur[-1]["w"]), norm(w["w"])) in bigrams
                if not inside_phrase and (len(cur) >= max_words or len(text) > max_chars
                        or w["start"] - cur[-1]["end"] > 0.25
                        or cur[-1]["w"][-1:] in ".,!?;:"
                        or shot_at(w["start"]) is not shot_at(cur[0]["start"])):
                    groups.append(cur)
                    cur = []
            cur.append(w)
        if cur:
            groups.append(cur)
        res = []
        for i, c in enumerate(groups):
            nxt = groups[i + 1][0]["start"] if i + 1 < len(groups) else self.duration
            s = shot_at(c[0]["start"])
            end = min(nxt, c[-1]["end"] + 0.35, s["end"])
            res.append((c, end, s))
        return res

    def ctas(self):
        c = self.e.get("cta")
        return [c] if isinstance(c, dict) else (c or [])

    def captions(self, ass, shots):
        W, H = self.W, self.H
        mode = self.cap.get("mode", "pop")
        emph = {w.lower().strip(".,!?") for p in self.cap.get("emphasis", []) for w in p.split()}
        accent = self.cap.get("accent", self.look["accent"])
        dim = self.cap.get("dim", "#9a9a9a")
        for group, end, s in self.chunks(shots):
            if s["caption"] == "none" or s.get("text") is not None:
                continue
            style = "cap_alt" if s["caption"] == "alt" else "cap_main"
            st = self.styles[style]
            lay = s["layout"]
            y = H * (self.cap.get("y", 0.68) if lay in PERSON_LAYOUTS | {"broll"}
                     else CAPTION_Y[lay])
            light_bg = lay in ("split", "full", "card") and is_light(s["bg"]) and not st.get("box")
            base = "\\shad0\\c" + tag_color("#111111") if light_bg else ""
            words = [w["w"] for w in group]
            if st.get("upper"):
                words = [w.upper() for w in words]

            def colored(i_spoken):
                parts = []
                for j, w in enumerate(words):
                    if mode == "karaoke" and j > i_spoken:
                        parts.append("{\\c" + tag_color(dim) + "}" + ass_text(w))
                    elif w.lower().strip(".,!?") in emph:
                        parts.append("{\\c" + tag_color(accent) + "}" + ass_text(w) +
                                     "{\\c" + (tag_color("#111111") if light_bg
                                               else tag_color(st["color"])) + "}")
                    else:
                        parts.append(ass_text(w))
                return " ".join(parts)

            start = group[0]["start"]
            if mode == "punch":
                k = self.k
                sm = self.styles[style]["size"]
                big = self.styles["cap_emph"]["size"]
                gap = (big * 0.47 + sm * 0.55) * k
                ph = find_phrase(words, self.cap.get("emphasis", []))
                if ph is None:
                    ass.text(start, end, style, W / 2, y, " ".join(words), tags=POP + base)
                    continue
                before, mid, after = words[:ph[0]], words[ph[0]:ph[1]], words[ph[1]:]
                if before:
                    ass.text(start, end, style, W / 2, y - gap, " ".join(before),
                             tags=POP + base)
                t_mid = group[ph[0]]["start"]
                ass.text(t_mid, end, "cap_emph", W / 2, y, " ".join(mid), tags=POP)
                if after:
                    ass.text(group[ph[1]]["start"], end, style, W / 2, y + gap,
                             " ".join(after), tags=POP + base)
                continue
            if mode == "karaoke":
                for j, w in enumerate(group):
                    ts = start if j == 0 else w["start"]
                    te = group[j + 1]["start"] if j + 1 < len(group) else end
                    ass.text(ts, te, style, W / 2, y, colored(j), tags=base)
            elif mode == "phrase":
                ass.text(start, end, style, W / 2, y, colored(len(words)),
                         tags=base + "\\fad(90,0)")
            else:
                ass.text(start, end, style, W / 2, y, colored(len(words)), tags=POP + base)

    def write_ass(self, shots, overlays):
        W, H, k = self.W, self.H, self.k
        ass = Ass(W, H, self.styles)
        self.captions(ass, shots)
        for s in shots:
            if s.get("text") is not None:
                style = "cap_alt" if s["caption"] == "alt" else "cap_main"
                y = H * (self.cap.get("y", 0.68) if s["layout"] in PERSON_LAYOUTS | {"broll"}
                         else CAPTION_Y[s["layout"]])
                dark = (s["layout"] in ("split", "full", "card") and is_light(s["bg"])
                        and not self.styles[style].get("box"))
                ass.text(s["start"], s["end"], style, W / 2, y, s["text"],
                         tags=POP + ("\\shad0\\c" + tag_color("#111111") if dark else ""))
            if s["layout"] == "card":
                light = is_light(s["bg"])
                col = "" if light else "\\c&HFFFFFF&"
                title = s.get("title", "")
                size = min(int(190 * k), int(W * 0.88 / max(1, len(title)) / 0.58))
                ass.text(s["start"], s["end"], "card_title", W / 2, H * 0.44, title,
                         tags=POP + col + f"\\fs{size}")
                if s.get("sub"):
                    ass.text(s["start"], s["end"], "card_sub", W / 2, H * 0.44 + size,
                             s["sub"], tags=col)
        for o in overlays:
            if o["type"] == "media":
                continue
            if o["z"] == "behind" and self._shot_type_at(shots, o["start"]) in PERSON_LAYOUTS:
                continue  # drawn under the presenter in render_shot
            self.text_overlay(ass, o)
        for c in self.ctas():
            st, en = c["start"], c.get("end", self.duration)
            y = H * c.get("y", 0.66)
            small, big = self.styles["cta_small"], self.styles["cta_big"]
            ass.text(st, en, "cta_small", W / 2, y - (big["size"] * 0.55 + small["size"] * 0.45)
                     * k, c.get("small", ""), tags=POP)
            glow = c.get("glow", big.get("glow"))
            if not glow and self.look_name == "explainer":
                glow = "#ff7a1a"
            if glow:
                g = int(14 * k)
                ass.raw(st, en, "cta_big", f"\\an5\\pos({W // 2},{int(y)}){POP}\\1a&HFF&"
                        f"\\bord{g}\\blur{int(18 * k)}\\3c{tag_color(glow)}",
                        ass_text(c.get("big", "")), layer=3)
                ass.raw(st, en, "cta_big", f"\\an5\\pos({W // 2},{int(y)}){POP}"
                        f"\\bord{int(3 * k)}\\blur{int(4 * k)}\\3c{tag_color(glow)}",
                        ass_text(c.get("big", "")), layer=4)
            else:
                ass.text(st, en, "cta_big", W / 2, y, c.get("big", ""), tags=POP, layer=3)
        return ass.write(os.path.join(self.work, "captions.ass"))

    @staticmethod
    def _shot_type_at(shots, t):
        for s in shots:
            if s["start"] <= t < s["end"]:
                return s["layout"]
        return shots[-1]["layout"]

    # ---- step 4: sound effects ---------------------------------------------------------
    def sfx_events(self, shots, overlays):
        ev = []
        auto = self.e.get("sfx_auto", True)
        if auto:
            for a, b in zip(shots, shots[1:]):
                if a["layout"] != b["layout"] and (b["layout"] in GRAPHIC_LAYOUTS
                                                   or a["layout"] in GRAPHIC_LAYOUTS):
                    ev.append({"sound": "whoosh", "at": b["start"] - 0.2, "volume": 0.3})
            for o in overlays:
                if "sfx" in o:
                    continue
                if o["type"] == "media":
                    ev.append({"sound": "pop", "at": o["start"], "volume": 0.4})
                elif o["type"] == "chip":
                    ev.append({"sound": "ding", "at": o["start"], "volume": 0.3})
                elif o["type"] == "text" and o.get("style", "title") in ("title", "big"):
                    if self.look_name == "punchy" and o.get("style") == "big":
                        ev.append({"sound": "riser", "at": max(0, o["start"] - 1.2),
                                   "volume": 0.4})
                        ev.append({"sound": "boom", "at": o["start"], "volume": 0.45})
                        continue
                    snd = "boom" if self.look_name == "editorial" else "pop"
                    ev.append({"sound": snd, "at": o["start"], "volume": 0.45})
                elif o["type"] == "note":
                    ev.append({"sound": "pop", "at": o["start"], "volume": 0.35})
            for t0, n, cps in self._typing:
                for i in range(n):
                    if i % 2 == 0:
                        ev.append({"sound": "click", "at": t0 + i / cps, "volume": 0.22})
            for c in self.ctas():
                ev.append({"sound": "ding", "at": c["start"], "volume": 0.3})
        for o in overlays:
            if o.get("sfx"):
                ev.append({"sound": self._sound(o["sfx"]), "at": o["start"],
                           "volume": o.get("sfx_volume", 0.45)})
        for fx in self.e.get("sfx", []):
            ev.append({"sound": self._sound(fx.get("sound") or fx["file"]), "at": fx["at"],
                       "volume": fx.get("volume", 0.5)})
        return ev

    def _sound(self, s):
        return s if s in sfx_mod.BUILTIN else self.path(s)

    # ---- step 5: assemble --------------------------------------------------------------
    def assemble(self, clips, ass, sfx_wav):
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
            inputs += ["-stream_loop", "-1", "-ss", str(music.get("start", 0)),
                       "-i", self.path(music["file"])]
            afc += (f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                    f"atrim=0:{self.duration:.3f},volume={music.get('volume', 0.12)},"
                    f"afade=t=in:d=0.3,"
                    f"afade=t=out:st={max(0, self.duration - 1.5):.3f}:d=1.5[mus];")
            if music.get("duck", True):
                afc = afc.replace("[voice];", "[voice0];") + \
                    "[voice0]asplit[voice][vkey];[mus][vkey]sidechaincompress=" \
                    "threshold=0.03:ratio=6:attack=20:release=300[musd];"
                mix.append("[musd]")
            else:
                mix.append("[mus]")
            n += 1
        if sfx_wav:
            inputs += ["-i", sfx_wav]
            afc += f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo[fx];"
            mix.append("[fx]")
            n += 1
        lufs = self.e.get("loudness", -14)
        if len(mix) > 1:
            afc += "".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0,"
        else:
            afc += "[voice]"
        afc += f"loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000[a]"

        vfc = f"[0:v]ass='{esc_filter_path(ass)}':fontsdir='{esc_filter_path(self.fonts_dir)}'[v]"
        run(["ffmpeg", "-y", *inputs, "-filter_complex", vfc + ";" + afc,
             "-map", "[v]", "-map", "[a]", *self.x264, "-r", str(self.fps),
             "-c:a", "aac", "-b:a", "192k", "-t", f"{self.duration:.3f}",
             "-movflags", "+faststart", out])
        return out

    def render(self):
        os.makedirs(self.work, exist_ok=True)
        shots = self.shots()
        overlays = self.overlays()
        print(f"look: {self.look_name}")
        print("1/5 trimming presenter track")
        self.build_aroll()
        needs_matte = any(s["layout"] == "cutout" for s in shots) or any(
            o["z"] == "behind" for o in overlays)
        if needs_matte:
            print("    cutting out the presenter (person matte)")
            self.build_matte()
        self.card, self.mask_h = self.card_mask()
        print(f"2/5 rendering {len(shots)} shots")
        clips = [self.render_shot(i, s, overlays) for i, s in enumerate(shots)]
        print("3/5 captions and text")
        ass = self.write_ass(shots, overlays)
        print("4/5 sound effects")
        ev = self.sfx_events(shots, overlays)
        sfx_wav = sfx_mod.build_track(ev, self.duration, os.path.join(self.work, "sfx.wav")) \
            if ev else None
        print("5/5 assembling")
        out = self.assemble(clips, ass, sfx_wav)
        d = float(probe(out)["format"]["duration"])
        print(f"done: {out}  ({d:.2f}s, {len(ev)} sound effects)")
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("--work", default=None)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    work = a.work or os.path.join(os.path.dirname(os.path.abspath(a.edit)), "work",
                                  "preview" if a.preview else "render")
    Reel(a.edit, work, a.preview).render()


if __name__ == "__main__":
    main()
