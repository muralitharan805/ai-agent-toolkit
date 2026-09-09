import {
  CallHandler,
  ExecutionContext,
  Injectable,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, of, tap } from 'rxjs';
import { RedisCacheService } from './redis-cache.service';
import * as crypto from 'crypto';

/**
 * HTTP Cache Interceptor with visual emoji console logging
 * and X-Cache header injection.
 */
@Injectable()
export class HttpCacheInterceptor implements NestInterceptor {
  private readonly logger = new Logger(HttpCacheInterceptor.name);

  constructor(private readonly cacheService: RedisCacheService) {}

  async intercept(context: ExecutionContext, next: CallHandler): Promise<Observable<unknown>> {
    const http = context.switchToHttp();
    const request = http.getRequest();
    const response = http.getResponse();

    // Only cache idempotent GET requests
    if (request.method.toUpperCase() !== 'GET') {
      return next.handle();
    }

    const start = Date.now();
    const cacheKey = this.generateCacheKey(request);
    const cachedData = await this.cacheService.get<unknown>(cacheKey);

    if (cachedData !== null) {
      const durationMs = Date.now() - start;
      this.logger.log(`⚡ [CACHE HIT] GET ${request.url} (cached - ${durationMs}ms)`);
      response.setHeader('X-Cache', 'HIT');
      return of(cachedData);
    }

    response.setHeader('X-Cache', 'MISS');
    return next.handle().pipe(
      tap(async (data) => {
        const durationMs = Date.now() - start;
        this.logger.log(`🔍 [CACHE MISS] GET ${request.url} (database query - ${durationMs}ms)`);
        await this.cacheService.set(cacheKey, data, 300);
      })
    );
  }

  private generateCacheKey(request: { url: string; query: Record<string, unknown> }): string {
    const hash = crypto.createHash('md5').update(JSON.stringify(request.query || {})).digest('hex');
    const sanitizedUrl = request.url.split('?')[0];
    return `app:cache:${sanitizedUrl}:${hash}`;
  }
}
