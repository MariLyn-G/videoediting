---
name: reel-editor
description: Edit raw talking-head footage into a vertical 9:16 Instagram Reel / TikTok / Short in one of four creator styles - "explainer" (word-pop captions, split-screen graphics), "editorial" (brand-color magazine look, giant words behind the head, typed prompt cards, karaoke captions), "steps" (persistent header, step chips, quiet serif captions, stickers) or "floating" (presenter cut out over a blurred room with app screens floating behind them). Handles jump cuts, captions, overlays, sound effects, music ducking and loudness. Use when the user asks to edit, cut, caption or assemble a reel, short, TikTok or vertical video, or to make a video "like" a reference reel.
---

# Reel editor

Turns a talking-head recording plus graphics into a finished 1080x1920
reel. Four looks, each measured from a reference reel. Read
`references/looks.md` first, then `references/edit-format.md`.

Scripts are in `scripts/`. They need `ffmpeg` (with libass), Python 3 and
`pip install numpy`. Transcription needs `pip install faster-whisper`
(model from Hugging Face). Cutouts and text behind the head need
`pip install mediapipe` (model from storage.googleapis.com).

## What this can and can't do

Reliable: silence and retake removal, reframing, word-timed captions in
four styles, layouts, punch-ins, person cutout, text and cards behind the
presenter, typed prompt cards, stickers, title text, synthesized sound
effects, music ducking, loudness to -14 LUFS.

Not done: custom motion graphics (animated mascots, counters, follow cards),
music selection, and judging which take is the best performance. Graphics
come from the user, screenshots, the built-in cards and text, or an
image/video generator if one is connected. Say this up front if the user
expects animation.

## Workflow

Work in a folder next to the footage: `assets/` for media, `work/` for
intermediates.

1. **Pick the look.** From the user's words or reference ("like the green
   one" = editorial). If unclear, ask, showing the four one-line
   descriptions from `looks.md`.

2. **Inspect inputs.** `ffprobe` the recording. Contact sheet:
   `scripts/contact_sheet.sh raw.mp4 work/raw.jpg 5`. Set `face_y` (eye
   height as a fraction of the frame; 0.3-0.4 typical). Look at every asset.

3. **Transcribe.** `python3 scripts/transcribe.py raw.mp4 -o work/words.json`
   (`--lang` for non-English). If it can't run, ask for a transcript or SRT
   and build `words.json` from it. Fix misheard names in words.json.

4. **Cut.** Keep the last clean take of each line, drop false starts and
   filler, open on the hook. Target 30-55 s. `python3 scripts/autocut.py
   work/words.json -o work/cut.json --start N --end M --drop a-b`. Plan
   against the output timecodes it prints.

5. **Plan.** Write `edit.json`. Per look:
   - explainer: change shot every 1.2-3 s; graphic on every concrete noun;
     numbers as cards; first 1.5 s is a graphic.
   - editorial: open on `cutout` over brand color with a typed `title`
     behind the head; one prompt card when the user describes asking an AI;
     a big word behind the head 2-3 times at key words; picture-in-picture
     for proof; note box for the CTA.
   - steps: one `header` for the whole video; a `chip` at each "step N";
     stickers when brands are named; full-screen screen recordings.
   - floating: `cutout` with `"bg": "blur"` for most of it; cards behind the
     head (`"z": "behind"`) for clips; full-screen screens for steps;
     `emphasis` for 2-4 key words.
   Cut and place on word boundaries. Keep text out of the bottom 15% and the
   right 12% (Instagram UI).

6. **Preview.** `python3 scripts/render.py edit.json --preview`, then
   `scripts/contact_sheet.sh out/reel_preview.mp4 work/prev.jpg 0.5` and
   look at it. Check that captions don't cover faces or graphics, behind-head
   text is readable around the head, nothing is cropped, the cutout edge is
   clean. Fix and repeat. The trimmed track and matte are cached between
   renders.

7. **Final.** `python3 scripts/render.py edit.json`. Check with `ffprobe`
   and send the file and a contact sheet.

## Sound

Read the sound notes for the chosen look in `looks.md`. Music is the
user's: ask for a file or suggest a mood and tempo to search for. Built-in
effects are synthesized and plain; prefer library files if the user has
them. Never add music if the user will add trending audio in Instagram.

## Writing on-screen text

Captions are the speaker's words; fix spelling, don't rewrite. Titles and
behind-head words are 1-3 words, taken from what is said at that moment.
Prompt cards show what the speaker says they typed.

## New references

Contact sheet at 1 frame/s, scene cuts
(`ffmpeg -i ref.mp4 -vf "select='gt(scene,0.12)',showinfo" -f null -`), and
for sound the stereo difference spectrogram
(`ffmpeg -i ref.mp4 -lavfi "pan=mono|c0=0.5*c0-0.5*c1,showspectrumpic=s=1600x300" side.png`),
which removes a mono voice and leaves music and effects. Add a look to
`scripts/looks.py` and a section to `references/looks.md`. Tell the user
what the reference does that this can't.
