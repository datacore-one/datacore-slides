#!/usr/bin/env python3
"""
slide_chrome.py — one shared visual language for the deterministic slide renderers.

WHY THIS EXISTS
---------------
render_table_slide.py, render_stats_slide.py and render_flow_slide.py each grew
their own canvas, palette and background. Side by side with the generated slides
they read as a different deck: orbs washed out to invisibility, content floating
in a thin band, and at least one renderer using yellow as an accent when the
design system reserves blue as the only accent colour.

Everything shared lives here so the four typeset slides cannot drift from each
other or from the generated ones again.

CONTRACT
--------
    canvas()                      -> RGBA image with background orbs
    title_block(draw, t, sub)     -> returns the y the content may start at
    caption(draw, text_or_lines)  -> bottom-left caption, one or many lines
    Palette constants             -> INK, BODY, MUTE, ACCENT, ACCENT_SOFT, RULE

The deck's rule: white ground, charcoal type, muted-grey captions, PURE BLUE as
the ONLY accent. Yellow is reserved for the hippocampus highlight and appears
nowhere else.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 3840, 2160

INK         = (26, 29, 36)
BODY        = (42, 47, 58)
MUTE        = (118, 125, 141)
ACCENT      = (26, 86, 219)
ACCENT_SOFT = (219, 231, 253)
ACCENT_EDGE = (150, 185, 246)
RULE        = (222, 226, 234)
PANEL       = (252, 253, 255)
BG          = (255, 255, 255)

MARGIN = 200
CONTENT_TOP = 470          # first y the body of a slide may use
CONTENT_BOTTOM = 1880      # last y the body may use, above the caption band

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"


def font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default(size)


def canvas(variant: int = 0) -> Image.Image:
    """White ground with exactly two soft pastel orbs, corner-anchored and cut off.

    Matched to the generated slides — the previous alpha (~30) rendered as
    effectively nothing at print size, which is what made the typeset slides
    look bare next to the rest of the deck.
    """
    img = Image.new("RGBA", (W, H), BG + (255,))
    # The layer's TRANSPARENT pixels must already carry the orb colour. Blurring
    # a layer whose clear areas are black mixes black into the soft edge and
    # leaves a grey ring around every orb — a premultiplied-alpha artefact that
    # is very visible on a white ground.
    ORB = (206, 222, 250)
    layer = Image.new("RGBA", (W, H), ORB + (0,))
    d = ImageDraw.Draw(layer)
    # The generated slides draw these as DEFINED circles with a soft edge, not
    # washes. Heavy blur is what made the typeset slides look like a different
    # deck, so keep the radius tight.
    # variant lets consecutive typeset slides differ — pixel-identical
    # backgrounds read as a repeated slide rather than a consistent one
    placements = [
        ([-430, -540, 700, 590],                [W - 620, H - 560, W + 430, H + 500]),
        ([-520, H - 700, 560, H + 380],         [W - 520, -600, W + 520, 440]),
        ([W - 760, -520, W + 300, 540],         [-480, H - 480, 520, H + 560]),
    ]
    a, b = placements[variant % len(placements)]
    d.ellipse(a, fill=ORB + (200,))
    d.ellipse(b, fill=ORB + (190,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(26)))
    return img


def tracked(draw, xy, text, fnt, fill, spacing=4):
    """Manual letter-spacing — PIL has no tracking."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def title_block(draw, title: str, subtitle: str = "") -> int:
    """Title, optional subtitle, and a short accent rule. Returns content top y."""
    draw.text((MARGIN, 150), title, font=font(104), fill=INK)
    y = 292
    if subtitle:
        draw.text((MARGIN, y), subtitle, font=font(50), fill=MUTE)
        y += 92
    # short blue rule — the one repeated accent that ties the typeset slides
    # to the generated ones
    draw.line([(MARGIN, y + 34), (MARGIN + 150, y + 34)], fill=ACCENT, width=6)
    return max(CONTENT_TOP, y + 120)


def caption(draw, text) -> None:
    """Bottom-left caption. Accepts a string or a list of lines."""
    if not text:
        return
    lines = text if isinstance(text, list) else [text]
    y = H - 190 - (len(lines) - 1) * 52
    for line in lines:
        draw.text((MARGIN, y), line, font=font(36), fill=MUTE)
        y += 52


def save(img: Image.Image, out) -> None:
    img.convert("RGB").save(out, "PNG")
