# CapCut drafts (MCP server + exporter)

Build CapCut desktop drafts from Claude: the same tool set as
[VectCutAPI](https://github.com/sun-guannan/VectCutAPI) (the most-starred
CapCut automation project, ~2.4k stars), plus an exporter that turns any
reel-editor `edit.json` into an editable CapCut project.

Everything runs on the computer where CapCut is installed. Drafts are written
straight into CapCut's drafts folder; reopen CapCut's home screen and the
project is there to edit and export.

## Install

```bash
cd videoediting
python3 -m venv .venv && source .venv/bin/activate
pip install -r capcut/requirements.txt
```

You also need ffmpeg (for `export_reel`, which reuses the reel renderer).

## Use from Claude Code

```bash
claude mcp add capcut -- "$(pwd)/.venv/bin/python" "$(pwd)/capcut/mcp_server.py"
```

Claude Desktop: Settings > Developer > Edit config, add

```json
{"mcpServers": {"capcut": {"command": "/full/path/videoediting/.venv/bin/python",
                           "args": ["/full/path/videoediting/capcut/mcp_server.py"]}}}
```

Then ask, for example:

> Make a CapCut draft from ~/Desktop/take.mp4: keep 0:03-0:41, add
> ~/Desktop/logo.png top right from 2s to 5s, a caption "3 tools I use" at the
> top for the first 3 seconds, and ~/Music/bed.mp3 at 15% volume.

> Export my reel edit (~/reels/ep1/edit.json) to CapCut so I can tweak it.

## Tools

| tool | does |
|---|---|
| `create_draft` | new draft (default 1080x1920, 30 fps) |
| `add_video` | clip with source in/out, timeline position, speed, volume, position/size, fades, transition, in/out animation |
| `add_image` | image layer with position/size and animations |
| `add_audio` | music, voiceover or sound effect with fades |
| `add_text` | text layer: size, color, bold/italic, font, border, background, shadow, text animations |
| `add_subtitle` | import an .srt as captions |
| `add_effect` | video effect or color filter over a time range |
| `add_sticker` | CapCut library sticker by resource id |
| `add_video_keyframe` | animate position, scale, rotation, opacity, color, volume |
| `get_video_duration` | media length |
| `save_draft` | write the draft (media copied inside it) to CapCut's drafts folder |
| `list_effects` | names for effects, filters, transitions, animations, fonts |
| `list_drafts` | drafts in CapCut's folder |
| `export_reel` | reel-editor `edit.json` -> CapCut draft |

Positions: `x`, `y` are the center of the element as fractions of the frame
(0.5, 0.5 is the middle). `width` is a fraction of the frame width. Times are
seconds.

## export_reel: what you get in CapCut

- **Main track**: your recording, cut exactly where the skill cut it, with the
  punch-in zooms. Every cut is a normal CapCut clip, so you can extend or move it.
- **layouts track**: shots CapCut can't build natively (split screen, inset
  boxes, cutout, app window, darkened hook, words behind your head) as
  pre-rendered clips over the main track. The voice stays on the main track.
- **text tracks**: every caption, title, header, chip, note, banner and CTA as
  editable CapCut text, at the same position and color.
- **overlay tracks**: screenshots, clips and generated stickers at their place
  and size.
- **music** and **sfx tracks**: the music bed and every sound effect.

Not carried over (add them in CapCut if you want): the color grade, voice
cleanup and loudness, music ducking, rounded corners and shadows on overlays,
two colors inside one caption, text pop-in animations, the prompt card's frame.

Command line: `python3 capcut/export_reel.py edit.json` (options:
`--drafts-dir`, `--link-dir`, `--name`).

## Limits to know

- **Only tested by building and re-reading drafts, not in the CapCut app.** The
  draft layout (draft_content.json, its mirrors and a Timelines/ copy) follows
  VectCutAPI's "jianying_pro_10"/"capcut" profile. If a CapCut update changes or
  encrypts the format, drafts may not open; tell me the CapCut version and what
  happens.
- **Effects, filters, transitions, animations and fonts use JianYing resource
  IDs** (from pyJianYingDraft). Most exist in CapCut too; some may show as
  missing. Core editing (cuts, layers, text, positions, keyframes, audio) needs
  no IDs.
- **Media paths are absolute.** Build drafts on the computer that runs CapCut.
  If you build elsewhere, pass `link_dir` / `--link-dir` with the CapCut drafts
  folder path on that computer, then copy the draft folder there.
- **Close the draft in CapCut** before overwriting it with the same name.

## Where CapCut keeps drafts

- macOS: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft`
- Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`

Set `CAPCUT_DRAFTS_DIR` if yours is elsewhere (CapCut > Settings shows it).
