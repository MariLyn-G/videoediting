---
name: reel-editor
description: Edit raw talking-head footage into a vertical 9:16 Instagram Reel / TikTok / Short. By default uses the "punchy" playbook from a reference reel - six-beat structure (hook, proof, relatable, cost, solution, comment CTA), white lowercase captions with the key word big and yellow, stickers generated from what the speaker says (tool tags, receipts, prices, handwritten notes with arrows, checklists, comment bar), angle changes, riser into the punchline. Also has explainer, editorial, steps and floating looks. Copies the tactics of references, never their content. Use when the user asks to edit, cut, caption or assemble a reel, short, TikTok or vertical video, or to make a video like a reference.
---

# Reel editor

Turns a talking-head recording into a finished 1080x1920 reel, adding the
images the script calls for. Five looks, each measured from a reference
reel. Read
`references/looks.md` first, then `references/edit-format.md`.

Scripts are in `scripts/`. They need `ffmpeg` (with libass), Python 3 and
`pip install numpy`. Transcription needs `pip install faster-whisper`
(model from Hugging Face). Cutouts and text behind the head need
`pip install mediapipe` (model from storage.googleapis.com).

## What this can and can't do

Reliable: silence and retake removal, reframing, word-timed captions in
five styles, layouts, punch-ins, person cutout, text and cards behind the
presenter, typed prompt cards, stickers, title text, synthesized sound
effects, music ducking, loudness to -14 LUFS.

Generated graphics (headless Chrome): tool tags, receipts, price
displays, handwritten notes with arrows, checklist cards, big stats, comment
bars, pills. See `references/edit-format.md`.

Not done: custom motion graphics (animated mascots, counters, follow cards),
music selection, and judging which take is the best performance. Graphics
come from the user, screenshots, the built-in cards and text, or an
image/video generator if one is connected. Say this up front if the user
expects animation.

## Workflow

Work in a folder next to the footage: `assets/` for media, `work/` for
intermediates.

1. **Pick the look.** `punchy` (the default playbook) unless the user names
   another one or sends a different reference ("like the green one" =
   editorial). Don't ask when they didn't specify.

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

5. **Visual plan from the script.** Read the kept transcript as an
   argument, not a word list. Map it onto the playbook's six beats, then
   write a beat list: one line per idea, with its output time, the exact
   words, and the visual. Pick visuals by meaning:
   - a tool, app or brand is named -> `tag` or `pill` (user's logo if given)
   - money, cost, price -> `receipt` (stack several for "every video"),
     `price`
   - the speaker describes themself ("I can't edit", "I'm not techy") ->
     `note` with an arrow pointing at the head
   - a process, steps, "it does X, Y, Z" -> `checklist` with those items
   - a number or percentage -> `stat` or `card`
   - "results like this", "my videos" -> the user's own clips as media cards
   - the punchline word -> giant `big` text
   - "comment X" -> `comment` graphic, held to the end
   - the key word of each line -> `emphasis` (punchy, floating looks)
   Aim for a new visual every 2-3 s in punchy and explainer, 3-5 s in steps.
   Show the beat list to the user before rendering if they asked to review;
   otherwise go straight to the preview. Use real screenshots or files the
   user gave over invented ones, and never invent facts (prices, numbers,
   names) the speaker didn't say.

6. **Plan.** Write `edit.json`. Per look:
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
   - punchy: `talk` shots with punch-ins; one `emphasis` phrase per 2-4
     second line; stickers beside the head (x 0.2-0.3 or 0.7-0.8, y
     0.15-0.3), tilted a few degrees, timed to the word; giant word once.
   Cut and place on word boundaries. Keep text out of the bottom 15% and the
   right 12% (Instagram UI).

7. **Preview.** `python3 scripts/render.py edit.json --preview`, then
   `scripts/contact_sheet.sh out/reel_preview.mp4 work/prev.jpg 0.5` and
   look at it. Check that captions don't cover faces or graphics, behind-head
   text is readable around the head, nothing is cropped, the cutout edge is
   clean. Fix and repeat. The trimmed track and matte are cached between
   renders.

8. **Final.** `python3 scripts/render.py edit.json`. Check with `ffprobe`
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
