---
name: reel-editor
description: Edit raw talking-head footage into a vertical 9:16 Instagram Reel / TikTok / Short in the "AI tool explainer" creator style - tight jump cuts with no dead air, word-by-word pop-in captions, alternating punch-in zooms, split-screen graphics above a presenter card, full-screen graphic and b-roll beats with italic serif captions, and a glowing "comment X" call to action. Use when the user asks to edit, cut, caption or assemble a reel, short, TikTok or vertical video from a recording, or to make a video "like" a reference reel of this kind.
---

# Reel editor

Turns one talking-head recording plus a few graphics or clips into a finished
1080x1920 reel. The style is measured from a reference reel; details are in
`references/style-guide.md`. Read it before planning shots.

Scripts are in `scripts/` next to this file. They need `ffmpeg` (with libass)
and Python 3. Transcription also needs `pip install faster-whisper`.

## What this can and can't do

It does reliably: silence and retake removal, 9:16 reframing, word-timed
captions, layouts, punch-ins, text cards, music ducking, loudness to -14 LUFS.

It does not make motion graphics (the animated mascots in the reference were
made by hand or with another tool). Graphics come from the user, from
screenshots, from the built-in `card` layout, or from an image/video
generator if one is connected (e.g. Higgsfield). Say this up front if the
user expects animated illustrations.

## Workflow

Work in a folder next to the footage, e.g. `reel/`, with `assets/` for media
and `work/` for intermediates.

1. **Inspect the inputs.** `ffprobe` the recording (duration, orientation,
   fps). Look at a contact sheet to find where the face sits vertically:
   `scripts/contact_sheet.sh raw.mp4 work/raw.jpg 5`. Set `face_y` from it
   (fraction of frame height at the eyes; 0.3-0.4 is typical).

2. **Transcribe.** `python3 scripts/transcribe.py raw.mp4 -o work/words.json`.
   Use `--lang` for non-English speech. If transcription can't run, ask the
   user for a transcript or SRT and build `words.json` from it
   (`[{"w","start","end"}]`, source seconds).

3. **Find the reel inside the recording.** Read the transcript. Creators
   usually do several takes; keep the last clean take of each line and drop
   false starts, filler ("um", "so yeah"), and repeated sentences. The reel
   should open on the hook sentence, not on "hey guys". Target 25-45 s.
   Then: `python3 scripts/autocut.py work/words.json -o work/cut.json
   --start N --end M --drop a-b --drop c-d`. It prints the kept transcript
   with **output** timecodes; plan shots against those numbers.

4. **Plan shots.** Write `edit.json` (format in `references/edit-format.md`).
   Rules of thumb from the reference:
   - First 1.5 s: a graphic beat (split or full) with a serif caption of the
     hook. Never open on a plain talking head.
   - Change the shot every 1.2-3 s. Average about 1.8 s.
   - Alternate graphics and talking head. Consecutive talk shots get an
     automatic punch-in on every other one, which hides jump cuts.
   - Put a graphic on every concrete noun the viewer should see: product
     name, numbers, lists ("a researcher, a scriptwriter, an editor"), demos.
   - Numbers get a `card` or a split with a screenshot.
   - Cut on word boundaries. Pick shot `end` times between words, using the
     timecodes autocut printed.
   - End with the CTA on a talking head for the last 2-3 s.
   Gather or make every media file the plan references before rendering. If
   something is missing, use a `card` instead of inventing an asset.

5. **Preview.** `python3 scripts/render.py edit.json --preview` (540x960,
   fast). Then `scripts/contact_sheet.sh out/reel_preview.mp4 work/prev.jpg
   0.5` and look at it. Check: captions don't cover faces or graphics, no
   graphic is cropped, text is readable, the card shows the face, nothing
   sits under the Instagram UI (bottom 15% and right 12% of the frame).
   Fix edit.json and repeat.

6. **Final render.** `python3 scripts/render.py edit.json`. Check the output
   with `ffprobe` (1080x1920, 30 fps, duration as expected) and send the
   user the file plus a contact sheet.

## Writing captions and on-screen text

Captions come from the transcript, 1-2 words at a time, so the words must be
right. Fix transcription errors in `work/words.json` (product names are the
usual problem) before running autocut. Keep the speaker's words; don't
rewrite them. A shot can replace the transcript with its own `text` when the
on-screen words should differ (e.g. a big number).

## When the user gives a new reference reel

Make a contact sheet at 1 frame/s, run scene detection
(`ffmpeg -i ref.mp4 -vf "select='gt(scene,0.12)',showinfo" -f null -`), and
compare cut rate, layouts, caption fonts, sizes and positions with
`references/style-guide.md`. Change the constants at the top of
`scripts/render.py` or the per-shot options to match, and tell the user what
the reference does that this pipeline can't reproduce.
