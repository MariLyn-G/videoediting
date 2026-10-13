# reel-editor

A Claude skill that edits a talking-head recording into a vertical 1080x1920
reel in one of four styles, each measured from a reference reel:

- `explainer`: word-pop captions, split-screen and full-screen graphics
- `editorial`: brand-color magazine look, giant words behind your head,
  typed prompt cards, karaoke captions
- `steps`: persistent header, step chips, quiet serif captions, stickers
- `floating`: you cut out over a blurred room, app screens floating behind you
- `punchy`: white captions with the key word big and yellow, stickers
  (tool tags, receipts, prices, handwritten notes with arrows)

Claude reads what you say and adds the images the script calls for:
generated stickers and cards, plus your own screenshots and clips.

Jump cuts, captions, overlays, synthesized sound effects, music ducking and
loudness are handled. Instructions for Claude are in `SKILL.md`; the styles,
their sound design and example prompts are in `references/looks.md`.

## Install

Claude Code (all projects):

```bash
git clone https://github.com/MariLyn-G/videoediting ~/.claude/skills/reel-editor
```

Claude Code (one project): clone into `<project>/.claude/skills/reel-editor`.

claude.ai: zip this folder and upload it under Settings > Capabilities > Skills.
The code environment there must have ffmpeg.

## Requirements

- ffmpeg built with libass
- Python 3
- Google Chrome or Chromium (for the generated graphics)
- `pip install numpy faster-whisper mediapipe`
  - faster-whisper (transcription) downloads a model from Hugging Face on first run
  - mediapipe (person cutout, text behind the head) downloads a model from
    storage.googleapis.com on first run. On a Linux server it also needs
    `libegl1` and `libgles2`.

## Layout

- `SKILL.md`: workflow Claude follows
- `references/looks.md`: the four styles, their sounds, and prompts to use
- `references/style-guide.md`: detailed measurements of the explainer reference
- `references/edit-format.md`: the `edit.json` format
- `scripts/`: `transcribe.py`, `autocut.py`, `render.py`, `looks.py`,
  `matte.py`, `sfx.py`, `graphic.py`, `contact_sheet.sh`
- `assets/fonts/`: Inter, Instrument Serif, Playfair Display, Nunito,
  Patrick Hand, Caveat, IBM Plex Mono (all SIL Open Font License)
