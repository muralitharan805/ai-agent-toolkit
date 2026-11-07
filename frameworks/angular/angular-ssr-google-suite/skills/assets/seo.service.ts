import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { DOCUMENT, isPlatformBrowser } from '@angular/common';

/**
 * Configuration payload for dynamic SEO meta tags and social open graph attributes.
 */
export interface SeoConfig {
  /** Page title to set in the browser tab and social previews */
  readonly title: string;
  /** Meta description summarizing page content (50-160 characters recommended) */
  readonly description: string;
  /** Fully qualified canonical URL of the page */
  readonly url: string;
  /** Optional preview image URL for Open Graph and Twitter Card */
  readonly image?: string;
  /** Optional custom canonical URL if different from the primary url */
  readonly canonicalUrl?: string;
}

/**
 * Service managing document head metadata, Open Graph tags, and canonical link
 * elements across both Server-Side Pre-rendering and client-side hydration.
 */
@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly title = inject(Title);
  private readonly document = inject(DOCUMENT);
  private readonly platformId = inject(PLATFORM_ID);

  /**
   * Sets page title, description, Open Graph metadata, and canonical link.
   *
   * @param config - The SEO configuration payload
   */
  setMetaTags(config: SeoConfig): void {
    this.title.setTitle(config.title);
    this.meta.updateTag({ name: 'description', content: config.description });
    this.meta.updateTag({ property: 'og:title', content: config.title });
    this.meta.updateTag({ property: 'og:description', content: config.description });
    this.meta.updateTag({ property: 'og:url', content: config.url });
    this.meta.updateTag({ property: 'og:image', content: config.image ?? `${config.url}/favicon.ico` });
    this.meta.updateTag({ property: 'twitter:card', content: 'summary_large_image' });

    this.setCanonicalUrl(config.canonicalUrl ?? config.url);
  }

  /**
   * Injects or updates the canonical link tag (<link rel="canonical" href="...">)
   * in the document head during both Edge SSR pre-rendering and CSR navigation.
   * Automatically strips query parameters to maintain deterministic canonical indexing.
   *
   * @param url - The URL string to designate as canonical
   */
  setCanonicalUrl(url?: string): void {
    const origin = isPlatformBrowser(this.platformId)
      ? this.document.location.origin
      : 'https://yourdomain.com';
    const path = isPlatformBrowser(this.platformId)
      ? this.document.location.pathname
      : '';
    const rawUrl = url ?? `${origin}${path}`;
    const cleanUrl = rawUrl.split('?')[0];

    let link: HTMLLinkElement | null = this.document.querySelector("link[rel='canonical']");
    if (!link) {
      link = this.document.createElement('link');
      link.setAttribute('rel', 'canonical');
      this.document.head.appendChild(link);
    }

    link.setAttribute('href', cleanUrl);
  }
}
