#!/usr/bin/env python3
"""Turn a reel-editor edit.json into an editable CapCut draft.

    python3 capcut/export_reel.py edit.json [--drafts-dir DIR] [--link-dir DIR] [--name NAME]

What lands in CapCut:
- Main track: the source recording, cut exactly as autocut kept it, one segment per
  kept range and shot, with the shot's punch-in zoom. Trims stay editable.
- Layout track: shots CapCut can't rebuild natively (split, full, broll, card, inset,
  window, cutout, darkened shots, text or cards behind the head) as pre-rendered
  clips on top of the main track. The voice still comes from the main track.
- Text tracks: every caption, title, header, chip, note, banner and CTA as CapCut
  text, at its position and color.
- Overlay tracks: images, clips and generated stickers at their position and size.
- Audio tracks: music and every sound effect.
Not carried over: the color grade, voice polish and loudness, ducking, rounded
corners and shadows on overlays, per-word colors inside one caption, text pop-in
animations. Add those in CapCut if you want them.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import render as render_mod  # noqa: E402
import sfx as sfx_mod  # noqa: E402
from capcut.draft import Draft, probe  # noqa: E402

TAG = re.compile(r"\{[^}]*\}")


class Lanes:
    """Assign overlapping items to numbered tracks (a CapCut track can't overlap)."""

    def __init__(self, prefix):
        self.prefix, self.ends = prefix, []

    def pick(self, start, end):
        for i, e in enumerate(self.ends):
            if start >= e - 1e-3:
                self.ends[i] = end
                return f"{self.prefix}{i + 1}"
        self.ends.append(end)
        return f"{self.prefix}{len(self.ends)}"


class RecordingAss(render_mod.Ass):
    """Ass that also records what was drawn, so text can be rebuilt in CapCut."""

    def __init__(self, W, H, styles):
        super().__init__(W, H, styles)
        self.items, self._in_text = [], False

    def text(self, start, end, style, x, y, text, tags="", layer=1, raw=False):
        self.items.append(dict(start=start, end=end, style=style, x=x, y=y, text=text,
                               tags=tags, raw=raw))
        self._in_text = True
        try:
            super().text(start, end, style, x, y, text, tags, layer, raw)
        finally:
            self._in_text = False

    def raw(self, start, end, style, tags, text, layer=1):
        if not self._in_text and "\\p1" not in tags and "\\1a&HFF&" not in tags:
            m = re.search(r"\\pos\((-?\d+),(-?\d+)\)", tags)
            if m and TAG.sub("", text).strip():
                self.items.append(dict(start=start, end=end, style=style, x=int(m.group(1)),
                                       y=int(m.group(2)), text=text, tags=tags, raw=True))
        super().raw(start, end, style, tags, text, layer)


def merge_growing(items):
    """Typing animations are drawn as many growing events; keep one per line."""
    out = []
    for it in sorted(items, key=lambda i: (i["start"], i["y"], i["x"])):
        clean = TAG.sub("", it["text"]).replace("\\N", "\n").rstrip("|").strip()
        if not clean:
            continue
        it = dict(it, clean=clean)
        for prev in reversed(out[-12:]):
            if (prev["style"] == it["style"] and abs(prev["x"] - it["x"]) < 2
                    and abs(prev["y"] - it["y"]) < 2 and abs(prev["end"] - it["start"]) < 0.05
                    and (clean.startswith(prev["clean"]) or prev["clean"].startswith(clean))):
                prev["end"], prev["clean"] = it["end"], max(clean, prev["clean"], key=len)
                break
        else:
            out.append(it)
    return out


def text_props(reel, it):
    s = reel.styles[it["style"]]
    k = reel.H / 1920
    size = s["size"]
    m = re.search(r"\\fs(\d+)", it["tags"])
    if m:
        size = int(m.group(1)) / k
    color = s["color"]
    m = re.search(r"\\c&H([0-9A-Fa-f]{6})&", it["tags"])
    if m:
        bgr = m.group(1)
        color = f"#{bgr[4:6]}{bgr[2:4]}{bgr[0:2]}"
    text = it["clean"]
    if s.get("upper"):
        text = text.upper()
    elif s.get("lower"):
        text = text.lower()
    return dict(text=text, size_px=size, color=color, italic=bool(s.get("italic")),
                bold=any(w in s["font"] for w in ("Black", "ExtraBold", "Anton")),
                background=s.get("box"), shadow=bool(s.get("shadow") or s.get("glow")),
                border=s.get("outline_color") if s.get("outline") else None)


def export(edit_json, drafts_dir=None, name=None, link_dir=None):
    edit_json = os.path.abspath(edit_json)
    work = os.path.join(os.path.dirname(edit_json), "work", "capcut")
    reel = render_mod.Reel(edit_json, work, preview=False)
    os.makedirs(work, exist_ok=True)
    shots, overlays = reel.shots(), reel.overlays()
    W, H = reel.W, reel.H
    draft = Draft(name or os.path.splitext(os.path.basename(reel.e.get("output", "reel")))[0],
                  W, H, reel.fps)
    src = reel.path(reel.e["source"])

    # 1. Shots that need the renderer are baked; everything else is native.
    def baked(s):
        if s["layout"] not in ("talk",):
            return True
        if s.get("dim"):
            return True
        return any(o["z"] == "behind" and o["start"] < s["end"] and o["end"] > s["start"]
                   for o in overlays)

    bake = [i for i, s in enumerate(shots) if baked(s)]
    if bake:
        print(f"rendering {len(bake)} layout shot(s) CapCut can't build natively")
        reel.build_aroll()
        if any(shots[i]["layout"] == "cutout" for i in bake) or any(
                o["z"] == "behind" for o in overlays):
            reel.build_matte()
        reel.card, reel.mask_h = reel.card_mask()
        behind_only = [o for o in overlays if o["z"] == "behind"]
        clips = {i: reel.render_shot(i, shots[i], behind_only) for i in bake}

    # 2. Main track: source cut by keep ranges, split at shot boundaries.
    sw, sh, _ = probe(src)
    cover = max(W / sw, H / sh) / min(W / sw, H / sh) if sw and sh else 1.0
    o_t, pieces = 0.0, []
    for ks, ke in reel.keep:
        pieces.append((o_t, o_t + ke - ks, ks))
        o_t += ke - ks
    for i, s in enumerate(shots):
        z = s.get("zoom", 1.0) if s["layout"] in ("talk", "cutout") else 1.0
        for po, pe, ps in pieces:
            a, b = max(s["start"], po), min(s["end"], pe)
            if b - a < 1 / reel.fps:
                continue
            src_a = ps + (a - po)
            draft.add_video(src, start=src_a, end=src_a + (b - a), target_start=a,
                            scale=cover * z, y=0.5 + (z - 1) * (0.5 - reel.face_y),
                            track="video_main")
        if i in bake:
            draft.add_video(clips[i], start=0, end=s["end"] - s["start"], target_start=s["start"],
                            volume=0.0, scale=1.0, track="layouts")

    # 3. Front media overlays (screenshots, clips, generated stickers).
    lanes = Lanes("overlay")
    for o in overlays:
        if o["type"] != "media":
            continue
        if o["z"] == "behind" and any(baked(s) for s in shots
                                      if s["start"] < o["end"] and s["end"] > o["start"]):
            continue  # already inside a baked shot
        path = reel.path(o["media"])
        end = min(o["end"], reel.duration)
        tr = lanes.pick(o["start"], end)
        w, h, dur = probe(path)
        if os.path.splitext(path)[1].lower() in render_mod.IMAGE_EXT:
            draft.add_image(path, o["start"], end - o["start"], x=o.get("x", 0.5),
                            y=o.get("y", 0.3), width=o.get("w", 0.4), track=tr)
        else:
            ms = o.get("media_start", 0)
            draft.add_video(path, start=ms, end=min(dur, ms + end - o["start"]),
                            target_start=o["start"], volume=0.0, x=o.get("x", 0.5),
                            y=o.get("y", 0.3), width=o.get("w", 0.4), track=tr)

    # 4. All text, recorded from the renderer's own caption and text planning.
    original_ass = render_mod.Ass
    render_mod.Ass = RecordingAss
    try:
        rec_holder = {}
        orig_write = RecordingAss.write

        def keep(self, path):
            rec_holder["ass"] = self
            return orig_write(self, path)
        RecordingAss.write = keep
        reel.write_ass(shots, overlays)
    finally:
        RecordingAss.write = orig_write
        render_mod.Ass = original_ass
    text_lanes = Lanes("text")
    for it in merge_growing(rec_holder["ass"].items):
        if it["style"] == "ui_label" or it["clean"] == "\u2191":
            continue  # prompt-card chrome: CapCut gets the typed text on a card background
        p = text_props(reel, it)
        if it["style"] == "ui":
            p["background"] = "#f4f1ea"
        end = min(it["end"], reel.duration)
        if end - it["start"] < 0.05:
            continue
        draft.add_text(p["text"], it["start"], end - it["start"], x=it["x"] / W, y=it["y"] / H,
                       size_px=p["size_px"], color=p["color"], bold=p["bold"],
                       italic=p["italic"], background=p["background"], shadow=p["shadow"],
                       border=p["border"], track=text_lanes.pick(it["start"], end))

    # 5. Music and sound effects.
    music = reel.e.get("music")
    if music:
        mp = reel.path(music["file"])
        mdur = probe(mp)[2]
        t, ms = 0.0, music.get("start", 0)
        while t < reel.duration - 0.05:  # loop the track if it's shorter than the reel
            seg = min(mdur - ms, reel.duration - t)
            last = t + seg >= reel.duration - 0.05
            draft.add_audio(mp, target_start=t, start=ms, end=ms + seg,
                            volume=music.get("volume", 0.12), fade_in=0.3 if t == 0 else 0,
                            fade_out=1.5 if last else 0, track="music")
            t, ms = t + seg, 0
    sfx_dir = os.path.join(work, "sfx")
    os.makedirs(sfx_dir, exist_ok=True)
    fx_lanes = Lanes("sfx")
    for j, ev in enumerate(reel.sfx_events(shots, overlays)):
        snd = ev["sound"]
        if snd in sfx_mod.BUILTIN:
            path = os.path.join(sfx_dir, f"{snd}_{j}.wav")
            sfx_mod.write_wav(path, sfx_mod.load(snd, seed=j))
        else:
            path = snd
        at = max(0.0, ev["at"])
        dur = probe(path)[2]
        dur = min(dur, reel.duration - at)
        if dur <= 0.02:
            continue
        draft.add_audio(path, target_start=at, end=dur, volume=ev.get("volume", 0.5),
                        track=fx_lanes.pick(at, at + dur))

    return draft.save(drafts_dir, link_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("--drafts-dir", default=None,
                    help="where to write the draft (default: CapCut's drafts folder)")
    ap.add_argument("--link-dir", default=None,
                    help="CapCut drafts folder the draft will be moved to, if different")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    print("saved:", export(a.edit, a.drafts_dir, a.name, a.link_dir))


if __name__ == "__main__":
    main()
