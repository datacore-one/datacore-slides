# Index Presentation

Index slides from an existing presentation for future reuse.

## Usage

```
/index-presentation [path]
```

**path** - Path to presentation metadata file

## Example

```bash
/index-presentation presentations/datafund/2025-01-15-investor-pitch.md
```

## Behavior

1. **Read Presentation** - Load metadata file
2. **Parse InputText** - Split by `---` separators
3. **Extract Slides** - Get title and content for each
4. **Generate Tags** - Auto-tag based on content
5. **Update Index** - Add to `presentations/_slides/index.json`
6. **Mark Indexed** - Update `slides_indexed: true` in metadata

## Output

```
INDEXING PRESENTATION
─────────────────────

Reading: presentations/datafund/2025-01-15-investor-pitch.md

Extracting slides...

Slide 1: Title - Investor Pitch Q1 2025
  Tags: [title, investor, q1]

Slide 2: Problem Statement
  Tags: [problem, data-ownership, privacy]

Slide 3: Market Opportunity
  Tags: [market, TAM, opportunity, investor]

...

Indexed 12 slides to presentations/_slides/index.json

Presentation marked as indexed.
```

## Slide Index Format

Each indexed slide:
```json
{
  "id": "slide-uuid",
  "source_presentation": "datafund/2025-01-15-investor-pitch.md",
  "slide_number": 3,
  "title": "Market Opportunity",
  "content": "[inputText section content]",
  "tags": ["market", "TAM", "opportunity"],
  "audience": "investors",
  "project": "datafund",
  "created": "2025-01-15"
}
```

## Tag Generation

Tags are generated from:
- Slide title keywords
- Common terms in content
- Audience from presentation metadata
- Project from path

## Re-indexing

Running on an already-indexed presentation:
- Updates existing slide entries
- Adds any new slides
- Removes slides no longer present

## Error Handling

### File Not Found
```
Error: Presentation not found: [path]
Check the path and try again.
```

### No InputText
```
Error: No Source InputText section found.
Presentations must include the original inputText to be indexed.
```

### Already Indexed
```
Presentation already indexed (12 slides).
Run again to re-index with updated content.
```

## Batch Indexing

To index all presentations:
```bash
# Use shell loop
for f in presentations/**/*.md; do
  /index-presentation "$f"
done
```

## Related Commands

- `/create-presentation` - Create new presentation (auto-indexes)
- `/sync-gamma` - Pull presentations from Gamma
