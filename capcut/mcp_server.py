#!/usr/bin/env python3
"""MCP server that builds CapCut desktop drafts.

Same tool set as VectCutAPI (create_draft, add_video, add_audio, add_image, add_text,
add_subtitle, add_effect, add_sticker, add_video_keyframe, get_video_duration,
save_draft), plus list_effects, list_drafts and export_reel (turns a reel-editor
edit.json into an editable CapCut draft).

Run:  python3 capcut/mcp_server.py        (stdio)
Register with Claude Code:
      claude mcp add capcut -- python3 /path/to/videoediting/capcut/mcp_server.py
Media paths are files on this computer. Drafts are saved into CapCut's drafts folder
(auto-detected, or CAPCUT_DRAFTS_DIR).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # 1.x
    from mcp.server.fastmcp import FastMCP as _Server

import pyJianYingDraft as pj  # noqa: E402
from capcut.draft import Draft, default_drafts_dir, get_video_duration as _duration  # noqa: E402

mcp = _Server("capcut")
DRAFTS: dict[str, Draft] = {}


def _get(draft_id: str) -> Draft:
    if draft_id not in DRAFTS:
        raise ValueError(f"no draft {draft_id!r}; create one with create_draft "
                         f"(open drafts: {', '.join(DRAFTS) or 'none'})")
    return DRAFTS[draft_id]


@mcp.tool()
def create_draft(name: str = "", width: int = 1080, height: int = 1920, fps: int = 30) -> str:
    """Start a new CapCut draft. Returns its draft_id (also its folder name).
    Default canvas is 1080x1920 vertical."""
    d = Draft(name or None, width, height, fps)
    DRAFTS[d.name] = d
    return d.name


@mcp.tool()
def add_video(draft_id: str, path: str, start: float = 0.0, end: float | None = None,
              target_start: float = 0.0, speed: float = 1.0, volume: float = 1.0,
              x: float = 0.5, y: float = 0.5, width: float | None = None,
              scale: float | None = None, cover: bool = False, track: str = "video_main",
              fade_in: float = 0.0, fade_out: float = 0.0, transition: str | None = None,
              intro: str | None = None, outro: str | None = None) -> str:
    """Add a video clip. start/end cut the source (seconds); target_start places it on
    the timeline. x, y = center as fractions of the frame. width = fraction of frame
    width, or cover=true to fill the frame. Use a different `track` for overlays
    (tracks are stacked in the order first used). Returns a segment_id."""
    return _get(draft_id).add_video(path, start, end, target_start, speed, volume, x, y, width,
                                    scale, cover, track, fade_in, fade_out, transition, intro,
                                    outro)


@mcp.tool()
def add_image(draft_id: str, path: str, target_start: float, duration: float,
              x: float = 0.5, y: float = 0.5, width: float | None = None,
              scale: float | None = None, cover: bool = False, track: str = "overlay",
              intro: str | None = None, outro: str | None = None) -> str:
    """Add an image (png/jpg) for `duration` seconds at target_start. Returns a segment_id."""
    return _get(draft_id).add_image(path, target_start, duration, x, y, width, scale, cover,
                                    track, intro, outro)


@mcp.tool()
def add_audio(draft_id: str, path: str, target_start: float = 0.0, start: float = 0.0,
              end: float | None = None, volume: float = 1.0, speed: float = 1.0,
              fade_in: float = 0.0, fade_out: float = 0.0, track: str = "audio") -> str:
    """Add music, a voiceover or a sound effect. Returns a segment_id."""
    return _get(draft_id).add_audio(path, target_start, start, end, volume, speed, fade_in,
                                    fade_out, track)


@mcp.tool()
def add_text(draft_id: str, text: str, target_start: float, duration: float,
             x: float = 0.5, y: float = 0.8, size_px: float = 60, color: str = "#ffffff",
             bold: bool = False, italic: bool = False, align: str = "center",
             font: str | None = None, border: str | None = None,
             background: str | None = None, background_alpha: float = 1.0,
             shadow: bool = False, intro: str | None = None, outro: str | None = None,
             loop: str | None = None, track: str = "text") -> str:
    """Add a text layer. size_px ~ text height in pixels on a 1920-high frame. Colors
    are hex (#rrggbb). font/intro/outro/loop are library names (see list_effects).
    Returns a segment_id."""
    return _get(draft_id).add_text(text, target_start, duration, x, y, size_px, color, bold,
                                   italic, align, font, border, 40.0, background,
                                   background_alpha, shadow, intro=intro, outro=outro, loop=loop,
                                   track=track)


@mcp.tool()
def add_subtitle(draft_id: str, srt_path: str, size_px: float = 56, color: str = "#ffffff",
                 y: float = 0.8, time_offset: float = 0.0, track: str = "subtitles") -> str:
    """Import an .srt file as captions on their own text track."""
    return _get(draft_id).add_subtitle(srt_path, size_px, color, y, time_offset, track)


@mcp.tool()
def add_effect(draft_id: str, name: str, target_start: float, duration: float,
               kind: str = "effect", intensity: float = 100.0) -> str:
    """Add a video effect (kind="effect") or a color filter (kind="filter") over a time
    range. Names come from list_effects. Effect IDs are JianYing's; most also exist in
    CapCut, but some may show as missing there."""
    d = _get(draft_id)
    if kind == "filter":
        return d.add_filter(name, target_start, duration, intensity)
    return d.add_effect(name, target_start, duration)


@mcp.tool()
def add_sticker(draft_id: str, resource_id: str, target_start: float, duration: float,
                x: float = 0.5, y: float = 0.5, scale: float = 1.0) -> str:
    """Add a CapCut library sticker by its resource_id (copy it from a draft where you
    added the sticker by hand). For your own images use add_image. Returns a segment_id."""
    return _get(draft_id).add_sticker(resource_id, target_start, duration, x, y, scale)


@mcp.tool()
def add_video_keyframe(draft_id: str, segment_id: str, property: str, times: list[float],
                       values: list[float]) -> str:
    """Animate a video/image segment. property: position_x, position_y, rotation,
    scale_x, scale_y, uniform_scale, alpha, saturation, contrast, brightness, volume.
    times are seconds from the segment's start; one value per time."""
    d = _get(draft_id)
    for t, v in zip(times, values):
        d.add_keyframe(segment_id, property, t, v)
    return f"{len(times)} keyframes on {segment_id}"


@mcp.tool()
def get_video_duration(path: str) -> float:
    """Duration of a media file in seconds."""
    return _duration(path)


@mcp.tool()
def save_draft(draft_id: str, drafts_dir: str = "", link_dir: str = "") -> str:
    """Write the draft (media copied inside it) into CapCut's drafts folder, or
    drafts_dir. Reopen CapCut's home screen to see it. link_dir: the drafts folder the
    draft will be moved to, if you save it elsewhere first."""
    out = _get(draft_id).save(drafts_dir or None, link_dir or None)
    return f"saved: {out}"


@mcp.tool()
def list_effects(kind: str = "effect", query: str = "", limit: int = 50) -> list[str]:
    """Names usable in add_effect / add_text / add_video. kind: effect, character_effect,
    filter, transition, video_intro, video_outro, text_intro, text_outro, text_loop, font.
    query filters by substring."""
    enums = {"effect": pj.VideoSceneEffectType, "character_effect": pj.VideoCharacterEffectType,
             "filter": pj.FilterType, "transition": pj.TransitionType,
             "video_intro": pj.IntroType, "video_outro": pj.OutroType,
             "text_intro": pj.TextIntro, "text_outro": pj.TextOutro,
             "text_loop": pj.TextLoopAnim, "font": pj.FontType}
    names = list(enums[kind].__members__)
    if query:
        names = [n for n in names if query.lower() in n.lower()]
    return names[:limit]


@mcp.tool()
def list_drafts(drafts_dir: str = "") -> list[str]:
    """Drafts in CapCut's drafts folder (or drafts_dir)."""
    root = drafts_dir or default_drafts_dir()
    if not root or not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


@mcp.tool()
def export_reel(edit_json: str, drafts_dir: str = "", name: str = "") -> str:
    """Turn a reel-editor edit.json into an editable CapCut draft: the cut presenter
    track, every caption and text as CapCut text, stickers and media as layers, music
    and sound effects as audio. Layouts CapCut can't rebuild (split, inset, cutout,
    window...) come in as pre-rendered clips."""
    from capcut.export_reel import export
    return f"saved: {export(edit_json, drafts_dir or None, name or None)}"


if __name__ == "__main__":
    mcp.run()
