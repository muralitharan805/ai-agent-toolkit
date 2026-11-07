import { Injectable, NestInterceptor, ExecutionContext, CallHandler, Logger } from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';

/**
 * Global HTTP request lifecycle interceptor measuring execution latency
 * and propagating unique correlation IDs across service boundaries.
 */
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const ctx = context.switchToHttp();
    const req = ctx.getRequest<Request>();
    const res = ctx.getResponse<Response>();

    const correlationId = (req.headers['x-correlation-id'] as string) || `req-${Date.now()}`;
    res.setHeader('X-Correlation-ID', correlationId);

    const startTime = Date.now();
    const { method, url } = req;

    return next.handle().pipe(
      tap(() => {
        const duration = Date.now() - startTime;
        const statusCode = res.statusCode;
        this.logger.log(`[${correlationId}] ${method} ${url} ${statusCode} - ${duration}ms`);
      }),
    );
  }
}
