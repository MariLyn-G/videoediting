"""Style presets ("looks"), one per reference reel. See references/looks.md.

Sizes are in pixels at 1080x1920 and are scaled for other sizes. A style is a
dict of: font, size, color, italic, upper, box (color or None), pad (box
padding), outline, outline_color, shadow, glow (color or None), spacing.
"""

BASE_STYLES = {
    "cap_main": dict(font="Inter ExtraBold", size=78, color="#ffffff", shadow=2.5),
    "cap_alt": dict(font="Instrument Serif", size=128, color="#ffffff", italic=True,
                    upper=True, shadow=2),
    "cap_emph": dict(font="Inter Black", size=124, color="#f3d46a", shadow=3),
    "title": dict(font="Instrument Serif", size=170, color="#ffffff", italic=True, shadow=2),
    "title2": dict(font="Instrument Serif", size=120, color="#ff7a1a", italic=True, shadow=2),
    "big": dict(font="Inter Black", size=170, color="#ffffff", shadow=2),
    "label": dict(font="Inter ExtraBold", size=52, color="#ffffff", shadow=2),
    "chip": dict(font="Inter ExtraBold", size=46, color="#111111", box="#ffffff", pad=14),
    "note": dict(font="Inter ExtraBold", size=50, color="#111111", box="#ffffff", pad=16),
    "header1": dict(font="Instrument Serif", size=64, color="#ffffff", shadow=2),
    "header2": dict(font="Playfair Display", size=84, color="#f0c75e", italic=True, shadow=2),
    "header3": dict(font="Inter Medium", size=40, color="#ffffff", shadow=2),
    "banner": dict(font="Inter ExtraBold", size=56, color="#111111", spacing=-1),
    "headline": dict(font="Inter ExtraBold", size=50, color="#111111", spacing=-1),
    "concept": dict(font="Anton", size=250, color="#f6c518", shadow=3),
    "cta_small": dict(font="Instrument Serif", size=96, color="#ffffff", italic=True, shadow=2),
    "cta_big": dict(font="Inter Black", size=150, color="#ffffff"),
    "card_title": dict(font="Inter Black", size=190, color="#111111"),
    "card_sub": dict(font="Inter ExtraBold", size=64, color="#6b6b6b"),
    "ui": dict(font="Inter Medium", size=40, color="#1c1c1c"),
    "ui_label": dict(font="Inter Medium", size=22, color="#8a8a8a", spacing=3),
}

LOOKS = {
    # Reference 0: AI tool explainer (white/dark graphics, word pop captions).
    "explainer": {
        "captions": dict(mode="pop", max_words=2, max_chars=14, y=0.68),
        "graphic_caption": "alt",
        "accent": "#ff7a1a",
        "brand": "#0d1117",
        "grade": None,
        "styles": {},
    },
    # Reference 1: editorial / magazine. Dark green brand, condensed serif,
    # karaoke captions in a green box, giant words behind the head, typed prompts.
    "editorial": {
        "captions": dict(mode="karaoke", max_words=4, max_chars=26, y=0.705,
                         dim="#9fc2a8"),
        "graphic_caption": "main",
        "accent": "#d9c48f",
        "brand": "#1d3a2b",
        "grade": "eq=contrast=1.06:saturation=0.88:gamma=0.97,"
                 "colorbalance=rs=0.03:gs=0.01:bs=-0.04:rh=0.02:bh=-0.02",
        "styles": {
            "cap_main": dict(font="Instrument Serif", size=66, color="#ffffff",
                             box="#1d3a2b", pad=12),
            "cap_alt": dict(font="Instrument Serif", size=66, color="#ffffff",
                            box="#1d3a2b", pad=12),
            "title": dict(font="Instrument Serif", size=250, color="#efe6d2", upper=True,
                          spacing=-4),
            "title2": dict(font="Instrument Serif", size=130, color="#d9c48f", italic=True),
            "big": dict(font="Inter Black", size=150, color="#efe6d2", box="#1d3a2b", pad=18),
            "label": dict(font="Instrument Serif", size=90, color="#d9c48f", italic=True,
                          box="#1d3a2b", pad=14),
            "note": dict(font="Inter ExtraBold", size=46, color="#111111", box="#ffffff",
                         pad=14),
            "cta_small": dict(font="Inter ExtraBold", size=46, color="#111111",
                              box="#ffffff", pad=14),
            "cta_big": dict(font="Instrument Serif", size=130, color="#efe6d2",
                            italic=True, box="#1d3a2b", pad=16),
        },
    },
    # Reference 2: step-by-step tutorial. Persistent two-line header, step chips,
    # small yellow serif phrase captions, logo stickers and picture-in-picture.
    "steps": {
        "captions": dict(mode="phrase", max_words=6, max_chars=34, y=0.675),
        "graphic_caption": "main",
        "accent": "#f0c75e",
        "brand": "#1a1a1a",
        "grade": "colorbalance=rm=0.04:gm=0.01:bm=-0.04,eq=saturation=1.04:gamma=1.02",
        "styles": {
            "cap_main": dict(font="Instrument Serif", size=56, color="#f5d76e", shadow=2),
            "cap_alt": dict(font="Instrument Serif", size=56, color="#f5d76e", shadow=2),
            "chip": dict(font="Patrick Hand", size=54, color="#111111", box="#ffffff",
                         pad=10),
            "label": dict(font="Inter ExtraBold", size=44, color="#ffffff", shadow=2),
            "note": dict(font="Inter ExtraBold", size=54, color="#ffffff", box="#111111",
                         pad=14),
        },
    },
    # Reference 3: floating screens. Presenter cut out over a blurred copy of the
    # room, phone/app recordings floating behind them, one bold word at a time.
    "floating": {
        "captions": dict(mode="pop", max_words=1, max_chars=12, y=0.60),
        "graphic_caption": "main",
        "accent": "#a9d4ff",
        "brand": "#e9e4da",
        "grade": "eq=brightness=0.015:saturation=1.05",
        "styles": {
            "cap_main": dict(font="Nunito Black", size=96, color="#f4f0a8", glow="#e8e070"),
            "cap_alt": dict(font="Nunito Black", size=96, color="#f4f0a8", glow="#e8e070"),
            "title": dict(font="Nunito Black", size=120, color="#f6f1a6", outline=6,
                          outline_color="#2b2b2b"),
            "title2": dict(font="Playfair Display", size=96, color="#ead7ff", italic=True,
                           outline=4, outline_color="#2b2b2b"),
            "label": dict(font="Nunito Black", size=60, color="#ffffff", shadow=2),
            "note": dict(font="Nunito Black", size=66, color="#f6f1a6", box="#3a3320",
                         pad=12),
            "cta_small": dict(font="Nunito Black", size=90, color="#f4f0a8", glow="#e8e070"),
            "cta_big": dict(font="Nunito Black", size=110, color="#a9d4ff", glow="#7fbfff"),
        },
    },
}


LOOKS["punchy"] = {
    # Reference 4: "video editors are cooked". White lowercase captions with the
    # key word big and yellow, paper/LED stickers, handwritten notes with arrows.
    "captions": dict(mode="punch", max_words=4, max_chars=22, y=0.57),
    "graphic_caption": "main",
    "accent": "#f3d46a",
    "brand": "#151515",
    "grade": "eq=contrast=1.05:saturation=0.88:gamma=0.98",
    "styles": {
        "cap_main": dict(font="Inter ExtraBold", size=62, color="#ffffff", shadow=3,
                         lower=True, spacing=-1),
        "cap_alt": dict(font="Inter ExtraBold", size=62, color="#ffffff", shadow=3,
                        lower=True, spacing=-1),
        "cap_emph": dict(font="Inter Black", size=132, color="#f3d46a", shadow=3,
                         lower=True, spacing=-3),
        "big": dict(font="Inter Black", size=230, color="#f3d46a", shadow=4, spacing=-6),
        "title": dict(font="Inter Black", size=170, color="#ffffff", shadow=4, spacing=-4),
        "title2": dict(font="Caveat", size=96, color="#f3d46a", shadow=2),
        "label": dict(font="Caveat", size=80, color="#f3d46a", shadow=2),
        "note": dict(font="Inter ExtraBold", size=46, color="#ffffff", box="#151515", pad=14),
        "cta_small": dict(font="Inter ExtraBold", size=52, color="#ffffff", shadow=3),
        "cta_big": dict(font="Inter Black", size=120, color="#f3d46a", shadow=3),
    },
}


LOOKS["aesthetic"] = {
    # Reference 5: "yapping videos" editing tips. White sans captions with big
    # cream italic serif key words overlapping them, the frame shrunk into boxes
    # on white or on a pattern with an image grid, a white top banner.
    "captions": dict(mode="punch", max_words=4, max_chars=24, y=0.66, gap=0.62),
    "graphic_caption": "main",
    "accent": "#f4ead2",
    "brand": "#ffffff",
    "grade": "eq=saturation=0.92:gamma=1.02,colorbalance=rm=0.02:bm=-0.02",
    "styles": {
        "cap_main": dict(font="Inter ExtraBold", size=58, color="#ffffff", shadow=2,
                         lower=True, spacing=-1),
        "cap_alt": dict(font="Inter ExtraBold", size=58, color="#ffffff", shadow=2,
                        lower=True, spacing=-1),
        "cap_emph": dict(font="Instrument Serif", size=128, color="#f4ead2", italic=True,
                         shadow=2, lower=True, spacing=-2),
        "big": dict(font="Instrument Serif", size=150, color="#f4ead2", italic=True,
                    shadow=2),
        "title": dict(font="Instrument Serif", size=130, color="#f4ead2", italic=True,
                      shadow=2),
        "title2": dict(font="Caveat", size=110, color="#111111"),
        "label": dict(font="Caveat", size=80, color="#111111"),
        "note": dict(font="Inter ExtraBold", size=46, color="#111111", box="#ffffff", pad=12),
        "cta_small": dict(font="Inter ExtraBold", size=54, color="#ffffff", shadow=2,
                          lower=True),
        "cta_big": dict(font="Instrument Serif", size=120, color="#f4ead2", italic=True,
                        shadow=2),
    },
}


LOOKS["framework"] = {
    # Reference 7: "An Anthropic engineer's advice". Clean and minimal: no
    # captions, a small black headline, each key concept as a full-screen photo
    # with one giant yellow word, quotes over a dimmed frame, a question build.
    "captions": dict(mode="none"),
    "graphic_caption": "none",
    "accent": "#f6c518",
    "brand": "#f4f1ec",
    "grade": None,
    "styles": {
        "cap_main": dict(font="Inter ExtraBold", size=56, color="#ffffff", shadow=2),
        "title": dict(font="Anton", size=250, color="#f6c518", shadow=3),
        "big": dict(font="Anton", size=250, color="#f6c518", shadow=3),
        "label": dict(font="Inter ExtraBold", size=50, color="#111111", spacing=-1),
        "note": dict(font="Inter ExtraBold", size=50, color="#111111", spacing=-1),
        "cta_small": dict(font="Inter ExtraBold", size=52, color="#111111"),
        "cta_big": dict(font="Inter ExtraBold", size=52, color="#111111"),
    },
}

LOOKS["listicle"] = {
    # Reference 8: "4 free plugins". Numbered sections, screen recordings over
    # the presenter, white captions with blue italic serif key words, stat badges.
    "captions": dict(mode="pop", max_words=3, max_chars=20, y=0.52, inline_emph=True),
    "graphic_caption": "main",
    "accent": "#2f7df6",
    "brand": "#f2f3f5",
    "grade": "eq=contrast=1.04:saturation=0.95",
    "styles": {
        "cap_main": dict(font="Inter ExtraBold", size=60, color="#ffffff", shadow=2,
                         lower=True, spacing=-1),
        "cap_alt": dict(font="Inter ExtraBold", size=60, color="#ffffff", shadow=2,
                        lower=True, spacing=-1),
        "cap_emph": dict(font="Instrument Serif", size=70, color="#2f7df6", italic=True),
        "header1": dict(font="Inter ExtraBold", size=62, color="#111111", spacing=-1),
        "header2": dict(font="Instrument Serif", size=80, color="#ffffff", italic=True,
                        box="#2f7df6", pad=8),
        "cta_small": dict(font="Instrument Serif", size=90, color="#ffffff", italic=True),
        "cta_big": dict(font="Inter Black", size=140, color="#ffffff", glow="#3ddc84"),
    },
}

LOOKS["showcase"] = {
    # Reference 9: "write this -> get this". Dark app UI: the typed command on the
    # left, the result on the right, cutting back to the face every second; a
    # dark end card with the comment word underlined and a pill subtitle.
    "captions": dict(mode="pop", max_words=3, max_chars=20, y=0.70),
    "graphic_caption": "main",
    "accent": "#e07a5f",
    "brand": "#1c1c1e",
    "grade": None,
    "styles": {
        "cap_main": dict(font="Inter ExtraBold", size=46, color="#ffffff", box="#111111",
                         pad=10, upper=True),
        "cap_alt": dict(font="Inter ExtraBold", size=46, color="#ffffff", box="#111111",
                        pad=10, upper=True),
        "label": dict(font="Inter ExtraBold", size=44, color="#ffffff", box="#111111",
                      pad=10, upper=True),
        "cta_small": dict(font="Inter Medium", size=80, color="#ffffff"),
        "cta_big": dict(font="Inter Medium", size=80, color="#e07a5f"),
    },
}


def resolve(name, overrides=None):
    """Return (look settings, styles) for a look name with edit.json overrides applied."""
    if name not in LOOKS:
        raise SystemExit(f"unknown look {name!r}; choose from {', '.join(LOOKS)}")
    look = {k: v for k, v in LOOKS[name].items() if k != "styles"}
    styles = {k: dict(v) for k, v in BASE_STYLES.items()}
    for k, v in LOOKS[name]["styles"].items():
        styles[k] = dict(v)
    for k, v in (overrides or {}).items():
        styles.setdefault(k, {}).update(v)
    return look, styles
