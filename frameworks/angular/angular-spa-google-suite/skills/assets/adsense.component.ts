import { Component, OnInit, inject, PLATFORM_ID, signal, input, ChangeDetectionStrategy } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

/**
 * Window extension interface for Google AdSense adsbygoogle queue.
 */
declare global {
  interface Window {
    adsbygoogle?: Array<Record<string, unknown>>;
  }
}

/**
 * Standalone responsive AdSense advertising slot component.
 *
 * Enforces Web Vitals Cumulative Layout Shift (CLS) prevention through explicit
 * min-height container reservation (min-height: 250px) and suppresses ad rendering
 * in local development environments.
 */
@Component({
  selector: 'app-adsense',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!isLocalhost()) {
      <div class="ad-slot-container" style="min-height: 250px; width: 100%; display: block; overflow: hidden;">
        <ins class="adsbygoogle"
             style="display: block;"
             [attr.data-ad-client]="client()"
             [attr.data-ad-slot]="slot()"
             [attr.data-ad-format]="format()"
             data-full-width-responsive="true"></ins>
      </div>
    }
  `,
  styles: [`
    .ad-slot-container {
      margin: 1.5rem auto;
      text-align: center;
    }
  `]
})
export class AdsenseComponent implements OnInit {
  /** AdSense ad unit slot ID */
  readonly slot = input<string>('');
  /** Ad unit layout format ('auto', 'rectangle', 'horizontal') */
  readonly format = input<string>('auto');
  /** Google AdSense Publisher Client ID */
  readonly client = input<string>('ca-pub-1649083292065809');

  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isLocalhost = signal<boolean>(true);

  /**
   * Initializes the ad slot queue when running in a live production browser.
   */
  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0';
    this.isLocalhost.set(isLocal);

    if (!isLocal) {
      try {
        const adsQueue = window.adsbygoogle ?? [];
        window.adsbygoogle = adsQueue;
        adsQueue.push({});
      } catch {
        // Silently capture ad blocker or network exceptions without breaking UI
      }
    }
  }
}
