---
name: sync-gamma
description: sync-gamma command
recall:
  # DIP-0029 default — engrams scoped to this command + tag-matched.
  scopes:
    - command:sync-gamma
  tags:
    - sync-gamma
---

# /sync-gamma

## Command Context

### When to Reference Slides Module

**Always reference when:**
- User wants to sync presentations from Gamma cloud
- Checking for new presentations created via API
- User mentions pulling or syncing presentations
- Maintaining consistency between Gamma and Datacore

**Key decisions the module informs:**
- Which presentations are new since last sync
- Whether presentations can be pulled (API-created only)
- Where to store synced presentation metadata and PDFs
- Whether to auto-index synced presentations

### Quick Reference

| Question | Answer |
|----------|--------|
| What can be synced? | Only API-created presentations, not web-created |
| Where is sync state stored? | `.datacore/state/gamma-sync.json` |
| What gets downloaded? | Metadata file and PDF export |
| Can I sync web-created decks? | No (API limitation), only CLI/API-created presentations |

### Agents This Command Invokes

| Agent | Purpose |
|-------|---------|
| (None directly) | Uses Gamma API via MCP tools for listing and downloading |

### Integration Points

- **Gamma API** - MCP tool for listing generations and exports
- **Sync state** - `.datacore/state/gamma-sync.json` tracks last sync
- **Presentation storage** - `presentations/{project}/` and `exports/{project}/`
- **/index-presentation** - Can be called after sync to index new slides

---

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
