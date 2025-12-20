import { z } from 'zod';
import type { GammaClient } from '../gamma-client.js';

export const getFileUrlsSchema = z.object({
  generationId: z.string()
    .describe('The ID of the gamma generation to get export URLs for'),
});

export type GetFileUrlsParams = z.infer<typeof getFileUrlsSchema>;

export async function getFileUrls(
  client: GammaClient,
  params: GetFileUrlsParams
) {
  const response = await client.getFileUrls(params.generationId);

  return {
    generationId: params.generationId,
    pdfUrl: response.pdf,
    pptxUrl: response.pptx,
    note: 'Export URLs expire. Download promptly after receiving.',
  };
}
