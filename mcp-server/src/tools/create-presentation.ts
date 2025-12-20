import { z } from 'zod';
import type { GammaClient } from '../gamma-client.js';

export const createPresentationSchema = z.object({
  inputText: z.string()
    .min(1)
    .max(400000)
    .describe('Content to generate from. Supports text and image URLs. Max 100k tokens (~400k chars). Use \\n---\\n for manual slide breaks.'),

  textMode: z.enum(['generate', 'condense', 'preserve'])
    .describe('How to handle input text: generate (rewrite/expand), condense (summarize), preserve (keep exact)'),

  format: z.enum(['presentation', 'document', 'social', 'webpage'])
    .default('presentation')
    .describe('Output format'),

  numCards: z.number()
    .min(1)
    .max(75)
    .optional()
    .describe('Number of cards/slides. Default 10. Pro: 1-60, Ultra: 1-75'),

  themeId: z.string()
    .optional()
    .describe('Theme ID from your workspace. Use gamma_list_themes to find available themes.'),

  folderIds: z.array(z.string())
    .optional()
    .describe('Folder IDs to save to. Use gamma_list_folders to find available folders.'),

  cardSplit: z.enum(['auto', 'inputTextBreaks'])
    .optional()
    .describe('auto: divide by numCards. inputTextBreaks: divide at \\n---\\n markers'),

  textOptions: z.object({
    amount: z.enum(['brief', 'medium', 'detailed', 'extensive'])
      .optional()
      .describe('Text density per slide'),
    tone: z.string()
      .max(500)
      .optional()
      .describe('Desired tone (e.g., professional, casual, technical)'),
    audience: z.string()
      .max(500)
      .optional()
      .describe('Target audience (e.g., investors, engineers, general public)'),
    language: z.string()
      .optional()
      .describe('Output language code (e.g., en, de, fr). Default: en'),
  }).optional(),

  imageOptions: z.object({
    source: z.enum([
      'aiGenerated', 'pictographic', 'unsplash', 'giphy',
      'webAllImages', 'webFreeToUse', 'webFreeToUseCommercially',
      'placeholder', 'noImages'
    ])
      .optional()
      .describe('Image source. Default: aiGenerated'),
    model: z.string()
      .optional()
      .describe('AI model for generated images (only when source is aiGenerated)'),
    style: z.string()
      .max(500)
      .optional()
      .describe('Image style description'),
  }).optional(),

  exportAs: z.enum(['pdf', 'pptx'])
    .optional()
    .describe('Auto-export format. Get download URL in response.'),

  additionalInstructions: z.string()
    .max(2000)
    .optional()
    .describe('Extra instructions for generation'),
});

export type CreatePresentationParams = z.infer<typeof createPresentationSchema>;

export async function createPresentation(
  client: GammaClient,
  params: CreatePresentationParams
) {
  console.error('[create-presentation] Starting generation...');

  const response = await client.createGeneration({
    inputText: params.inputText,
    textMode: params.textMode,
    format: params.format,
    numCards: params.numCards,
    themeId: params.themeId,
    folderIds: params.folderIds,
    cardSplit: params.cardSplit,
    textOptions: params.textOptions,
    imageOptions: params.imageOptions,
    exportAs: params.exportAs,
    additionalInstructions: params.additionalInstructions,
  });

  console.error('[create-presentation] Response received:', JSON.stringify(response, null, 2));

  const result = {
    success: true,
    gammaId: response.id || 'unknown',
    url: response.url || 'unknown',
    title: response.title || 'unknown',
    creditsUsed: response.creditsUsed || 0,
    exportUrls: response.exportUrls || null,
  };

  console.error('[create-presentation] Returning result:', JSON.stringify(result, null, 2));

  return result;
}
