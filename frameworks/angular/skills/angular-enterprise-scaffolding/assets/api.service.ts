import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

/**
 * Configuration options for HTTP requests.
 */
export interface HttpOptions {
  /** Query parameter map supporting primitive types and arrays. */
  readonly params?: Record<string, string | number | boolean | readonly (string | number | boolean)[] | undefined>;
  /** Optional custom HTTP header record. */
  readonly headers?: Record<string, string>;
}

/**
 * Generic enterprise API service wrapping Angular HttpClient.
 * Provides typed REST verb wrappers, automated parameter serialization, and file uploads.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  /**
   * Performs an HTTP GET request.
   * @param endpoint - Target API endpoint or relative URL path.
   * @param options - Optional query parameters and custom headers.
   * @returns Observable emitting the typed response payload.
   */
  get<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    return this.http.get<T>(endpoint, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  /**
   * Performs an HTTP POST request.
   * @param endpoint - Target API endpoint.
   * @param body - Request payload to serialize as JSON.
   * @param options - Optional query parameters and custom headers.
   * @returns Observable emitting the typed response payload.
   */
  post<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    return this.http.post<T>(endpoint, body, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  /**
   * Performs an HTTP PUT request.
   * @param endpoint - Target API endpoint.
   * @param body - Request payload to replace resource state.
   * @param options - Optional query parameters and custom headers.
   * @returns Observable emitting the typed response payload.
   */
  put<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    return this.http.put<T>(endpoint, body, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  /**
   * Performs an HTTP PATCH request.
   * @param endpoint - Target API endpoint.
   * @param body - Partial request payload for incremental update.
   * @param options - Optional query parameters and custom headers.
   * @returns Observable emitting the typed response payload.
   */
  patch<T>(endpoint: string, body: unknown, options?: HttpOptions): Observable<T> {
    return this.http.patch<T>(endpoint, body, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  /**
   * Performs an HTTP DELETE request.
   * @param endpoint - Target API endpoint.
   * @param options - Optional query parameters and custom headers.
   * @returns Observable emitting the typed response payload.
   */
  delete<T>(endpoint: string, options?: HttpOptions): Observable<T> {
    return this.http.delete<T>(endpoint, {
      params: this.buildHttpParams(options?.params),
      headers: new HttpHeaders(options?.headers ?? {})
    });
  }

  /**
   * Uploads a binary file using multipart/form-data encoding.
   * @param endpoint - Target upload endpoint.
   * @param file - Binary file to upload.
   * @param extraData - Optional auxiliary form fields to include in upload.
   * @returns Observable emitting the typed response payload.
   */
  uploadFile<T>(endpoint: string, file: File, extraData?: Record<string, string>): Observable<T> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    if (extraData) {
      Object.entries(extraData).forEach(([key, value]) => formData.append(key, value));
    }

    return this.http.post<T>(endpoint, formData);
  }

  /**
   * Serializes a dictionary of primitives into an Angular HttpParams instance.
   * Filters out undefined, null, and empty string entries.
   * @param paramsObj - Dictionary of key-value query parameters.
   * @returns Populated HttpParams object.
   */
  private buildHttpParams(paramsObj?: HttpOptions['params']): HttpParams {
    let httpParams = new HttpParams();
    if (!paramsObj) {
      return httpParams;
    }

    for (const [key, value] of Object.entries(paramsObj)) {
      if (value === undefined || value === null || value === '') {
        continue;
      }
      if (Array.isArray(value)) {
        for (const item of value) {
          httpParams = httpParams.append(key, String(item));
        }
      } else {
        httpParams = httpParams.set(key, String(value));
      }
    }

    return httpParams;
  }
}
