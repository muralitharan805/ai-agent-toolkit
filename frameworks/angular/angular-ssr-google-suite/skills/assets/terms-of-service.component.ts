import { Component, ChangeDetectionStrategy, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

/**
 * Standalone SSR-safe Terms of Service component establishing acceptable usage policies
 * and disclaimer of warranties for Google AdSense inventory compliance.
 */
@Component({
  selector: 'app-terms-of-service',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="legal-container">
      <header class="legal-header">
        <h1>Terms of Service</h1>
        <p class="effective-date">Effective Date: August 16, 2026</p>
      </header>

      <section class="legal-section">
        <h2>1. Acceptance of Terms</h2>
        <p>By accessing or using this edge-rendered web application, you agree to be bound by these Terms of Service and all applicable laws and regulations. If you do not agree, you are prohibited from using the service.</p>
      </section>

      <section class="legal-section">
        <h2>2. Permitted Use & Intellectual Property</h2>
        <p>You are granted a limited, revocable license to access and use the web utilities provided for personal or authorized business evaluation. Automated scraping or denial-of-service attacks against our edge endpoints are strictly prohibited.</p>
      </section>

      <section class="legal-section">
        <h2>3. Advertisements & External Links</h2>
        <p>Our application presents third-party advertisements via Google AdSense and hyperlinks to third-party web destinations. We do not endorse or control the practices of these external services.</p>
      </section>

      <section class="legal-section">
        <h2>4. Disclaimer of Warranties</h2>
        <p>The application and its utility calculators are provided "as is" without warranty of any kind, either express or implied.</p>
      </section>
    </article>
  `,
  styles: [`
    .legal-container {
      max-width: 800px;
      margin: 2rem auto;
      padding: 2rem;
      color: #e2e8f0;
      line-height: 1.7;
    }
    .legal-header {
      margin-bottom: 2rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 1rem;
    }
    .legal-header h1 {
      font-size: 2rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 0.5rem 0;
    }
    .effective-date {
      color: #94a3b8;
      font-size: 0.875rem;
      margin: 0;
    }
    .legal-section {
      margin-bottom: 2rem;
    }
    .legal-section h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #94a3b8;
      margin: 0 0 0.75rem 0;
    }
    .legal-section p {
      color: #cbd5e1;
      font-size: 0.95rem;
      margin: 0 0 1rem 0;
    }
  `]
})
export class TermsOfServiceComponent {
  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isBrowser = isPlatformBrowser(this.platformId);
}
