# Banking-deck typography preset for nano-banana

Reusable `design_system` block + model recommendation for bank-grade, information-dense decks.

**Solves the long-standing problem of Gemini rendering text too large.**

## How to use

Paste the `design_system` block below into the frontmatter of any nano-banana slide markdown source. Run with `--model gemini-3-pro-image-preview` (Pro, not Flash) for production decks. Pro respects typography directives much better than Flash.

```bash
python3 .datacore/modules/slides/scripts/nano-banana-slides.py source.md \
  --output-dir ./slides-out \
  --model gemini-3-pro-image-preview \
  --reference path/to/style-reference.pdf \
  --resolution 4k
```

## The directive (paste verbatim into frontmatter `design_system:`)

```yaml
design_system: |
  Datafund "Data Business" visual language. Light, editorial, restrained.

  TYPOGRAPHY — CRITICAL (zero tolerance):
  - This is a printed banking proposal — TEXT MUST BE SMALL AND TIGHT.
  - Reference standard: a Bloomberg terminal, a Financial Times print spread, a McKinsey report.
  - NOT a TED-style poster. NOT a marketing banner. NOT a conference slide. NOT a magazine cover.
  - Slide titles: rendered in 36-PIXEL Helvetica Neue, charcoal #1A1A1A. NOT large. NOT a hero headline.
  - Body text and bullet content: rendered in 18-PIXEL Helvetica Neue, mid-charcoal #333. TINY. DENSE.
  - Subtitles: rendered in 22-PIXEL Helvetica Neue, muted grey #555.
  - Cover and "One more thing" titles may be larger (~60-PIXEL) for impact only.
  - The eye should see 60-70% WHITE SPACE on every slide. Text occupies maximum 30% of canvas area.
  - Bullet markers: 8-PIXEL pure-blue filled squares. SMALL.
  - DO NOT enlarge text. DO NOT use poster typography. DO NOT use marketing typography.
  - When in doubt, render text SMALLER than expected.

  LAYOUT:
  - Body slides are STRICT TWO-COLUMN. Left ≈55% width: title + 3-4 short bullets in 18pt.
  - Right ≈40% width: single geometric diagram, vertically centred.
  - Cover and dedicated visual slides may use single-column.
  - White background. Helvetica Neue regular only. No bold. No italic except quotes.
  - Pure blue (#0066FF) for bullet markers, hairline rules, arrowheads.
  - Pure blue NEVER used for titles.

  BULLETS:
  - Bullet marker: 8-pixel pure-blue filled squares.
  - Bullet lines short — one phrase each, no wrapping past one soft line break.

  DIAGRAMS:
  - Geometric, line-based, no shading, no 3D.
  - Soft pastel orbs (peach, lavender, sky-blue) and thin wave lines may sit subtly behind.
  - Diagrams may have small in-diagram labels — these are not slide text.

  Compact, restrained, information-dense — like a Financial Times two-page spread.

  ZERO TOLERANCE:
  - Render numbers exact. Never render layout instructions, "Visual:", "logo", or any meta text.
  - DO NOT exceed the typography sizes above.
```

## Why this works (and why simpler prompts don't)

Gemini interprets typography prompts as *guidance*, not *constraints*. Saying "18px body" alone is ignored. The fixes that move the needle:

1. **Model = Pro, not Flash.** `gemini-3-pro-image-preview` respects text-size guidance materially better than `gemini-3.1-flash-image-preview`. Flash trains toward poster-style typography by default.

2. **Comparators Gemini knows.** "Bloomberg terminal", "Financial Times print spread", "McKinsey report" are concrete visual references Gemini has training data for. They constrain its interpretation more than abstract "small" or "tight" do.

3. **Negative anchors.** Explicitly listing what the deck must NOT look like ("NOT a TED-style poster", "NOT a marketing banner") rules out the default training bias toward conference-slide typography.

4. **Whitespace ratio as a constraint.** "60-70% white space" forces Gemini to leave the canvas mostly empty, which forces text to occupy a smaller share.

5. **Per-slide TYPOGRAPHY ENFORCEMENT line.** Repeat the directive at the END of each slide's `Visual:` block. Gemini weights instructions closer to the image generation step more heavily.

6. **Pixel-specific units.** "36 pixel" + "18 pixel" are more constraining than "small" or "compact". Gemini parses pixels as a concrete unit.

## Validated 2026-06-04

Used to generate the 30-slide Lloyds Banking Group proposal v42. Pro model + this directive produced FT-spread density typography across all slides. Prior runs with Flash + simpler prompts produced "visual assault" poster-style typography.
