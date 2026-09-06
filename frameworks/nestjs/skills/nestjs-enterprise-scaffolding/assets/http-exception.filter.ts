import { ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus } from '@nestjs/common';
import { Request, Response } from 'express';

/**
 * Global exception filter standardizing error payloads across all HTTP endpoints.
 * Prevents raw database connection strings or stack traces from leaking to clients.
 */
@Catch()
export class GlobalHttpExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const exceptionResponse =
      exception instanceof HttpException
        ? exception.getResponse()
        : 'Internal server error';

    const formattedError =
      typeof exceptionResponse === 'object' && exceptionResponse !== null
        ? exceptionResponse
        : { message: exceptionResponse };

    response.status(status).json({
      success: false,
      statusCode: status,
      path: request.url,
      timestamp: new Date().toISOString(),
      error: formattedError,
    });
  }
}
