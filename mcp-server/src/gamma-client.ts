/**
 * Gamma API Client
 * Wrapper for Gamma.app public API v1.0
 */

// Types
export type Format = 'presentation' | 'document' | 'social' | 'webpage';
export type TextMode = 'generate' | 'condense' | 'preserve';
export type TextAmount = 'brief' | 'medium' | 'detailed' | 'extensive';
export type ImageSource = 'aiGenerated' | 'pictographic' | 'unsplash' | 'giphy' |
  'webAllImages' | 'webFreeToUse' | 'webFreeToUseCommercially' | 'placeholder' | 'noImages';
export type CardSplit = 'auto' | 'inputTextBreaks';
export type ExportFormat = 'pdf' | 'pptx';
export type PresentationDimensions = 'fluid' | '16x9' | '4x3';
export type DocumentDimensions = 'fluid' | 'pageless' | 'letter' | 'a4';
export type SocialDimensions = '1x1' | '4x5' | '9x16';
export type AccessLevel = 'noAccess' | 'view' | 'comment' | 'edit' | 'fullAccess';

export interface TextOptions {
  amount?: TextAmount;
  tone?: string;        // max 500 chars
  audience?: string;    // max 500 chars
  language?: string;    // default 'en'
}

export interface ImageOptions {
  source?: ImageSource;
  model?: string;       // only when source is aiGenerated
  style?: string;       // max 500 chars
}

export interface CardOptions {
  dimensions?: PresentationDimensions | DocumentDimensions | SocialDimensions;
  headerFooter?: {
    position: 'topLeft' | 'topRight' | 'topCenter' | 'bottomLeft' | 'bottomRight' | 'bottomCenter';
    type: 'text' | 'image' | 'cardNumber';
    content?: string;
  };
}

export interface SharingOptions {
  workspaceAccess?: AccessLevel;
  externalAccess?: Exclude<AccessLevel, 'fullAccess'>;
  emailOptions?: {
    recipients: string[];
    access: Exclude<AccessLevel, 'noAccess'>;
  };
}

export interface GenerateParams {
  inputText: string;                    // required, max 100k tokens
  textMode: TextMode;                   // required
  format?: Format;                      // default: presentation
  themeId?: string;
  numCards?: number;                    // 1-60 (Pro) or 1-75 (Ultra)
  cardSplit?: CardSplit;                // default: auto
  additionalInstructions?: string;      // max 2000 chars
  folderIds?: string[];
  exportAs?: ExportFormat;
  textOptions?: TextOptions;
  imageOptions?: ImageOptions;
  cardOptions?: CardOptions;
  sharingOptions?: SharingOptions;
}

export interface GenerateResponse {
  id: string;
  url: string;
  title: string;
  creditsUsed: number;
  exportUrls?: {
    pdf?: string;
    pptx?: string;
  };
}

export interface Theme {
  id: string;
  name: string;
  description?: string;
  previewUrl?: string;
}

export interface Folder {
  id: string;
  name: string;
  parentId?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  hasMore: boolean;
  nextCursor?: string;
}

export interface GammaClientConfig {
  apiKey: string;
  baseUrl?: string;
}

export class GammaClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(config: GammaClientConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://public-api.gamma.app/v1.0';
  }

  private async request<T>(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      method,
      headers: {
        'X-API-KEY': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage: string;

      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.message || errorJson.error || errorText;
      } catch {
        errorMessage = errorText;
      }

      throw new GammaApiError(
        `Gamma API error (${response.status}): ${errorMessage}`,
        response.status,
        errorMessage
      );
    }

    return response.json();
  }

  /**
   * Create a new gamma (presentation, document, webpage, or social post)
   */
  async createGeneration(params: GenerateParams): Promise<GenerateResponse> {
    const response = await this.request<any>('POST', '/generations', params);

    // Log the actual response for debugging
    console.error('Gamma API response:', JSON.stringify(response, null, 2));

    // Map the response to our expected format
    // Gamma API may return different field names
    return {
      id: response.id || response.generationId || response.gamma_id,
      url: response.url || response.gammaUrl || response.gamma_url || `https://gamma.app/docs/${response.id || response.generationId}`,
      title: response.title || response.name || 'Untitled',
      creditsUsed: response.creditsUsed || response.credits_used || 0,
      exportUrls: response.exportUrls || response.export_urls || response.exports,
    };
  }

  /**
   * List available themes
   */
  async listThemes(options?: {
    query?: string;
    limit?: number;
    after?: string;
  }): Promise<PaginatedResponse<Theme>> {
    const searchParams = new URLSearchParams();
    if (options?.query) searchParams.set('query', options.query);
    if (options?.limit) searchParams.set('limit', options.limit.toString());
    if (options?.after) searchParams.set('after', options.after);

    const queryString = searchParams.toString();
    const endpoint = `/themes${queryString ? `?${queryString}` : ''}`;

    return this.request<PaginatedResponse<Theme>>('GET', endpoint);
  }

  /**
   * List available folders
   */
  async listFolders(options?: {
    query?: string;
    limit?: number;
    after?: string;
  }): Promise<PaginatedResponse<Folder>> {
    const searchParams = new URLSearchParams();
    if (options?.query) searchParams.set('query', options.query);
    if (options?.limit) searchParams.set('limit', options.limit.toString());
    if (options?.after) searchParams.set('after', options.after);

    const queryString = searchParams.toString();
    const endpoint = `/folders${queryString ? `?${queryString}` : ''}`;

    return this.request<PaginatedResponse<Folder>>('GET', endpoint);
  }

  /**
   * Get export URLs for a generation
   * Note: Export URLs expire, download promptly
   */
  async getFileUrls(generationId: string): Promise<{ pdf?: string; pptx?: string }> {
    return this.request<{ pdf?: string; pptx?: string }>(
      'GET',
      `/generations/${generationId}/exports`
    );
  }
}

export class GammaApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public apiMessage: string
  ) {
    super(message);
    this.name = 'GammaApiError';
  }
}
