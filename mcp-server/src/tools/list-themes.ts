import { z } from 'zod';
import type { GammaClient } from '../gamma-client.js';

export const listThemesSchema = z.object({
  query: z.string()
    .optional()
    .describe('Search query to filter themes by name'),
  limit: z.number()
    .min(1)
    .max(100)
    .optional()
    .describe('Maximum number of themes to return'),
  after: z.string()
    .optional()
    .describe('Cursor for pagination'),
});

export type ListThemesParams = z.infer<typeof listThemesSchema>;

export async function listThemes(
  client: GammaClient,
  params: ListThemesParams
) {
  const response = await client.listThemes({
    query: params.query,
    limit: params.limit,
    after: params.after,
  });

  return {
    themes: response.data.map(theme => ({
      id: theme.id,
      name: theme.name,
      description: theme.description,
    })),
    hasMore: response.hasMore,
    nextCursor: response.nextCursor,
  };
}
