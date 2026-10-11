# edit.json

All paths are relative to the folder that holds `edit.json`. All times are
**output** seconds (after autocut), as printed by `autocut.py`.

```json
{
  "look": "editorial",
  "source": "raw/talk.mp4",
  "cut": "work/cut.json",
  "output": "out/reel.mp4",
  "size": [1080, 1920],
  "fps": 30,
  "face_y": 0.33,
  "shots": [
    {"end": 2.4, "layout": "cutout"},
    {"end": 5.1, "layout": "talk"},
    {"end": 8.0, "layout": "split", "media": "assets/repo.png"},
    {"end": null, "layout": "talk"}
  ],
  "overlays": [
    {"type": "text", "style": "title", "text": "I didn't\nedit", "start": 0, "end": 2.4,
     "y": 0.24, "z": "behind", "anim": "type"},
    {"type": "prompt", "label": "to Claude", "text": "make it more aesthetic",
     "start": 5.1, "end": 8.0},
    {"media": "assets/timer.png", "start": 9.0, "end": 11.0, "x": 0.5, "y": 0.2, "w": 0.4}
  ],
  "captions": {"emphasis": ["Claude"]},
  "cta": {"start": 33.0, "small": "comment", "big": "“EDIT”"},
  "music": {"file": "assets/track.mp3", "volume": 0.12, "duck": true, "start": 0},
  "sfx_auto": true,
  "sfx": [{"sound": "boom", "at": 19.2, "volume": 0.5}],
  "loudness": -14
}
```

Only `source`, `cut` and `shots` are required.

## look

`explainer` (default), `editorial`, `steps` or `floating`. Sets caption
style, fonts, colors, grade and which sound effects are added. See
`looks.md`. Override single text styles with `"styles": {"cap_main":
{"size": 72, "color": "#ffffff"}}` (style names are in `scripts/looks.py`).
`"grade"` overrides the look's color grade with an ffmpeg filter string, or
`null` for none.

## Shots

Each shot runs from the previous shot's `end` to its own `end`. The first
starts at 0. The last always runs to the end (use `"end": null`).

| layout | what it shows | needs |
|---|---|---|
| `talk` | presenter full frame | - |
| `cutout` | presenter cut out over `bg`: a color, or `"blur"` for a blurred copy of the room | person matte (automatic) |
| `split` | `media` in the top 40% on `bg`, caption in the middle, presenter card in the bottom 46% | `media` optional |
| `full` | `media` centered on `bg`, caption below | `media` |
| `broll` | `media` fills the frame (cropped) | `media` |
| `card` | big `title` and optional `sub` on `bg` | `title` |

Per-shot options:

- `zoom` (talk, cutout): 1.0 = none. Default alternates 1.0 / 1.15.
- `bg`: hex color or `"blur"` (cutout only).
- `caption`: `main`, `alt` (the look's second caption style; serif caps in
  explainer) or `none`.
- `text`: show this text for the whole shot instead of the transcript words.
- `media`, `media_start`, `anim` (`pop` or `none`), `dim` (broll, 0-1).

## Overlays

Timed elements on top of the shots. Each has `start` and `end` (null = to
the end of the reel). Positions `x`, `y` are the center, as fractions of the
frame width and height.

- `"z": "behind"` puts the element behind the presenter on `talk` and
  `cutout` shots (text behind the head, cards behind the shoulders). This
  computes a person matte once per render (needs mediapipe).
- `anim`: `pop` (default), `fade`, `slide` (rises in), `type` (text only,
  letters appear one by one), `none`.
- `sfx`: a built-in sound name or a file, played at `start`. Overrides the
  automatic one.
- `hide_captions`: true hides transcript captions while it is on screen.

Types:

| type | fields | notes |
|---|---|---|
| `text` | `text`, `style`, `size`, `color` | `\n` stacks lines tightly (`leading`, default 0.86). Styles: `title`, `title2`, `big`, `label`, `note`, `chip`, `header1`, `header2`, `cap_main`, `cap_alt` |
| media | `media`, `w` (fraction of width), `radius` (px at 1080 wide, default 28, 0 = square), `shadow`, `media_start` | image or video. No `type` needed |
| `prompt` | `text`, `label`, `w`, `y`, `cps` (typing speed), `box`, `accent` | chat input card that types the text, with key clicks |
| `header` | `lines` (two strings), `y` | two-line header held for the whole video (steps look) |
| `chip` | `text`, `y` | boxed label, e.g. "STEP 1 : Voiceover"; chime on entry |
| `note` | `text`, `y` | boxed note, e.g. "Comment 'EDIT' and I'll send it" |

## captions

From the look; any key can be overridden:

- `mode`: `pop` (1-2 words, scale-in), `karaoke` (3-5 words, spoken word
  bright, rest `dim`), `phrase` (5-6 words, fade-in).
- `max_words`, `max_chars`, `y`, `dim`.
- `emphasis`: list of words shown in the look's accent color.

## Sound

- `music`: `file`, `volume` (0.08-0.15 under speech), `duck` (lower it while
  you talk), `start` (seconds into the track). Fades in and out.
- `sfx_auto` (default true): whooshes on graphic cuts, pops on media and
  notes, chimes on chips and the CTA, typing clicks on prompts, bass hits on
  titles in the editorial look.
- `sfx`: extra sounds, `{"sound": name or file, "at": seconds, "volume"}`.
  Built-in names: `whoosh`, `pop`, `ding`, `boom`, `click`, `riser`.
- `loudness`: target LUFS, default -14 (what all four references measure).

## cta

A small line over a big word: `start`, `end`, `small`, `big`, `glow`
(color, or leave out for the look's default), `y`.

## Other

- `matte_model`: `multiclass` (default, cleaner hair) or `fast`.
- `fonts`: `{"dir": "my-fonts"}` to add fonts for other scripts (Armenian,
  Cyrillic); then set style fonts with `styles`.
