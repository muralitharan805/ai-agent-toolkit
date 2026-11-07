import { Pipe, PipeTransform, inject } from '@angular/core';
import { STRAPI_BASE_URL } from './strapi.service';

/**
 * Standalone Angular Pipe transforming relative Strapi media URLs into absolute URLs.
 * Automatically preserves absolute CDN URLs (e.g. Cloudflare R2, AWS S3).
 *
 * @example
 * ```html
 * <img [src]="article.coverImage.url | strapiMedia" [alt]="article.title" />
 * ```
 */
@Pipe({
  name: 'strapiMedia',
  standalone: true
})
export class StrapiMediaPipe implements PipeTransform {
  private readonly baseUrl = inject(STRAPI_BASE_URL);

  /**
   * Transforms a Strapi media URL into a fully qualified image source.
   *
   * @param url - Relative or absolute media path returned by Strapi
   * @returns Fully qualified media URL string
   */
  transform(url?: string | null): string {
    if (!url) {
      return '';
    }

    // Already an absolute URL (e.g. external S3/Cloudinary/R2 storage)
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('//')) {
      return url;
    }

    const normalizedBase = this.baseUrl.replace(/\/$/, '');
    const normalizedPath = url.startsWith('/') ? url : `/${url}`;
    return `${normalizedBase}${normalizedPath}`;
  }
}
