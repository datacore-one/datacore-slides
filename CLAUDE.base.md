# slides Module Instructions

This file provides guidance for AI agents working with the slides module.

## Overview

The slides module provides visual content generation:

**Gamma.app Integration:**
- **Create** - Generate presentations from prompts or existing content
- **Reuse** - Build on previous slides via indexed slide library
- **Export** - Download PDF/PPTX for sharing

**Nano Banana (Gemini Image Generation):**
- **Generate images** - Create any image from text prompts
- **Slide backgrounds** - Generate continuous panoramic backgrounds
- **Profile pictures** - Bot avatars, logos, icons
- **Presentation slides** - Full slide images with content

## Architecture

**MCP Server** (`mcp-server/`) provides tools:
- `gamma_create_presentation` - Create new presentations
- `gamma_list_themes` - List available themes
- `gamma_list_folders` - List workspace folders
- `gamma_get_file_urls` - Get export download URLs

**Agents** automate workflows:
- `gamma-presentation-generator` - Main creation agent
- `gamma-slide-indexer` - Index slides for reuse

**Commands** for interactive use:
- `/create-presentation` - Smart creation wizard
- `/index-presentation` - Index existing deck
- `/sync-gamma` - Pull from Gamma

## Storage Structure

Presentations organized by project/space:

```
[space]/
├── presentations/                # Presentation library
│   ├── _slides/                 # Indexed slide sections
│   │   └── index.json           # Searchable slide index
│   ├── datafund/                # Project: Datafund
│   │   └── 2025-01-investor-pitch.md
│   └── project-x/               # Project: X
│       └── 2025-01-demo.md
└── exports/                      # Downloaded files
    └── datafund/
        └── 2025-01-investor-pitch.pdf
```

## Presentation Metadata

Each presentation stored as markdown with frontmatter:

```markdown
---
type: presentation
title: Datafund Investor Pitch Q1 2025
gamma_id: abc123
gamma_url: https://gamma.app/docs/...
pdf_url: exports/datafund/2025-01-investor-pitch.pdf
project: datafund
audience: investors
template: investor-pitch
created: 2025-01-15
slides_indexed: true
---

# Datafund Investor Pitch Q1 2025

**View**: [Gamma URL]
**Download**: [PDF]

## Source InputText

[Full inputText stored here for reuse/modification]

## Slides

1. Title slide
2. Problem statement
3. Market opportunity (indexed)
...
```

## Slide Index

Slides indexed for reuse in `presentations/_slides/index.json`:

```json
{
  "slides": [
    {
      "id": "slide-001",
      "source_presentation": "datafund/2025-01-investor-pitch.md",
      "slide_number": 3,
      "title": "Market Opportunity",
      "content": "[inputText section]",
      "tags": ["market", "TAM", "investor"],
      "audience": "investors",
      "project": "datafund",
      "created": "2025-01-15"
    }
  ]
}
```

## Smart Creation Workflow

When creating presentations, the workflow is:

1. **Purpose & Context** - Ask about meeting type, audience, project
2. **Template Selection** - Choose from investor-pitch, partner-intro, product-demo, or blank
3. **Slide Suggestions** - Search slide index for relevant existing slides
4. **Custom Content** - Add occasion-specific content
5. **Generate** - Combine and call Gamma API
6. **Index** - Add new slides to library

## Content Transformation

### Blog Post to Presentation
```
Title → presentation title
H2 headings → slide breaks (use --- separator)
Introduction → opening card
Conclusion → closing card
```

### Outline to Presentation
```
Use textMode: preserve and cardSplit: inputTextBreaks
Each numbered item → card
```

### Existing Slides to Presentation
```
Retrieve from _slides/index.json
Concatenate with --- separators
```

## Task Tags

| Tag | Agent | Action |
|-----|-------|--------|
| `:AI:presentation:` | gamma-presentation-generator | Create presentation |
| `:AI:presentation:index:` | gamma-slide-indexer | Index slides for reuse |

## Nano Banana (Gemini Image Generation)

Generate images using Google's Gemini models. Requires `GEMINI_API_KEY`.

**Available models:**
- `gemini-2.5-flash-image` - Fast, good quality (recommended)
- `gemini-2.5-flash-image-preview` - Preview version
- `gemini-3-pro-image-preview` - Highest quality, slower

**Scripts:**
- `scripts/nano-banana-slides.py` - Generate full presentation slides from markdown
- `scripts/nano-banana-backgrounds.py` - Generate tiling panoramic backgrounds

**Quick image generation (inline):**
```python
import google.generativeai as genai
from PIL import Image
from io import BytesIO

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash-image')

response = model.generate_content(
    contents=["Your prompt here"],
    generation_config={"response_modalities": ["IMAGE"]}
)

for part in response.parts:
    if hasattr(part, 'inline_data'):
        image = Image.open(BytesIO(part.inline_data.data))
        image.save('output.png')
```

**Use cases:**
- Profile pictures / avatars
- Presentation slide images
- Blog post hero images
- Social media graphics
- Icons and logos

### Nano Banana Iteration Workflow

Proven workflow for high-quality slide decks:

1. **Write deck markdown** with `---` separators between slides
2. **Generate all slides**: `nano-banana-slides.py deck.md --output-dir slides/ --resolution 4k --reference style.pdf`
3. **Add logos and compile**: `nano-banana-slides.py --rebuild-pdf slides/ --add-logo logo.svg --pdf-name my-deck`
4. **Iterate single slides**: write temp markdown → generate to temp dir → copy PNG to slides dir → rebuild PDF
5. **Design notes in markdown**: append "Design notes: ..." to guide Gemini on icons, diagrams, layout
6. **Never use `--logo` flag** (unreliable Gemini baked-in logos) — always use `--add-logo` for post-processing

**Important patterns:**
- Never programmatically edit text in generated images (font mismatch) — always regenerate
- Use a single good slide as `--reference` PDF for style consistency across the deck
- Sakal v19 reference produces rich, icon-heavy, elegant results

## Environment Variables

Located in `.datacore/env/.env`:

```bash
GAMMA_API_KEY=sk-gamma-xxxxxxxxxxxxxxxx
GAMMA_DEFAULT_THEME=              # Optional
GAMMA_DEFAULT_FOLDER=             # Optional
GEMINI_API_KEY=AIza...            # For Nano Banana image generation
```

## MCP Server Setup

Add to Claude Code MCP config:

```json
{
  "mcpServers": {
    "gamma": {
      "command": "node",
      "args": ["/path/to/.datacore/modules/gamma/mcp-server/dist/index.js"],
      "env": {
        "GAMMA_API_KEY": "sk-gamma-xxxxxxxx"
      }
    }
  }
}
```

## API Limitations

| Limitation | Workaround |
|------------|------------|
| No edit API | Store inputText, recreate with modifications |
| Can't pull slides from web-created decks | Index slides from API-created presentations only |
| Export URLs expire | Download immediately after generation |

## Templates

Templates provide structure for common presentation types:

- `templates/investor-pitch.md` - 15 slides: problem, solution, traction, team, ask
- `templates/partner-intro.md` - 10 slides: who we are, what we do, collaboration
- `templates/product-demo.md` - 12 slides: problem, demo, benefits, CTA

## Knowledge Feedback

After presentation creation:
1. Index slides to `_slides/index.json`
2. Store full inputText in presentation metadata
3. Export PDF to `exports/` for archival
