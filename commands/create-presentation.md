# Create Presentation

Generate a Gamma presentation using the smart creation wizard.

## Usage

```
/create-presentation [source]
```

**source** (optional):
- File path: `/create-presentation notes/datafund/product-overview.md`
- Topic: `/create-presentation "Investor pitch for Q1"`
- Empty: Interactive wizard mode

## Smart Creation Workflow

### Step 1: Purpose & Context

Ask the user about the presentation purpose:

```
Creating a new presentation...

? What's this presentation for?
  1. Investor meeting
  2. Partner introduction
  3. Product demo
  4. Conference/event talk
  5. Team/internal meeting
  6. Other (describe)

? Who's the audience?
  > [text input]

? Which project is this for?
  > [list projects from presentations/ subdirectories]
```

### Step 2: Template Selection

Offer relevant templates:

```
? Start from a template?
  1. Investor Pitch (15 slides: problem, solution, market, traction, team, ask)
  2. Partner Intro (10 slides: who we are, what we do, collaboration)
  3. Product Demo (12 slides: problem, demo, benefits, CTA)
  4. Blank (start fresh)
```

### Step 3: Slide Library Search

Search for relevant existing slides:

1. Read `presentations/_slides/index.json`
2. Filter by project, audience, and relevant tags
3. Present top matches to user

```
Found relevant slides in your library:

From "Investor Pitch Dec 2024":
  [x] Market Opportunity - $50B TAM analysis
  [x] Competitive Landscape - 5 competitor comparison

From "Partner Intro - Swarm":
  [ ] Technical Architecture - System diagram

? Include these slides? (space to toggle, enter to confirm)
```

### Step 4: Custom Content

If source was provided, transform it. Otherwise ask:

```
? Add content for this presentation:
  1. Enter text/outline
  2. Select a file to convert
  3. Skip (template + slides only)
```

### Step 5: Generate

Combine all elements and call Gamma API:

1. Assemble inputText from:
   - Template structure (if selected)
   - Selected slides from library
   - Custom content
2. Call `gamma_create_presentation` MCP tool
3. Download PDF export
4. Save metadata to `presentations/[project]/`
5. Index new slides

### Step 6: Output

Display results:

```
PRESENTATION CREATED
────────────────────

Title: Investor Pitch - Acme Corp Q1 2025
Slides: 12 total (3 reused, 9 new)

View:     https://gamma.app/docs/abc123
Download: exports/datafund/2025-01-15-acme-pitch.pdf
Saved:    presentations/datafund/2025-01-15-acme-pitch.md

New slides indexed for future reuse.
```

## Quick Mode

If source is provided, skip interactive steps:

```bash
# From file - auto-detect project from path
/create-presentation notes/datafund/product-overview.md

# From topic - minimal prompts
/create-presentation "Q1 investor update"
```

Quick mode still:
- Searches slide library for relevant slides
- Asks for audience if not obvious
- Offers template if applicable

## Configuration

### Environment Variables

Required in `.datacore/env/.env`:
```bash
GAMMA_API_KEY=sk-gamma-xxxxxxxx
```

Optional:
```bash
GAMMA_DEFAULT_THEME=theme-id
GAMMA_DEFAULT_FOLDER=folder-id
```

### Default Behavior

- Format: `presentation` (not document/webpage)
- TextMode: `generate` (rewrite and expand)
- NumCards: Auto-calculated from content
- ExportAs: `pdf` (always export)
- ImageSource: `aiGenerated`

## Output Files

### Presentation Metadata
`presentations/[project]/YYYY-MM-DD-[slug].md`

### PDF Export
`exports/[project]/YYYY-MM-DD-[slug].pdf`

### Slide Index Update
`presentations/_slides/index.json`

## Examples

### Interactive Mode
```bash
/create-presentation
# Walks through full wizard
```

### From Existing Content
```bash
/create-presentation content/blog/2025-01-10-privacy-features.md
# Transforms blog post into presentation
```

### From Topic
```bash
/create-presentation "Product demo for TechCrunch"
# Generates from prompt with template
```

### With Specific Audience
```bash
/create-presentation "Partnership proposal" --audience "Swarm leadership"
# Uses audience context for slide search
```

## Error Handling

### Missing API Key
```
Error: GAMMA_API_KEY not configured.

Set your Gamma API key in .datacore/env/.env:
  GAMMA_API_KEY=sk-gamma-xxxxxxxx

Get your API key from: Settings > API key in Gamma Pro
```

### No Slide Library
```
No slide library found. Creating fresh presentation.

Tip: Run /index-presentation after creating presentations
to build your slide library for future reuse.
```

### API Error
```
Gamma API error: [error message]

Check your API key and credit balance at gamma.app
```

## Related Commands

- `/index-presentation [path]` - Index slides from existing presentation
- `/sync-gamma` - Pull presentations created in Gamma web app
