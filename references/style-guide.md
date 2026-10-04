# Style guide

Measured from the reference reel (36.3 s, 720x1280, 30 fps): a creator
presenting an open-source AI video tool. The renderer's defaults reproduce
these numbers at 1080x1920.

## Pacing

- 20 visual cuts in 36 s. Average shot 1.8 s, range about 0.4-5.5 s.
- No pauses in speech. Every breath and gap is cut.
- Graphics take about half the runtime. The presenter is never off screen for
  more than about 5 s.
- Structure:
  - 0-1.4 s: hook. Blurred logo on dark, "AI TOOL" in serif, presenter card below.
  - 1.4-6.5 s: claim, with an animated illustration and serif captions, then
    the product name on a full-screen graphic.
  - 6.5-10 s: social proof. GitHub star counter in split layout, sans captions.
  - 10-16 s: how it works, as a list of roles. Each role appears in sync with
    the word.
  - 16-27 s: features (search, write, generate...) in split layout with UI
    screenshots, then a fast dark b-roll montage of outputs.
  - 27-36 s: talking head into the CTA: "comment 'Video'".

## Layouts

1. **Talk**: presenter full frame. Consecutive talk shots alternate between
   normal and punched in (about 1.15x).
2. **Split**: background (white or near-black `#0d1117`), graphic in the top
   ~40%, caption at ~50% height, presenter in the bottom ~46% inside a card
   with rounded top corners and a soft top edge.
3. **Full graphic**: graphic centered on white, serif caption at ~70% height.
4. **B-roll**: dark full-bleed montage, serif uppercase caption.

## Captions

- One or two words at a time, timed to speech. Each pops in (86% to 100% scale
  over 90 ms).
- **Sans**: Inter ExtraBold, ~78 px at 1080 wide, sentence case as spoken.
  White with a soft shadow on video. Near-black on white backgrounds. Used on
  talking head and on split screens with screenshots.
- **Serif**: Instrument Serif Italic, ~128 px, ALL CAPS. White on dark,
  black on white. Used on illustrations, product name, b-roll.
- Position: ~68% height on talking head, between graphic and card on split.
- CTA: small serif "comment" over a heavy sans quoted keyword with an orange
  glow, held for the last 2-3 s.

## Not reproduced by this skill

- Custom animated mascots and the animated star counter (motion graphics).
  Substitute: screenshots with pop-in, `card` shots, or generated clips.
- The rec-frame overlay with a running timecode on the illustration shot.
- Per-letter caption animation. Captions pop in per chunk instead.
