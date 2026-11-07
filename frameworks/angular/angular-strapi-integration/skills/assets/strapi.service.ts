import { Injectable, inject, PLATFORM_ID, makeStateKey, TransferState, InjectionToken } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { StrapiResponse, StrapiQueryParams } from './strapi-models';

/**
 * Injection token for configuring the base Strapi CMS URL (e.g. 'https://cms.yourdomain.com').
 */
export const STRAPI_BASE_URL = new InjectionToken<string>('STRAPI_BASE_URL', {
  providedIn: 'root',
  factory: () => 'http://localhost:1337'
});

/**
 * Generic, type-safe client service for querying Strapi v5 Document APIs
 * with integrated Angular SSR TransferState caching to eliminate hydration layout shifts.
 */
@Injectable({ providedIn: 'root' })
export class StrapiService {
  private readonly http = inject(HttpClient);
  private readonly transferState = inject(TransferState);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly baseUrl = inject(STRAPI_BASE_URL);

  /**
   * Executes a GET request against a Strapi endpoint without TransferState caching.
   *
   * @param endpoint - Strapi API route path (e.g. '/api/articles')
   * @param query - Optional query parameters for population, filtering, and pagination
   */
  get<T>(endpoint: string, query?: StrapiQueryParams): Observable<StrapiResponse<T>> {
    const url = this.buildUrl(endpoint);
    const params = this.buildHttpParams(query);
    return this.http.get<StrapiResponse<T>>(url, { params });
  }

  /**
   * Executes a GET request with TransferState caching to optimize SSR pre-rendering
   * and prevent duplicate network calls during client hydration.
   *
   * @param cacheKey - Unique key string identifying the cached payload
   * @param endpoint - Strapi API route path (e.g. '/api/global-setting')
   * @param query - Optional query parameters
   */
  getWithTransferState<T>(cacheKey: string, endpoint: string, query?: StrapiQueryParams): Observable<StrapiResponse<T>> {
    const key = makeStateKey<StrapiResponse<T>>(cacheKey);

    // Read from transferred state on the client if available
    if (this.transferState.hasKey(key)) {
      const cached = this.transferState.get(key, null as unknown as StrapiResponse<T>);
      this.transferState.remove(key); // Evict after hydration consumption
      if (cached) {
        return of(cached);
      }
    }

    // Fetch from HTTP and cache in TransferState if running on server
    return this.get<T>(endpoint, query).pipe(
      tap((response) => {
        if (!isPlatformBrowser(this.platformId)) {
          this.transferState.set(key, response);
        }
      })
    );
  }

  /**
   * Resolves the full URL for a relative Strapi endpoint path.
   */
  private buildUrl(endpoint: string): string {
    const normalizedBase = this.baseUrl.replace(/\/$/, '');
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${normalizedBase}${normalizedEndpoint}`;
  }

  /**
   * Converts a structured StrapiQueryParams object into Angular HttpParams.
   */
  private buildHttpParams(query?: StrapiQueryParams): HttpParams {
    let params = new HttpParams();
    if (!query) {
      return params;
    }

    if (query.populate) {
      if (typeof query.populate === 'string') {
        params = params.set('populate', query.populate);
      } else if (Array.isArray(query.populate)) {
        query.populate.forEach((field, index) => {
          params = params.set(`populate[${index}]`, String(field));
        });
      }
    }

    if (query.locale) {
      params = params.set('locale', query.locale);
    }

    return params;
  }
}
