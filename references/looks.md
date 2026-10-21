# Looks

Four reference reels, four looks. Set one with `"look"` in edit.json. Each
section lists what the reference does (measured from the file), what the
skill reproduces, the sound design, and what to record and ask for.

How the sound notes were made: the voice in these reels is mono and the
music and effects are stereo, so the stereo difference (L-R) isolates the
music and effects layer. Its spectrogram shows when music plays, beat
pulses, chimes and bass hits. This identifies the kind of sound and its
timing, not the specific track. All four reels are mastered to -14 LUFS.

---

## explainer (reference 0, "AI tool explainer", 36 s)

Measured: 20 cuts in 36 s (one every 1.8 s). Word-by-word sans captions on
the talking head, italic serif caps on graphics, split screen with presenter
card, white and dark graphic beats, glowing "comment X" ending. Details in
`style-guide.md`.

Sound: a steady music bed about 20 dB under the voice, with low pulses
roughly every 1.2 s (slow, about 50 bpm or a half-time feel) and whooshes on
graphic cuts.

Skill: layouts `talk`, `split`, `full`, `broll`, `card`; auto whooshes on
graphic cuts; CTA with glow.

Record: one framing, face in the upper third, neutral wall. Bring
screenshots of everything you name (product page, numbers, app UI).

Prompt:
> Edit raw.mp4 into a reel with the reel-editor skill, look "explainer".
> Hook: "<first sentence>". Put assets/<file>.png on screen when I say
> "<phrase>". Numbers as cards. End with comment "<WORD>". Music:
> assets/music.mp3 low. Under 40 seconds.

---

## editorial (reference 1, "I didn't edit a single second", 54 s)

Measured:
- About 27 visual changes in 54 s (one every 2 s), plus 3-4 camera setups (close, medium,
  wide standing shot). The angle changes do much of the pacing.
- Brand colors: dark green `#1d3a2b`, cream `#efe6d2`, gold `#d9c48f`.
  Condensed serif (Instrument Serif) for everything except one heavy sans
  "BIGGER" sticker.
- Opening: presenter cut out over solid green, giant serif words typed in
  *behind* the head ("I DIDN'T EDIT"), then gold italic "Claude did."
- Captions: 3-5 words in a green box, the spoken word bright and the rest
  dimmed (karaoke), at ~70% height.
- A chat input card slides in at the top and the prompt types itself
  ("make it more aesthetic").
- Giant words behind the head again mid-video ("CLAUDE", "HUG", "NEVER").
- Picture-in-picture: other reels, a timeline screenshot, a "0:54" timer card.
- A grade change to show "moody" mid-video.
- Ending: white note "Comment 'EDIT' and I'll send you the walkthrough", a
  comment being typed, a follow card.

Sound:
- Music bed under the whole video, about 20 dB below the voice, with a
  busy hi-hat pattern (pulse about every 0.35 s, roughly 85 bpm half-time).
  Clean, modern, not lo-fi.
- The music drops out for about 2 s around 29-31 s, right as he says "a
  little different". A music stop before a new section.
- Bass hits on reveals at about 19 s, 25 s, 40 s and 43 s (bad take card,
  "moody" grade, "BIGGER captions").
- Typing ticks are likely under the prompt card.

Skill reproduces: cutout over brand color, text behind the head (`"z":
"behind"`), typed titles (`"anim": "type"`), karaoke captions in a box,
prompt card with typing clicks, media cards, "big" sticker, note box, grade,
bass hits on titles (auto in this look). Not reproduced: the follow card
and the comment-reply animation (use a screenshot as a media overlay), the
music stop (cut your music file there, or pass `"music": {"start": ...}`).

Record: 2-3 angles of the same take if you can (phone on tripod plus a wide
shot), darker room with warm lamps, plain top area above your head (the big
words need empty space there). Leave a beat of silence before the hook.

Prompt:
> Edit raw.mp4 into a reel with the reel-editor skill, look "editorial".
> Open on a cutout over the brand green with "<2-3 WORDS>" typed in behind
> my head, then "<short italic line>" in gold. When I say "<phrase>", show a
> prompt card typing "<prompt text>". Put "<WORD>" behind my head when I say
> it. Use assets/<files> as picture-in-picture. Bass hits on the big
> reveals. End with a note "Comment '<WORD>' and I'll send you <thing>".
> Music: assets/music.mp3, cut it out for a second before "<phrase>".

---

## steps (reference 2, "How I edit my storytelling reels", 52 s)

Measured:
- Slow: about 22 visual changes in 52 s (one every 2.4 s), mostly one camera angle. Screen recordings
  filmed off a laptop.
- Two-line header held the whole video: "How I edit my" in white serif over
  "Storytelling Reels" in gold italic serif.
- Step chip under the header ("STEP 1 : Voiceover" ... "STEP 6 : Color
  grade") in a handwritten font on white boxes. Changes with each step.
- Captions: small yellow serif phrases (5-6 words), low on the frame, no
  box, no word pop. Quiet on purpose; the header carries the design.
- Stickers: brand pills (Epidemic Sound, CapCut), a mic photo, past reels in
  the corners with view counts, a profile card.
- Warm grade.

Sound:
- A calm melodic bed (guitar or keys) under the whole video, about 18 dB
  under the voice, slow (about 75 bpm).
- A bright chime at each step change, at about 3, 10, 17, 24, 29, 35 and
  42 s. Seven chimes for six steps plus the intro.
- She says on camera that she uses Epidemic Sound for music and CapCut's
  library for effects.

Skill reproduces: `header` overlay, `chip` overlays with a chime each,
phrase captions, stickers and picture-in-picture as media overlays, warm
grade.

Record: one steady framing, mid-shot, with room above your head for the
header. Say "Step one", "Step two" clearly so the chips can be timed to the
words. Screen-record or film the screens you talk about.

Prompt:
> Edit raw.mp4 into a reel with the reel-editor skill, look "steps".
> Header: "<line 1>" / "<line 2>" for the whole video. A chip for each step
> when I say it: STEP 1 : <name>, STEP 2 : <name>, ... Show
> assets/<logo>.png as a sticker when I mention <brand>. Use
> assets/<screen>.mp4 full screen while I explain step <n>. Calm music
> (assets/music.mp3), a chime on each step. End on "<last line>".

---

## floating (reference 3, "Anime cooking tutorial", 58 s)

Measured:
- Fast: about 40 visual changes in 58 s (one every 1.4 s).
- The presenter is cut out and the room behind them is blurred. Phone
  screen recordings and AI clips float in rounded cards *behind* the
  presenter (head and shoulders overlap the card), with a soft shadow.
- Full-screen phone recordings over the blurred room for the how-to part.
- Title stacked at the start: "Anime Cooking" in heavy rounded yellow sans
  with a dark outline, "Tutorial" in a script/italic serif.
- Captions: one word at a time, heavy rounded sans, pale yellow with a soft
  glow, some words in light blue for emphasis, mid-frame.
- "Comment 'CAPCUT' get prompt" box over the prompt screen; before/after
  pair; brand logo sticker; "comment 'CapCut'" ending in yellow and blue.

Sound:
- Almost no stereo content, so either no music or a very quiet mono bed.
  The voice carries it.
- Short stereo bursts in the first 8 s (whooshes on the intro clip changes)
  and short tonal blips at about 2, 3, 7, 16, 22, 33, 38, 42 and 52 s that
  line up with things popping on screen. Pops and clicks, not a beat.

Skill reproduces: `cutout` layout with `"bg": "blur"`, media cards behind
the presenter with shadow, title + script title, one-word glow captions with
emphasis colors, note box, CTA, pops on media and whooshes on cuts.
Before/after: two media overlays plus two `label` texts.

Record: sit in front of a simple room (the blur hides it anyway), leave
space beside your head for the cards. Screen-record your phone in
portrait. Export the AI clips you show.

Prompt:
> Edit raw.mp4 into a reel with the reel-editor skill, look "floating".
> Cut me out over a blurred background. Title "<Line 1>\n<Line 2>" with
> "<script word>" under it for the first 3 s. Float assets/<clip>.mp4 behind
> my head top-left while I say "<phrase>". Full-screen assets/<screen>.mp4
> for the steps. Emphasize the words <word>, <word> in blue. Note box
> "Comment '<WORD>' get prompt" over the prompt screen. Pops on every card,
> no music. End with comment "<WORD>".

---

## punchy (reference 4, "video editors are cooked", 27 s) - DEFAULT

The full rules for this look, including the six-beat structure and how to
choose stickers for a new script, are in `playbook.md`.

Measured:
- Several camera setups (seated wide, close from below, standing), changing
  every 2-5 s, plus punch-ins.
- Captions in the middle of the frame, white lowercase heavy sans, 2-4 words.
  The key word of each line is on its own line, 2x bigger and yellow
  (`#f3d46a`): "i suck at / **video editing**", "and i'm not / **techy** / at
  all". About one big word every 2-3 s.
- One giant yellow word for the punchline ("cooked.") with sparks.
- Paper and gadget stickers next to the head, each tied to a word:
  dark tool tags ("CapCut / video editor", "Premiere Pro", "DaVinci") as
  each tool is named; invoice receipts "Video editor 1 video ... $150" that
  stack up; a red LED price "$750 / EVERY SINGLE VIDEO".
- Handwritten yellow notes with arrows pointing at his head ("can't edit",
  "not techy") while he says it about himself.
- Proof beat: the video playing in an app window on cream, with a checklist
  card ("Using skill video-edit": transcribed, picked takes, cut, captions,
  sound design, rendered) and a big serif "100% edited".
- Phone mockups of result videos for "results like this".
- Ending: comment bar with "EDIT" typed in, held to the end.
- This reel was made with the `video-edit` skill (its checklist card says so).

Sound:
- No music bed. The voice is alone for most of the reel.
- A 3 s rising noise build (riser, with crackle) from about 1.7 s that lands
  on "cooked." at 4.7 s.
- A short pop or swish each time a sticker appears: about 12 between 8 s
  and 25 s, densest in the tool tags and receipts (15-21 s).

Skill reproduces: two-size captions (`mode: "punch"` with `emphasis`
phrases), giant word (`big` text), all the stickers as generated graphics
(`tag`, `receipt`, `price`, `note`, `checklist`, `stat`, `comment`), phone
cards as media overlays, pops on every sticker, a riser into the giant
word (automatic in this look). Not reproduced: the sparks,
the app window with video playing inside it (use a `split` or a screenshot).

Record: 2-3 framings of the same script (seated, close from below,
standing), mid-tone room. Say tool names and prices out loud; each one gets a
sticker.

Prompt:
> Use the reel-editor skill, look "punchy". Edit my video into a reel under
> [30] seconds. Read what I say and add stickers for the ideas: a tag for
> every tool I name, receipts and a price for anything about cost, a
> handwritten note with an arrow at my head when I talk about myself, a
> checklist card for the process. Big yellow words: [word], [word]. Giant
> "[punchline.]" when I say it. End with a comment bar typing "[WORD]".

---

## steps, storytelling variant (reference 6, "How I script my storytelling reels", 71 s)

Same creator and look as reference 2, used for a long personal story.
Measured:
- Header has three lines: "How I script my" / "Storytelling Reels" (gold
  italic) / "1 video -> 29,518 followers" (small white, the proof). Held all
  71 s.
- One camera angle the whole time. Only about 18 visual changes in 71 s;
  the story carries it.
- Three times the frame shrinks into a rounded card on black for 2-4 s
  (17 s, 43-47 s, 55-59 s) to mark a turn in the story.
- Proof inserts: profile and analytics screenshots in the corners with a
  small handwritten-style label ("*trial reel").
- Captions small white serif; one phrase per beat set larger ("Main
  Character").

Sound: a soft melodic bed under the whole story; chimes at a few beats
(about 7, 14 and 36 s); a low thud each time the frame shrinks.

Skill: `header` with three `lines`; `inset` shots with `"bg": "#000000"`,
`"anim": "shrink"` (thud is automatic); screenshots as media overlays with
a `label` text; `"styles": {"cap_main": {...}}` for the serif captions.

Prompt:
> Use the reel-editor skill, look "steps". Header "[line 1]" / "[line 2]" /
> "[proof line]" for the whole video. Shrink the frame into a card on black
> at the turns of the story: when I say "[words]" and "[words]". Show
> [screenshot.png] in the corner when I talk about [x]. Soft music.

---

## aesthetic (reference 5, "yapping videos", 37.5 s)

Measured:
- About 13 visual changes in 37 s, but the text moves constantly: captions
  sit at the bottom, the middle or the top depending on the shot.
- Captions: white lowercase sans, 2-4 words, with the key word in a big
  cream italic serif that overlaps the small line ("your / *yapping
  videos*", "absolute / *key moments*", "*immediately*"). Font contrast is the
  whole look.
- Edits shown literally as she names them: "crop yourself" shrinks the frame
  to a small box on white, then the box moves up and a hand-drawn title
  ("HOW TO EDIT TIPS") is sketched under it; "center yourself with a
  dynamic grid" puts the frame on a leopard pattern with topic photos
  popping around it.
- A white banner across the top with a word in it ("gatekeep").
- A small meme image pops in once for a joke.
- Ending: "let me know if you need more" top-left, "and save this for your
  next edit :)" at the bottom. A save CTA, not a comment CTA.

Sound: a very quiet steady bed (about 27 dB under the voice) and a couple of
accent hits on inserts (about 3 s and 5.5 s).

Skill: look `aesthetic` (punch captions with a serif key word, `gap` 0.62 so
the lines overlap); `inset` shots on white or on a pattern image (`"bg":
"assets/pattern.jpg"`, `aspect` 1.0 for a square); `title2`/`label` in
handwriting with `"anim": "type"`; `banner` overlays; `caption_y` per shot
to move the captions.

Record: plain wall, mid-shot, a lavalier mic. Name the thing you're
explaining out loud ("crop yourself", "a grid") so the edit can show it.

Prompt:
> Use the reel-editor skill, look "aesthetic". Big serif key words:
> [word], [word], [word]. When I say "[words]", shrink me into a small box
> on white and write "[short title]" by hand under it. When I say
> "[words]", put me in the middle of assets/[pattern].jpg with
> assets/[photos] around me. A white banner with "[word]" when I say it.
> End with "save this for [x]". Very quiet music.

---

## Where to get sounds

- Music: Epidemic Sound (what reference 2 uses), Artlist, CapCut's library,
  or Instagram's own audio picker when you post. Pick by mood and tempo from
  the notes above. Royalty-free sites (Pixabay Music) work for tests.
- Effects: the skill synthesizes whoosh, pop, ding, boom, click and riser.
  They are plain. Library effects (Epidemic Sound, CapCut, Pixabay) sound
  better; put files in assets/ and reference them in `sfx` or an overlay's
  `sfx`.
- Trending audio: if you want a trending sound, add it in Instagram when
  posting and keep the skill's music off, or the two will clash.
