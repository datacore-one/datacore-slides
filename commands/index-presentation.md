# /index-presentation

Index slides from a presentation for future reuse.

## Workflow

### Step 1: Understand Intent

If invoked with no path, ask:

"Which presentation would you like to index?"

- List recent presentations from `presentations/` that aren't indexed yet
- Or accept a file path directly

If path is provided, proceed directly.

### Step 2: Validate

Check the presentation file:
- Exists and is readable
- Has `## Source InputText` section (required for indexing)
- Note if already indexed (offer to re-index)

### Step 3: Extract Slides

Parse the inputText by `---` separators:
- Extract title and content for each slide
- Auto-generate tags from content keywords
- Include metadata (project, audience) from frontmatter

### Step 4: Update Index

Add slides to `presentations/_slides/index.json`:

```
Indexing: presentations/datafund/2025-01-15-pitch.md

Extracted 12 slides:
  1. Title Slide - [title, datafund]
  2. Problem Statement - [problem, data-ownership, privacy]
  3. Market Opportunity - [market, TAM, investor]
  ...

Added to slide library. These slides can now be reused in future presentations.
```

### Step 5: Follow-up

- "Want to index another presentation?"
- "Run /create-presentation to use these slides"

## Your Boundaries

**YOU CAN:**
- Index slides from any presentation with Source InputText
- Auto-generate tags from content
- Re-index to update existing entries
- Batch index multiple presentations

**YOU CANNOT:**
- Index presentations without Source InputText section
- Index web-created Gamma presentations (no inputText available)
- Modify the original presentation file (except marking as indexed)

**YOU MUST:**
- Preserve existing slide IDs when re-indexing
- Mark presentation as `slides_indexed: true` in frontmatter
- Warn if Source InputText is missing

## Settings Reference

```yaml
slides:
  auto_index_slides: true    # Auto-index after /create-presentation
```

## Error Handling

**File Not Found:**
```
Presentation not found: [path]

Check the path and try again, or run /create-presentation first.
```

**No InputText:**
```
This presentation doesn't have a Source InputText section.

Only presentations created via /create-presentation can be indexed.
Web-created Gamma presentations can't be indexed (API limitation).
```

**Already Indexed:**
```
This presentation is already indexed (12 slides).

Re-index to update? This will refresh tags and content.
```

## Related

- `/create-presentation` - Create new presentation (auto-indexes)
- `/sync-gamma` - Pull presentations from Gamma
