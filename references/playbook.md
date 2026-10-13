# Default playbook (punchy)

Every reel uses this playbook unless the user names another look. It is
reverse-engineered from the reference reel "video editors are cooked" (27 s).

**Copy the tactics, never the content.** The reference's words, tools,
prices, notes and stickers belong to that video. For a new video, every
image, word and number comes from the new speaker's script, assets and
topic. Two reels made with this playbook should look like the same creator
made them, and should not share a single sticker.

## 1. Structure: six beats

Map the speaker's script onto these beats. Not every script has all six;
keep the order of what exists, and never invent a beat the speaker didn't
say.

| beat | reference timing | what the speaker does | how it's edited |
|---|---|---|---|
| Hook | 0-4.5 s | bold or contrarian claim | wide shot; frame darkens (`dim` 0.4-0.5) as the claim turns; a graphic of the topic in the lower third; the punchline word giant and yellow (`big`), riser into it |
| Proof | 4.5-8.5 s | shows it's real ("this video was...") | `window` layout on cream: the speaker inside an app window, a checklist ticking off one item every ~0.5 s, a big `stat` |
| Relatable | 8.5-14.5 s | self-deprecating, "I'm like you" | new angle (zoom in); handwritten `note`s with arrows pointing at the head, one per claim about themself; one big yellow word per line; a row of result cards for "results like this" |
| Problem / cost | 14.5-21 s | lists the old way, what it costs | new angle; a `tag` pops on each named tool or option as it's said, the last one or two crossed out (`strike`); `receipt`s stack up one per mention; a `price` that climbs with each receipt and is crossed out at the end |
| Solution | 21-23.5 s | "all you need is..." | closest, most energetic shot; the answer word big and yellow |
| CTA | 24-26.5 s | "comment X" | wide shot; `comment` bar slides in and holds; on the last 1.5 s swap to a version with a `reply` bubble |

## 2. Pacing

- A new visual event (sticker, big word, angle change, layout) every 1-2 s.
  Never more than 3 s of plain talking head.
- Change the camera angle at each beat. With one camera, fake it: alternate
  `zoom` between 1.0, 1.2 and 1.35 by beat, with punch-ins inside a beat.
- Remove every pause. Aim for 25-35 s total.

## 3. Captions

- `mode: "punch"`: 2-4 words, lowercase, white, in the middle of the frame
  (y 0.55-0.6), above the hands.
- One `emphasis` word or short phrase per line, roughly every 2-3 s: the word
  that carries the meaning (the punchline, the feeling, the result, the
  answer). It goes big and yellow on its own line, with the rest small above
  and below.
- Never emphasize filler words, never two big words on one line.

## 4. Stickers: choose by meaning

| the speaker... | sticker | placement |
|---|---|---|
| names a tool, app, brand, person | `tag` (title = name, sub = what it is) | beside the head, x 0.2-0.3 or 0.7-0.8, y 0.15-0.3, tilted -6..6 |
| mentions a cost, price, fee, time | `receipt` (stack 2-6, offset each by ~0.03 x/y) and `price` | top half; price above the receipts |
| says something about themself | `note` + arrow pointing at the head | near the head, opposite sides for two notes |
| describes a process or features | `checklist` (ticking: same card with `done` 1, 2, 3...) | left of the presenter or `window` |
| gives a number or percentage | `stat` | top-left |
| says "results", "videos like this" | the user's own clips/screenshots as media cards in a row (`w` 0.14-0.18, radius 24) | top third, staggered pops 0.15 s apart |
| names the topic in the hook | `timeline`-like topic graphic, or the user's screenshot | lower third under the caption |
| asks for a comment | `comment` with the keyword, then with `reply` | lower third, y 0.72-0.78 |

Text on stickers is short (1-4 words, or a number) and taken from what is
said. Prices, numbers and names must be the speaker's own. If a beat has no
concrete noun to show, use a big yellow word or an angle change instead of
an invented sticker.

Vary the design between videos: tilt angles, left/right sides, which
stickers stack. Use the user's brand color as `accent` if they have one.

## 5. Sound

- No music by default. The voice carries it.
- Riser (about 1.2 s) into the giant punchline word, with a low hit on it.
- A pop on every sticker, a whoosh on layout changes (window in and out).
- Loudness -14 LUFS.
- If the user wants music, keep it under -20 dB relative to the voice and
  drop it out for the riser.

## 6. Checklist before rendering the preview

- Does each beat have at least one visual event every 2 s?
- Is every sticker tied to a word said within 0.3 s of its start?
- Are all names, prices and numbers from the transcript?
- Nothing in the bottom 15% or right 12% except the comment bar?
- Is anything copied from the reference's content? Remove it.
