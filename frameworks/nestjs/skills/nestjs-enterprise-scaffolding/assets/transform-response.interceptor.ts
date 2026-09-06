import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Request, Response } from 'express';

/**
 * Standardized API Response Envelope wrapping all successful endpoint results.
 */
export interface ApiResponseEnvelope<T> {
  readonly success: boolean;
  readonly statusCode: number;
  readonly message: string;
  readonly data: T;
  readonly meta?: Record<string, unknown>;
  readonly timestamp: string;
  readonly path: string;
}

/**
 * Global response transformer wrapping raw controller returns into the uniform API envelope.
 */
@Injectable()
export class TransformResponseInterceptor<T> implements NestInterceptor<T, ApiResponseEnvelope<T>> {
  intercept(context: ExecutionContext, next: CallHandler): Observable<ApiResponseEnvelope<T>> {
    const ctx = context.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    return next.handle().pipe(
      map((resData: unknown) => {
        const isPaginated =
          resData !== null &&
          typeof resData === 'object' &&
          'data' in resData &&
          'meta' in resData;

        const payloadRecord = resData as Record<string, unknown> | null;
        const data = (isPaginated && payloadRecord ? payloadRecord['data'] : resData) as T;
        const meta = isPaginated && payloadRecord ? (payloadRecord['meta'] as Record<string, unknown>) : undefined;

        return {
          success: true,
          statusCode: response.statusCode,
          message: 'Operation completed successfully',
          data,
          ...(meta ? { meta } : {}),
          timestamp: new Date().toISOString(),
          path: request.url,
        };
      }),
    );
  }
}
