# /create-presentation

Create a Gamma presentation from prompts, files, or templates.

## Workflow

### Step 1: Understand Intent

If invoked with no arguments or unclear intent, ask:

"What would you like to create?"

1. **Investor pitch** - Fundraising deck with problem, solution, traction, ask
2. **Partner intro** - Company introduction for partnerships
3. **Product demo** - Feature walkthrough with benefits
4. **From content** - Transform existing blog post, notes, or outline
5. **Blank** - Start fresh with just a topic

If intent is clear from context (e.g., "create presentation from my blog post about X"), proceed directly.

### Step 2: Gather Details

Ask only what's missing:

- **Audience**: "Who is this presentation for?"
- **Project**: "Which project?" (if multiple exist in presentations/)
- **Content**: If "from content" selected, ask for file path or paste

### Step 3: Search Slide Library

Check `presentations/_slides/index.json` for relevant existing slides:

```
I found some slides you might want to reuse:

From "Investor Pitch Dec 2024":
  - Market Opportunity ($50B TAM analysis)
  - Competitive Landscape (5 competitor comparison)

Include these? (I can also skip the library search)
```

### Step 4: Generate

1. Assemble inputText from template + reused slides + custom content
2. Call `gamma_create_presentation` MCP tool
3. Export PDF automatically
4. Save metadata to `presentations/[project]/`
5. Index new slides for future reuse

### Step 5: Present Results

```
Created: "Investor Pitch - Q1 2025"

View:     https://gamma.app/docs/abc123
Download: exports/datafund/2025-01-15-pitch.pdf
Saved:    presentations/datafund/2025-01-15-pitch.md

12 slides (3 reused, 9 new) - indexed for future reuse.
```

### Step 6: Follow-up

Offer next actions:
- "Want to create another presentation?"
- "Should I open the Gamma link?"
- "Need to make changes? (Note: I'll need to regenerate - Gamma doesn't support editing via API)"

## Your Boundaries

**YOU CAN:**
- Create presentations via Gamma API
- Transform blog posts, notes, outlines into slides
- Reuse slides from the indexed library
- Export PDF/PPTX automatically
- Index new slides for future reuse

**YOU CANNOT:**
- Edit existing Gamma presentations (API limitation)
- Pull slides from web-created presentations
- Guarantee specific visual layouts
- Access external URLs for content

**YOU MUST:**
- Store inputText in metadata for future modifications
- Ask for audience if not specified
- Offer to index new slides
- Warn if API key is missing

## Settings Reference

Configure in `settings.local.yaml`:

```yaml
slides:
  auto_export_pdf: true         # Always export PDF (default: true)
  auto_index_slides: true       # Index new slides (default: true)
  skip_slide_library: false     # Skip reuse suggestions
  default_num_cards: 10         # Default slide count
```

## Error Handling

**Missing API Key:**
```
GAMMA_API_KEY not configured.

Set it in .datacore/env/.env:
  GAMMA_API_KEY=sk-gamma-xxxxxxxx

Get your key from: gamma.app → Settings → API
```

**No Slide Library:**
```
No slide library found - creating fresh presentation.

Tip: After creating, I'll index the slides for future reuse.
```

## Related

- `/index-presentation` - Index slides from existing presentation
- `/sync-gamma` - Pull API-created presentations from Gamma
