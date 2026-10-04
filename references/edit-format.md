# edit.json

All paths are relative to the folder that holds `edit.json`. All times are
**output** seconds (after autocut), as printed by `autocut.py`.

```json
{
  "source": "raw/talk.mp4",
  "cut": "work/cut.json",
  "output": "out/reel.mp4",
  "size": [1080, 1920],
  "fps": 30,
  "face_y": 0.33,
  "shots": [
    {"end": 1.5, "layout": "split", "media": "assets/logo.png", "bg": "#0d1117", "caption": "serif"},
    {"end": 3.9, "layout": "talk"},
    {"end": 5.3, "layout": "full", "media": "assets/mascot.png", "bg": "#ffffff"},
    {"end": 6.5, "layout": "card", "title": "62.3k", "sub": "stars on GitHub"},
    {"end": 9.8, "layout": "split", "media": "assets/repo.png"},
    {"end": 12.3, "layout": "talk"},
    {"end": 15.6, "layout": "broll", "media": "assets/demo.mp4", "media_start": 4, "dim": 0.25},
    {"end": null, "layout": "talk"}
  ],
  "captions": {"max_words": 2, "max_chars": 14},
  "cta": {"start": 33.0, "small": "comment", "big": "“Video”", "glow": "#ff7a1a"},
  "music": {"file": "assets/track.mp3", "volume": 0.12, "duck": true},
  "sfx": [{"file": "assets/whoosh.wav", "at": 1.5, "volume": 0.5}],
  "loudness": -14,
  "fonts": {"sans": "Inter ExtraBold", "heavy": "Inter Black", "serif": "Instrument Serif", "dir": null}
}
```

Only `source`, `cut` and `shots` are required.

## Shots

Each shot runs from the previous shot's `end` to its own `end`. The first
starts at 0. The last shot always runs to the end of the reel (use
`"end": null`). If the shots stop early, a talk shot fills the rest.

| layout | what it shows | needs |
|---|---|---|
| `talk` | presenter full frame | - |
| `split` | `media` in the top 40% on `bg`, caption in the middle, presenter in a rounded card in the bottom 46% | `media` optional |
| `full` | `media` centered on `bg`, caption below | `media` |
| `broll` | `media` fills the frame (cropped), optional darkening | `media` |
| `card` | big `title` and optional `sub` on `bg` | `title` |

Per-shot options:

- `zoom` (talk): 1.0 = no zoom. Default alternates 1.0 / 1.15 across talk shots.
- `bg`: hex color. Default `#ffffff` (`#0d1117` for broll). Caption color
  follows it: dark text on light backgrounds, white on dark.
- `caption`: `sans` (Inter, lowercase as spoken), `serif` (italic serif,
  uppercase), or `none`. Defaults: talk/split = sans, full/broll = serif,
  card = none.
- `text`: show this text for the whole shot instead of the transcript words.
- `media`: image (png/jpg/webp) or video. Videos loop if shorter than the shot.
- `media_start`: seconds into a video `media` to start from.
- `anim`: `pop` (default; scale-in and fade over 0.2 s) or `none`.
- `dim` (broll): 0-1 black overlay so captions stay readable.

## cta

A two-line call to action: small serif word over a big word with a colored
glow. Transcript captions are hidden while it is on screen. It can also be a
list of CTAs. `y` (fraction of height, default 0.66) moves it.

## fonts

Bundled fonts (Inter, Instrument Serif; OFL) cover Latin script only. For
Armenian, Cyrillic or other scripts, set `fonts.dir` to a folder with fonts
that cover them and give their family names in `sans`/`heavy`/`serif`
(check names with `fc-scan --format "%{family}\n" font.ttf`).
