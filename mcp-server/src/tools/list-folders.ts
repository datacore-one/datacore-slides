import { z } from 'zod';
import type { GammaClient } from '../gamma-client.js';

export const listFoldersSchema = z.object({
  query: z.string()
    .optional()
    .describe('Search query to filter folders by name'),
  limit: z.number()
    .min(1)
    .max(100)
    .optional()
    .describe('Maximum number of folders to return'),
  after: z.string()
    .optional()
    .describe('Cursor for pagination'),
});

export type ListFoldersParams = z.infer<typeof listFoldersSchema>;

export async function listFolders(
  client: GammaClient,
  params: ListFoldersParams
) {
  const response = await client.listFolders({
    query: params.query,
    limit: params.limit,
    after: params.after,
  });

  return {
    folders: response.data.map(folder => ({
      id: folder.id,
      name: folder.name,
      parentId: folder.parentId,
    })),
    hasMore: response.hasMore,
    nextCursor: response.nextCursor,
  };
}
