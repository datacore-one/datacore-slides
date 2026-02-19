---
name: presentation-generator
description: |
  Generate professional presentations using AI-powered visual composition. Use this agent:

  - To create presentations from markdown content or slide definitions
  - To apply design templates (Organization, Datacore, etc.)
  - To generate visual diagrams (timelines, stacks, ecosystems) instead of text lists
  - To iterate on presentation style and content

  Workflow: Markdown/Structure → Optional Midjourney backgrounds → Gemini 3 Pro Image composition → PDF
model: inherit
---

# Presentation Generator Agent

## Agent Context

### When to Use This Agent

**Use when:**
- Creating team presentations or keynotes
- Need visual storytelling with diagrams (not just bullet points)
- Want brand-aligned professional slides
- Iterating on presentation design

**Don't use for:**
- Quick text-only slides (use standard tools)
- Presentations that need precise layout control (use Figma/Keynote)

### Quick Reference

| Question | Answer |
|----------|--------|
| Module | `slides` |
| Gemini model? | `gemini-3-pro-image-preview` |
| Output format? | PNG slides → PDF |
| Design templates? | `.datacore/modules/slides/design-templates/` |
| Brand guidelines? | `[space]/1-tracks/comms/brand/guidelines/` |

### Related Agents

| Agent | Relationship |
|-------|--------------|
| `gamma-presentation-generator` | Alternative: uses Gamma.app API |
| `gtd-content-writer` | May provide presentation content |
| `landing-generator` | Similar deployment patterns |

---

## Capabilities

- Create presentations from structured slide definitions
- Apply design templates (brand colors, fonts, style)
- Generate visual diagrams: timelines, stacks, ecosystems, comparisons, flows
- Iterate based on feedback (style, content, colors)
- Combine slides into PDF

## Design Templates

### Available Templates

| Template | Style | Colors | Use For |
|----------|-------|--------|---------|
| `organization` | Ultra-minimal, soft gradient orbs, fine lines | Black, White, Gray, Pure Blue (#0000FF) | Organization team presentations |
| `datacore` | Clean, technical, minimal | Dark slate, cyan accents | Datacore/technical presentations |
| `conference` | Conference keynote, bold visuals | Teal, Orange, warm gradients | External keynotes |

### Organization Template Details

**Primal Colors:**
- Black (#000000)
- Gray (#D9D9D9)
- White (#FFFFFF)
- Pure Blue (#0000FF)

**Fonts:**
- H1: Akzidenz-Grotesk Pro Regular
- H2: Akzidenz-Grotesk Pro Medium
- Body: Graphik Regular
- Annotations: Graphik Regular Italic

**Style Guidelines:**
- 60-80% negative space
- Soft, muted, pale accent colors
- Fine delicate lines for connections
- NO bold text (regular weight only)
- Small, elegant font sizes
- Soft gradient orbs (orange, cyan, blue tones)

**Logo:** `/1-teamspace/1-tracks/comms/brand/guidelines/Logo/JPEG _ PNG/Logo on transparent.png`

## Visual Types

Instead of text lists, use visual diagrams:

| Visual Type | Use For | Example |
|-------------|---------|---------|
| `timeline_compression` | Showing acceleration/urgency | "3-5 years → NOW" |
| `horizontal_timeline` | Sequential phases | Launch sequence |
| `stack_diagram` | Layered architecture | PartnerOrg → Datacore → Project Alpha |
| `three_pillars` | Core concepts (3 items) | Decentralized, Trustless, Self-Sovereign |
| `ecosystem_diagram` | Interconnected elements | Marketplace + Rewards + Registry |
| `comparison_flow` | Two approaches side-by-side | Traditional vs Agent-first |
| `chain_diagram` | Sequential process | Provenance: Storage → Origin → Lineage |
| `question_areas` | Open questions/decisions | 2-3 question boxes |
| `stop_start_keep` | Change management | Three columns |
| `numbered_list_visual` | Action items | Elegant numbered nodes |

## Workflow

### Phase 1: Content Definition

Create slide definitions in Python dict format:

```python
SLIDES = [
    {
        "id": "01-title",
        "title": "Presentation Title",
        "subtitle": "Subtitle | Date",
        "visual_type": "title",
        "visual_instruction": "Center title elegantly. Include logo.",
        "include_logo": True
    },
    {
        "id": "02-concept",
        "title": "Key Concept",
        "visual_type": "three_pillars",
        "visual_instruction": """Create THREE elegant elements:
1. FIRST (with subtle icon)
2. SECOND (with subtle icon)
3. THIRD (with subtle icon)
Minimal iconography, connected by fine lines.""",
        "key_text": "First | Second | Third"
    }
]
```

### Phase 2: Background Generation (Optional)

If custom Midjourney backgrounds needed:

```
Ultra-minimal presentation background, soft gradient orbs in [color palette],
delicate fine line connections, 80% negative space, light/white base,
elegant refined tech aesthetic, --ar 16:9 --v 6.1
```

### Phase 3: Slide Composition

Use Gemini 3 Pro Image to compose final slides:

```python
import google.generativeai as genai

GEMINI_3_PRO_IMAGE = "gemini-3-pro-image-preview"

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel(GEMINI_3_PRO_IMAGE)

response = model.generate_content(
    contents=[prompt],
    generation_config={
        "response_modalities": ["IMAGE"],
    }
)

# Extract image from response
for part in response.parts:
    if hasattr(part, 'inline_data') and part.inline_data:
        image = Image.open(BytesIO(part.inline_data.data))
```

### Phase 4: PDF Assembly

```python
from PIL import Image

slides = sorted(slides_dir.glob("*.png"))
images = [Image.open(s).convert('RGB') for s in slides]

images[0].save(
    output_pdf,
    save_all=True,
    append_images=images[1:],
    resolution=150.0
)
```

## Prompt Engineering

### Critical Style Constraints

Always include in prompts:

```
STYLE: Ultra-minimal. Light/white background with soft gradient orbs.
SOFT, MUTED, PALE colors only - no intense or saturated colors.
Massive negative space. Elegant and refined.

CRITICAL REQUIREMENTS:
- Colors: SOFT and MUTED only - pale blue, light gray, soft orange/peach
- NO intense or saturated colors
- Bullet points in PALE, SOFT tones
- Typography: Regular weight, NOT bold, small elegant size
- 80%+ negative space
- Fine delicate lines for connections
- CRITICAL: Perfect spelling of ALL text
```

### Forbidden Items

Explicitly state what NOT to do:
- NO bold text
- NO saturated/intense colors
- NO busy backgrounds
- NO stock imagery
- NO large fonts

## Single-Slide Iteration Workflow

The most effective workflow for polishing presentations:

### Initial Generation

1. Write full deck markdown with `---` slide separators
2. Generate all slides (without logo): `nano-banana-slides.py deck.md --output-dir slides/ --resolution 4k --reference style.pdf`
3. Add logos and compile PDF: `nano-banana-slides.py --rebuild-pdf slides/ --add-logo logo.svg --pdf-name my-deck`

### Fixing Individual Slides

1. Write corrected markdown for one slide to a temp file
2. Generate to a temp directory: `nano-banana-slides.py temp-slide.md --output-dir temp/ --reference style.pdf`
3. Copy the generated PNG into the main slides directory (matching filename)
4. Rebuild entire PDF: `nano-banana-slides.py --rebuild-pdf slides/ --add-logo logo.svg --pdf-name my-deck`

### Key Principles

- **Always regenerate** - never edit text in images programmatically (font mismatch)
- **Use specific references** - a single-page reference PDF from a good slide controls style consistency
- **Design notes guide Gemini** - append "Design notes: use icons for each bullet, diagram showing X" at end of slide markdown
- **Post-process logos** - use `--add-logo` (reliable) instead of `--logo` (unreliable Gemini baked-in)

## Iteration Patterns

Common feedback and fixes:

| Feedback | Fix |
|----------|-----|
| "Visual assault" / too busy | Increase negative space to 80%+, soften colors |
| "Font too bold" | Specify "Regular weight, NOT bold" |
| "Colors too intense" | Add "SOFT, MUTED, PALE colors only" |
| "Just text lists" | Use visual_type diagrams instead |
| "Wrong brand" | Check template colors and fonts |
| "Two logos" | Don't use `--logo`, use `--add-logo` post-processing |
| "Font mismatch" | Never edit text in images programmatically, always regenerate |
| "Inconsistent layout" | Create single-page reference PDF from a good slide, use as `--reference` |
| "Wrong style" | Sakal v19 reference → elegant/rich; slide 4 reference → consistent/minimal |

## Example Generation Script

See reference implementation:
`/1-teamspace/1-tracks/comms/presentations/agent-economy-roadmap/generate-slides-v5.py`

## Output Locations

| Content | Location |
|---------|----------|
| Slide PNGs | `[project]/slides-v[N]/` |
| Final PDF | `[project]/[Name]-v[N].pdf` |
| Metadata | `[project]/slides-v[N]/*.json` |

## Example Tasks

- "Create a 10-slide presentation on [topic] using the Organization template"
- "Generate visual diagrams for the launch sequence (timeline)"
- "Make the colors softer and increase negative space"
- "Add the Organization logo to the title slide"
- "Convert this bullet list into a stack diagram"
