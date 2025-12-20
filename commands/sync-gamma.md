# /sync-gamma

Pull presentations from Gamma to keep Datacore in sync.

## Workflow

### Step 1: Check Prerequisites

Verify GAMMA_API_KEY is configured. If not:

```
GAMMA_API_KEY not configured.

Set it in .datacore/env/.env:
  GAMMA_API_KEY=sk-gamma-xxxxxxxx
```

### Step 2: Fetch Recent Presentations

Call Gamma API to list recent generations:
- Compare with local sync state (`.datacore/state/gamma-sync.json`)
- Identify presentations not yet in Datacore

### Step 3: Present Findings

```
Found 2 new presentations since last sync:

1. "Q1 Investor Update" (created Jan 14)
2. "Partner Intro - Acme" (created Jan 13)

Import these to Datacore?
```

If nothing new: "All presentations are synced. Last sync: [timestamp]"

### Step 4: Import

For each new presentation:
- Create metadata file in `presentations/[project]/`
- Download PDF export to `exports/[project]/`
- Update sync state

### Step 5: Follow-up

- "Want to index these slides for reuse?"
- "Create a new presentation?"

## Your Boundaries

**YOU CAN:**
- Sync presentations created via Gamma API
- Download PDF/PPTX exports
- Track sync state across sessions

**YOU CANNOT:**
- Sync presentations created in Gamma web app (API limitation)
- Get slide content from web-created presentations
- Edit presentations in Gamma

**YOU MUST:**
- Warn about the web-created presentation limitation
- Update sync state after successful sync
- Offer to index imported presentations

## Limitations

Due to Gamma API restrictions:
- Only API-created presentations can be synced
- Presentations made in gamma.app web interface cannot be pulled
- No way to retrieve slide content from web-created decks

If you created presentations in the web app, they won't appear here.

## Settings Reference

```yaml
slides:
  auto_export_pdf: true    # Download PDF on sync
```

## Error Handling

**No New Presentations:**
```
All presentations are synced.
Last sync: 2025-01-15 10:30

Nothing new from Gamma API.
```

**API Error:**
```
Gamma API error: [message]

Check your API key and try again.
```

## Related

- `/create-presentation` - Create new presentation
- `/index-presentation` - Index slides for reuse
