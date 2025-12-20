# Sync Gamma

Pull presentations from Gamma to Datacore for tracking.

## Usage

```
/sync-gamma [options]
```

## Options

- `--export` - Download PDF/PPTX for all synced presentations
- `--project [name]` - Only sync to specific project folder

## Behavior

1. **Check API Key** - Verify GAMMA_API_KEY is configured
2. **Read Sync State** - Load `.datacore/state/gamma-sync.json`
3. **List Recent Generations** - Call Gamma API for recent creations
4. **Compare with Local** - Find presentations not yet in Datacore
5. **Create Metadata** - For new presentations
6. **Download Exports** - If --export flag or missing PDF
7. **Update Sync State** - Save new state

## Limitations

Due to Gamma API limitations:
- Only presentations created via API can be synced
- Presentations created in Gamma web app cannot be pulled
- No way to get slide content from web-created decks

## Output

```
SYNCING GAMMA PRESENTATIONS
───────────────────────────

Checking for new presentations...

Found 2 new presentations:

1. "Q1 Investor Update" (2025-01-14)
   → presentations/datafund/2025-01-14-q1-investor.md
   → exports/datafund/2025-01-14-q1-investor.pdf

2. "Partner Intro - Acme" (2025-01-13)
   → presentations/datafund/2025-01-13-acme-partner.md
   → exports/datafund/2025-01-13-acme-partner.pdf

Sync complete. 2 presentations added.
Last sync: 2025-01-15 10:30:00
```

## Sync State

Location: `.datacore/state/gamma-sync.json`

```json
{
  "version": "1.0",
  "last_sync": "2025-01-15T10:30:00Z",
  "presentations": {
    "gamma-id-123": {
      "datacore_path": "presentations/datafund/2025-01-15-pitch.md",
      "gamma_url": "https://gamma.app/docs/...",
      "created": "2025-01-15T08:00:00Z",
      "status": "active"
    }
  }
}
```

## Error Handling

### No API Key
```
Error: GAMMA_API_KEY not configured.
Set your API key in .datacore/env/.env
```

### No New Presentations
```
No new presentations found.
Last sync: 2025-01-15 10:30:00
```

### API Error
```
Gamma API error: [message]
Check your API key and network connection.
```

## Related Commands

- `/create-presentation` - Create new presentation
- `/index-presentation` - Index slides for reuse
