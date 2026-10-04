# reel-editor

A Claude skill that edits a talking-head recording into a vertical 1080x1920
reel: jump cuts with no dead air, word-by-word captions, punch-in zooms,
split-screen and full-screen graphics, b-roll, and a "comment X" call to
action. Instructions for Claude are in `SKILL.md`.

## Install

Claude Code (all projects):

```bash
git clone <this repo> ~/.claude/skills/reel-editor
```

Claude Code (one project): clone into `<project>/.claude/skills/reel-editor`.

claude.ai: zip this folder and upload it under Settings > Capabilities > Skills.
The code environment there must have ffmpeg.

## Requirements

- ffmpeg built with libass
- Python 3
- `pip install faster-whisper` for transcription (downloads a model from
  Hugging Face on first run)

## Layout

- `SKILL.md`: workflow Claude follows
- `references/style-guide.md`: the style, measured from the reference reel
- `references/edit-format.md`: the `edit.json` format
- `scripts/`: `transcribe.py`, `autocut.py`, `render.py`, `contact_sheet.sh`
- `assets/fonts/`: Inter and Instrument Serif (SIL Open Font License)
