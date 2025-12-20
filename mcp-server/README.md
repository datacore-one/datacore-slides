# Gamma MCP Server

MCP server exposing Gamma.app API for Claude Code.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build:
   ```bash
   npm run build
   ```

3. Configure Claude Code MCP settings:
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

## Tools

| Tool | Description |
|------|-------------|
| `gamma_create_presentation` | Create presentation, document, webpage, or social post |
| `gamma_list_themes` | List available workspace themes |
| `gamma_list_folders` | List workspace folders |
| `gamma_get_file_urls` | Get PDF/PPTX export download URLs |

## API Reference

### gamma_create_presentation

```typescript
{
  inputText: string;      // Content (max 100k tokens)
  textMode: 'generate' | 'condense' | 'preserve';
  format?: 'presentation' | 'document' | 'social' | 'webpage';
  numCards?: number;      // 1-75
  themeId?: string;
  folderIds?: string[];
  cardSplit?: 'auto' | 'inputTextBreaks';
  textOptions?: {
    amount?: 'brief' | 'medium' | 'detailed' | 'extensive';
    tone?: string;
    audience?: string;
    language?: string;
  };
  imageOptions?: {
    source?: 'aiGenerated' | 'unsplash' | 'placeholder' | 'noImages' | ...;
    model?: string;
    style?: string;
  };
  exportAs?: 'pdf' | 'pptx';
  additionalInstructions?: string;
}
```

### gamma_list_themes / gamma_list_folders

```typescript
{
  query?: string;   // Search filter
  limit?: number;   // Max results
  after?: string;   // Pagination cursor
}
```

### gamma_get_file_urls

```typescript
{
  generationId: string;  // Gamma ID from create response
}
```

## Environment

- `GAMMA_API_KEY` - Required. Get from Gamma Settings > API key (Pro account required)
