/**
 * Represents image dimensions and responsive format variations in Strapi Media Library.
 */
export interface StrapiMediaFormat {
  readonly name: string;
  readonly hash: string;
  readonly ext: string;
  readonly mime: string;
  readonly width: number;
  readonly height: number;
  readonly size: number;
  readonly url: string;
}

/**
 * Strapi Media Library attachment schema.
 */
export interface StrapiMedia {
  readonly id: number;
  readonly documentId: string;
  readonly name: string;
  readonly alternativeText?: string | null;
  readonly caption?: string | null;
  readonly width?: number;
  readonly height?: number;
  readonly formats?: {
    readonly thumbnail?: StrapiMediaFormat;
    readonly small?: StrapiMediaFormat;
    readonly medium?: StrapiMediaFormat;
    readonly large?: StrapiMediaFormat;
  } | null;
  readonly url: string;
  readonly mime: string;
  readonly size: number;
}

/**
 * Strapi REST API pagination metadata.
 */
export interface StrapiPagination {
  readonly page: number;
  readonly pageSize: number;
  readonly pageCount: number;
  readonly total: number;
}

/**
 * Standard metadata wrapper in Strapi REST API responses.
 */
export interface StrapiResponseMeta {
  readonly pagination?: StrapiPagination;
}

/**
 * Base document fields provided by Strapi v5 Document Service.
 */
export interface StrapiBaseDocument {
  readonly id: number;
  readonly documentId: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly publishedAt?: string | null;
  readonly locale?: string | null;
}

/**
 * Reusable SEO component schema (`shared.seo`) in Strapi CMS.
 */
export interface StrapiSeoComponent {
  readonly id?: number;
  readonly metaTitle: string;
  readonly metaDescription: string;
  readonly shareImage?: StrapiMedia | null;
  readonly canonicalUrl?: string | null;
  readonly keywords?: string | null;
}

/**
 * Generic response envelope for Strapi v5 collection and single-type endpoints.
 * In Strapi v5, `data` contains the flat document model (or array of models).
 */
export interface StrapiResponse<T> {
  readonly data: T;
  readonly meta: StrapiResponseMeta;
}

/**
 * Generic query parameters for Strapi REST API requests.
 */
export interface StrapiQueryParams {
  readonly populate?: string | readonly string[] | Record<string, unknown>;
  readonly filters?: Record<string, unknown>;
  readonly sort?: string | readonly string[];
  readonly pagination?: {
    readonly page?: number;
    readonly pageSize?: number;
    readonly start?: number;
    readonly limit?: number;
  };
  readonly locale?: string;
}
