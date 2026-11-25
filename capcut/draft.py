"""Build CapCut desktop drafts from Python: video, audio, images, text, subtitles,
effects, stickers and keyframes, then save a draft folder CapCut can open.

Built on pyJianYingDraft (Apache-2.0). The draft folder layout (draft_content.json
with its mirrors and a Timelines/ copy) and the template in ./template come from
VectCutAPI (Apache-2.0, https://github.com/sun-guannan/VectCutAPI); see NOTICE.

Coordinates: x, y are the center of the element as fractions of the frame
(0,0 top-left; 0.5,0.5 center). Times are in seconds.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

import pyJianYingDraft as pj
from pyJianYingDraft.track import TrackSpec

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template")
MIRRORS = ("draft_content.json", "draft_content.json.bak", "template-2.tmp")
TIMELINE_EXTRA = "template.tmp"
# CapCut text size is not in pixels. About 10 px of a 1920-high frame per unit
# matches what CapCut shows for its default caption size; adjust in the app.
PX_PER_TEXT_UNIT = 10.0


def default_drafts_dir():
    """CapCut's drafts folder on this computer, or None if not found."""
    env = os.environ.get("CAPCUT_DRAFTS_DIR")
    if env:
        return env
    home = os.path.expanduser("~")
    cands = [
        os.path.join(home, "Movies", "CapCut", "User Data", "Projects", "com.lveditor.draft"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "User Data", "Projects",
                     "com.lveditor.draft"),
    ]
    for c in cands:
        if c and os.path.isdir(c):
            return c
    return None


def hex_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", path],
                         capture_output=True, text=True).stdout
    j = json.loads(out or "{}")
    s = next((x for x in j.get("streams", []) if x.get("width")), {})
    return s.get("width"), s.get("height"), float(j.get("format", {}).get("duration", 0) or 0)


def get_video_duration(path):
    return probe(path)[2]


def _enum(enum_cls, name):
    if name is None:
        return None
    try:
        return enum_cls[name]
    except KeyError:
        matches = [m for m in enum_cls.__members__ if name.lower() in m.lower()]
        hint = f"; close matches: {', '.join(matches[:8])}" if matches else ""
        raise ValueError(f"unknown {enum_cls.__name__} {name!r}{hint}")


class Draft:
    """One CapCut draft being built. Each add_* returns a segment id."""

    def __init__(self, name=None, width=1080, height=1920, fps=30):
        self.name = name or f"reel_{time.strftime('%Y%m%d_%H%M%S')}"
        self.width, self.height, self.fps = width, height, fps
        self.script = pj.ScriptFile(width, height, fps, maintrack_adsorb=True)
        self.tracks = {}
        self.segments = {}

    # ---- helpers -------------------------------------------------------------------
    def _track(self, kind, name):
        key = (kind, name)
        if key not in self.tracks:
            self.tracks[key] = self.script.append_track(TrackSpec(getattr(pj.TrackType, kind),
                                                                  name=name))
        return self.tracks[key]

    def _clip(self, x=0.5, y=0.5, scale=1.0, rotation=0.0, alpha=1.0):
        return pj.ClipSettings(transform_x=(x - 0.5) * 2, transform_y=(0.5 - y) * 2,
                               scale_x=scale, scale_y=scale, rotation=rotation, alpha=alpha)

    def _fit_scale(self, path, width=None, cover=False):
        """CapCut fits media inside the canvas at scale 1. Return the scale that makes
        it `width` (fraction of canvas width) wide, or covers the canvas."""
        w, h, _ = probe(path)
        if not w or not h:
            return 1.0
        fit = min(self.width / w, self.height / h)
        if cover:
            return max(self.width / w, self.height / h) / fit
        if width is None:
            return 1.0
        return (self.width * width) / (w * fit)

    def _add(self, seg, kind, track):
        self.script.add_segment(seg, self._track(kind, track))
        sid = f"seg{len(self.segments) + 1}"
        self.segments[sid] = seg
        return sid

    # ---- media ---------------------------------------------------------------------
    def add_video(self, path, start=0.0, end=None, target_start=0.0, speed=1.0, volume=1.0,
                  x=0.5, y=0.5, width=None, scale=None, cover=False, track="video_main",
                  fade_in=0.0, fade_out=0.0, transition=None, intro=None, outro=None):
        """Add a clip. start/end cut the source; target_start places it on the timeline."""
        mat = pj.VideoMaterial(path)
        dur = mat.duration / 1e6
        end = dur if end is None else min(end, dur)
        s = scale if scale is not None else self._fit_scale(path, width, cover)
        seg = pj.VideoSegment(mat, pj.trange_seconds(target_start, duration=(end - start) / speed),
                              source_timerange=pj.trange_seconds(start, end=end), speed=speed,
                              volume=volume, clip_settings=self._clip(x, y, s))
        if fade_in or fade_out:
            seg.add_fade(f"{fade_in}s", f"{fade_out}s")
        if transition:
            seg.add_transition(_enum(pj.TransitionType, transition))
        if intro:
            seg.add_animation(_enum(pj.IntroType, intro))
        if outro:
            seg.add_animation(_enum(pj.OutroType, outro))
        return self._add(seg, "video", track)

    def add_image(self, path, target_start, duration, x=0.5, y=0.5, width=None, scale=None,
                  cover=False, track="overlay", intro=None, outro=None):
        mat = pj.VideoMaterial(path)
        s = scale if scale is not None else self._fit_scale(path, width, cover)
        seg = pj.VideoSegment(mat, pj.trange_seconds(target_start, duration=duration),
                              clip_settings=self._clip(x, y, s))
        if intro:
            seg.add_animation(_enum(pj.IntroType, intro))
        if outro:
            seg.add_animation(_enum(pj.OutroType, outro))
        return self._add(seg, "video", track)

    def add_audio(self, path, target_start=0.0, start=0.0, end=None, volume=1.0, speed=1.0,
                  fade_in=0.0, fade_out=0.0, track="audio"):
        mat = pj.AudioMaterial(path)
        dur = mat.duration / 1e6
        end = dur if end is None else min(end, dur)
        seg = pj.AudioSegment(mat, pj.trange_seconds(target_start, duration=(end - start) / speed),
                              source_timerange=pj.trange_seconds(start, end=end), speed=speed,
                              volume=volume)
        if fade_in or fade_out:
            seg.add_fade(f"{fade_in}s", f"{fade_out}s")
        return self._add(seg, "audio", track)

    # ---- text ----------------------------------------------------------------------
    def add_text(self, text, target_start, duration, x=0.5, y=0.8, size_px=60, color="#ffffff",
                 bold=False, italic=False, align="center", font=None, border=None,
                 border_width=40.0, background=None, background_alpha=1.0, shadow=False,
                 letter_spacing=0, line_spacing=0, max_width=0.82, intro=None, outro=None,
                 loop=None, track="text"):
        """size_px is the text height in pixels of a 1920-high frame (approximate)."""
        style = pj.TextStyle(size=size_px / PX_PER_TEXT_UNIT,
                             bold=bold, italic=italic, color=hex_rgb(color),
                             align={"left": 0, "center": 1, "right": 2}[align],
                             letter_spacing=letter_spacing, line_spacing=line_spacing,
                             auto_wrapping=True, max_line_width=max_width)
        seg = pj.TextSegment(
            text, pj.trange_seconds(target_start, duration=duration),
            font=_enum(pj.FontType, font) if font else None, style=style,
            clip_settings=self._clip(x, y),
            border=pj.TextBorder(color=hex_rgb(border), width=border_width) if border else None,
            background=pj.TextBackground(color=background, alpha=background_alpha,
                                         round_radius=0.2) if background else None,
            shadow=pj.TextShadow() if shadow else None)
        for anim, enum_cls in ((intro, pj.TextIntro), (outro, pj.TextOutro), (loop, pj.TextLoopAnim)):
            if anim:
                seg.add_animation(_enum(enum_cls, anim))
        return self._add(seg, "text", track)

    def add_subtitle(self, srt_path, size_px=56, color="#ffffff", y=0.8, time_offset=0.0,
                     track="subtitles"):
        style = pj.TextStyle(size=size_px / PX_PER_TEXT_UNIT, color=hex_rgb(color), align=1,
                             auto_wrapping=True)
        self.script.import_srt(srt_path, track, time_offset=time_offset, text_style=style,
                               clip_settings=self._clip(0.5, y))
        return track

    # ---- effects, stickers, keyframes ----------------------------------------------
    def add_effect(self, name, target_start, duration, params=None, track="effects"):
        """A scene/character effect by its library name (JianYing IDs; best effort in CapCut)."""
        try:
            eff = _enum(pj.VideoSceneEffectType, name)
        except ValueError:
            eff = _enum(pj.VideoCharacterEffectType, name)
        self._track("effect", track)
        self.script.add_effect(eff, pj.trange_seconds(target_start, duration=duration), track,
                               params=params)
        return track

    def add_filter(self, name, target_start, duration, intensity=100.0, track="filters"):
        self._track("filter", track)
        self.script.add_filter(_enum(pj.FilterType, name),
                               pj.trange_seconds(target_start, duration=duration), track,
                               intensity=intensity)
        return track

    def add_sticker(self, resource_id, target_start, duration, x=0.5, y=0.5, scale=1.0,
                    track="stickers"):
        seg = pj.StickerSegment(resource_id, pj.trange_seconds(target_start, duration=duration),
                                clip_settings=self._clip(x, y, scale))
        return self._add(seg, "sticker", track)

    def add_keyframe(self, segment_id, prop, time_offset, value):
        """prop: position_x, position_y, rotation, scale_x, scale_y, uniform_scale, alpha,
        saturation, contrast, brightness, volume. time_offset is seconds into the segment."""
        seg = self.segments[segment_id]
        seg.add_keyframe(_enum(pj.KeyframeProperty, prop), f"{time_offset}s", value)
        return segment_id

    # ---- save ----------------------------------------------------------------------
    def save(self, drafts_dir=None, link_dir=None, copy_media=True):
        """Write the draft folder into drafts_dir (CapCut's drafts folder by default).

        Media files are copied into the draft so it is self-contained. link_dir is the
        drafts folder the draft will finally live in, when you build it somewhere else
        and copy it over; media paths inside the draft point there.
        """
        drafts_dir = drafts_dir or default_drafts_dir() or os.path.abspath("capcut_drafts")
        link_dir = link_dir or drafts_dir
        out = os.path.join(drafts_dir, self.name)
        if os.path.exists(out):
            shutil.rmtree(out)
        shutil.copytree(TEMPLATE, out, ignore=shutil.ignore_patterns(".gitkeep", "__pycache__"))

        if copy_media:
            res = os.path.join(out, "Resources", "media")
            os.makedirs(res, exist_ok=True)
            seen = {}
            # Segments hold their own copies of the materials: rewrite those.
            for m in list(self.script.materials.videos) + list(self.script.materials.audios):
                src = m.path
                if src not in seen:
                    base = os.path.basename(src)
                    dst_name = base if base not in seen.values() else f"{len(seen)}_{base}"
                    shutil.copy2(src, os.path.join(res, dst_name))
                    seen[src] = dst_name
                m.path = os.path.join(link_dir, self.name, "Resources", "media", seen[src])

        content = json.loads(self.script.dumps())
        content["id"] = content.get("id") or str(uuid.uuid4()).upper()
        cfg = content.setdefault("canvas_config", {})
        cfg.update({"width": self.width, "height": self.height})
        if cfg.get("ratio") in (None, "", "original"):
            cfg["ratio"] = "9:16" if self.height > self.width else (
                "16:9" if self.width > self.height else "1:1")
        text = json.dumps(content, ensure_ascii=False)
        for rel in MIRRORS:
            with open(os.path.join(out, rel), "w", encoding="utf-8") as f:
                f.write(text)

        # Modern CapCut/JianYing also read a per-timeline copy under Timelines/<id>/.
        tl_root = os.path.join(out, "Timelines")
        tl_id = content["id"]
        old = [d for d in os.listdir(tl_root) if os.path.isdir(os.path.join(tl_root, d))]
        tl_dir = os.path.join(tl_root, tl_id)
        if old and old[0] != tl_id:
            os.rename(os.path.join(tl_root, old[0]), tl_dir)
        os.makedirs(tl_dir, exist_ok=True)
        for rel in MIRRORS + (TIMELINE_EXTRA,):
            with open(os.path.join(tl_dir, rel), "w", encoding="utf-8") as f:
                f.write(text)
        now = int(time.time() * 1_000_000)
        project = {"config": {"color_space": -1, "render_index_track_mode_on": False,
                              "use_float_render": False},
                   "create_time": now, "id": str(uuid.uuid4()).upper(), "main_timeline_id": tl_id,
                   "timelines": [{"create_time": now, "id": tl_id, "is_marked_delete": False,
                                  "name": "Timeline 1", "update_time": now}],
                   "update_time": now, "version": 0}
        for rel in ("project.json", "project.json.bak"):
            with open(os.path.join(tl_root, rel), "w", encoding="utf-8") as f:
                json.dump(project, f, separators=(",", ":"))
        layout_p = os.path.join(out, "timeline_layout.json")
        layout = json.load(open(layout_p))
        for item in layout.get("dockItems", []):
            item["timelineIds"] = [tl_id]
            item["timelineNames"] = ["Timeline 1"]
        json.dump(layout, open(layout_p, "w"), separators=(",", ":"))

        meta_p = os.path.join(out, "draft_meta_info.json")
        meta = json.load(open(meta_p))
        meta.update({"draft_fold_path": os.path.join(link_dir, self.name),
                     "draft_id": str(uuid.uuid4()).upper(), "draft_name": self.name,
                     "draft_root_path": link_dir,
                     "tm_draft_create": now, "tm_draft_modified": now,
                     "tm_duration": content.get("duration", 0)})
        json.dump(meta, open(meta_p, "w"), ensure_ascii=False, separators=(",", ":"))
        secs = now // 1_000_000
        with open(os.path.join(out, "draft_settings"), "w") as f:
            f.write(f"[General]\ndraft_create_time={secs}\ndraft_last_edit_time={secs}\n"
                    "real_edit_seconds=0\nreal_edit_keys=0\n"
                    f"cloud_last_modify_platform={'mac' if sys.platform == 'darwin' else 'windows'}\n")
        return out
