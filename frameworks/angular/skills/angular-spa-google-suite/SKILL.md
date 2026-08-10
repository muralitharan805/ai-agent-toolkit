---
name: angular-spa-google-suite
description: "Angular Standalone CSR SPA code templates for AppTitleStrategy, SeoService, AnalyticsService SPA route tracking, and AdsenseComponent."
---

# Angular SPA Google Suite Skill

## Code Templates

### 1. Title Synchronization (`src/app/core/strategies/page-title.strategy.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AppTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);

  override updateTitle(routerState: RouterStateSnapshot): void {
    const title = this.buildTitle(routerState);
    if (title) {
      this.title.setTitle(`${title} | SeyaliCraft Labs`);
    } else {
      this.title.setTitle('SeyaliCraft Labs — Personal Engineering Sandbox');
    }
  }
}
```

### 2. Dynamic Meta & Canonical Link Resolution (`src/app/core/services/seo.service.ts`)
```typescript
import { Injectable, inject } from '@angular/core';
import { Meta } from '@angular/platform-browser';
import { DOCUMENT } from '@angular/common';

export interface SeoConfig {
  title: string;
  description: string;
  url: string;
  image?: string;
  canonicalUrl?: string;
}

@Injectable({ providedIn: 'root' })
export class SeoService {
  private readonly meta = inject(Meta);
  private readonly document = inject(DOCUMENT);

  /**
   * Updates standard Open Graph, Twitter, and meta description tags.
   * Also updates or injects the page canonical link tag.
   */
  setMetaTags(config: SeoConfig): void {
    this.meta.updateTag({ name: 'description', content: config.description });
    this.meta.updateTag({ property: 'og:title', content: config.title });
    this.meta.updateTag({ property: 'og:description', content: config.description });
    this.meta.updateTag({ property: 'og:url', content: config.url });
    this.meta.updateTag({ property: 'og:image', content: config.image || `${config.url}/favicon.ico` });
    this.meta.updateTag({ property: 'twitter:card', content: 'summary_large_image' });

    this.setCanonicalUrl(config.canonicalUrl || config.url);
  }

  /**
   * Injects or updates the canonical link tag (<link rel="canonical" href="...">)
   * in the document head to prevent duplicate content penalties in Search Console.
   * Automatically strips query parameters to maintain clean canonical URLs.
   */
  setCanonicalUrl(url?: string): void {
    const rawUrl = url || `${this.document.location.origin}${this.document.location.pathname}`;
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
```

### 3. SPA Route Navigation Analytics (`src/app/core/services/analytics.service.ts`)
```typescript
import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
  }
}

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly router = inject(Router);
  private readonly platformId = inject(PLATFORM_ID);

  init(measurementId: string): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        if (typeof window.gtag === 'function') {
          window.gtag('config', measurementId, {
            page_path: event.urlAfterRedirects,
          });
        }
      });
  }

  trackEvent(eventName: string, params: Record<string, unknown> = {}): void {
    if (isPlatformBrowser(this.platformId) && typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
    }
  }
}
```

### 4. Standalone AdSense Banner Component (`src/app/shared/components/adsense.component.ts`)
```typescript
import { Component, OnInit, inject, PLATFORM_ID, signal, input } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-adsense',
  standalone: true,
  template: `
    @if (!isDevMode()) {
      <div class="ad-container-wrapper" style="min-height: 250px; width: 100%; display: block;">
        <ins class="adsbygoogle"
             style="display:block"
             [attr.data-ad-client]="client()"
             [attr.data-ad-slot]="slot()"
             [attr.data-ad-format]="format()"
             data-full-width-responsive="true"></ins>
      </div>
    }
  `
})
export class AdsenseComponent implements OnInit {
  slot = input<string>('');
  format = input<string>('auto');
  client = input<string>('ca-pub-1649083292065809');

  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isDevMode = signal(true);

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      const host = window.location.hostname;
      if (host !== 'localhost' && host !== '127.0.0.1') {
        this.isDevMode.set(false);
        try {
          // @ts-ignore
          (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
          console.warn('AdSense load error:', e);
        }
      }
    }
  }
}
```
