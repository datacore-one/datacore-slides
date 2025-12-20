#!/usr/bin/env node
/**
 * Gamma MCP Server
 * Exposes Gamma.app API as MCP tools for Claude Code
 */

import { config } from 'dotenv';
import { join } from 'path';
import { homedir } from 'os';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { GammaClient, GammaApiError } from './gamma-client.js';
import {
  createPresentationSchema,
  createPresentation,
  listThemesSchema,
  listThemes,
  listFoldersSchema,
  listFolders,
  getFileUrlsSchema,
  getFileUrls,
} from './tools/index.js';

// Load environment from datacore .env file
const envPath = join(homedir(), 'Data', '.datacore', 'env', '.env');
config({ path: envPath });

// Get API key from environment
const apiKey = process.env.GAMMA_API_KEY;
if (!apiKey) {
  console.error('Error: GAMMA_API_KEY environment variable is required');
  console.error(`Checked: ${envPath}`);
  process.exit(1);
}

// Initialize Gamma client
const gammaClient = new GammaClient({ apiKey });

// Create MCP server
const server = new McpServer({
  name: 'gamma-mcp-server',
  version: '1.0.0',
});

// Helper to format tool responses
function formatResponse(data: unknown): { content: Array<{ type: 'text'; text: string }> } {
  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify(data, null, 2),
    }],
  };
}

// Helper to handle errors
function handleError(error: unknown): { content: Array<{ type: 'text'; text: string }>; isError: true } {
  let message: string;

  if (error instanceof GammaApiError) {
    message = `Gamma API Error (${error.statusCode}): ${error.apiMessage}`;
  } else if (error instanceof Error) {
    message = error.message;
  } else {
    message = String(error);
  }

  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify({ error: message }, null, 2),
    }],
    isError: true,
  };
}

// Register tools
server.tool(
  'gamma_create_presentation',
  'Create a presentation, document, webpage, or social post using Gamma.app AI. ' +
  'Input text is transformed based on textMode: generate (expand), condense (summarize), or preserve (keep exact). ' +
  'Returns the Gamma URL and optional export download links.',
  createPresentationSchema.shape,
  async (params) => {
    try {
      const result = await createPresentation(gammaClient, params as Parameters<typeof createPresentation>[1]);
      return formatResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }
);

server.tool(
  'gamma_list_themes',
  'List available themes from your Gamma workspace. Use the returned theme IDs with gamma_create_presentation.',
  listThemesSchema.shape,
  async (params) => {
    try {
      const result = await listThemes(gammaClient, params as Parameters<typeof listThemes>[1]);
      return formatResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }
);

server.tool(
  'gamma_list_folders',
  'List available folders in your Gamma workspace. Use folder IDs with gamma_create_presentation to organize generated content.',
  listFoldersSchema.shape,
  async (params) => {
    try {
      const result = await listFolders(gammaClient, params as Parameters<typeof listFolders>[1]);
      return formatResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }
);

server.tool(
  'gamma_get_file_urls',
  'Get PDF and PPTX download URLs for a previously created gamma. Note: URLs expire, download promptly.',
  getFileUrlsSchema.shape,
  async (params) => {
    try {
      const result = await getFileUrls(gammaClient, params as Parameters<typeof getFileUrls>[1]);
      return formatResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }
);

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Gamma MCP Server started');
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
