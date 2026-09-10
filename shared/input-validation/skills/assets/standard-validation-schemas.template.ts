/**
 * Standard Inbound DTO Schemas & Validation Pipe Template (Zod)
 * Implements strict whitelist mode (Mass Assignment defense) & field error aggregation.
 */

import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';

// Standard Format Regex Standards
export const E164_PHONE_REGEX = /^\+[1-9]\d{1,14}$/;
export const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * Standard User Registration Inbound DTO Schema
 */
export const RegisterUserDtoSchema = z.object({
  emailAddress: z.string().trim().email('Invalid email address format'),
  password: z.string().min(8, 'Password must contain at least 8 characters').max(128),
  fullName: z.string().trim().min(2, 'Full name must be at least 2 characters').max(100),
  phoneNumber: z.string().regex(E164_PHONE_REGEX, 'Phone must follow international E.164 format (+1234567890)').optional(),
  age: z.number().int().min(18, 'Must be at least 18 years of age').max(120),
}).strict(); // Enforce whitelist: reject unexpected fields like 'role' or 'isAdmin'

export type RegisterUserDto = z.infer<typeof RegisterUserDtoSchema>;

/**
 * Standard Pagination Query Schema
 */
export const PaginationQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.string().trim().max(50).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
}).strict();

export type PaginationQuery = z.infer<typeof PaginationQuerySchema>;

/**
 * Standard UUID Route Parameter Schema
 */
export const UuidParamSchema = z.object({
  id: z.string().regex(UUID_V4_REGEX, 'Identifier must be a valid UUIDv4'),
}).strict();

export type UuidParam = z.infer<typeof UuidParamSchema>;

/**
 * Reusable Express Middleware Factory for Inbound Request Validation
 */
export function validateRequest<TBody = unknown, TQuery = unknown, TParams = unknown>(schemas: {
  body?: z.ZodType<TBody>;
  query?: z.ZodType<TQuery>;
  params?: z.ZodType<TParams>;
}) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const errorDetails: Array<{ field: string; message: string }> = [];

    if (schemas.body) {
      const result = schemas.body.safeParse(req.body);
      if (!result.success) {
        result.error.errors.forEach((err) => {
          errorDetails.push({ field: `body.${err.path.join('.')}`, message: err.message });
        });
      } else {
        req.body = result.data;
      }
    }

    if (schemas.query) {
      const result = schemas.query.safeParse(req.query);
      if (!result.success) {
        result.error.errors.forEach((err) => {
          errorDetails.push({ field: `query.${err.path.join('.')}`, message: err.message });
        });
      } else {
        req.query = result.data as Record<string, unknown>;
      }
    }

    if (schemas.params) {
      const result = schemas.params.safeParse(req.params);
      if (!result.success) {
        result.error.errors.forEach((err) => {
          errorDetails.push({ field: `params.${err.path.join('.')}`, message: err.message });
        });
      } else {
        req.params = result.data as Record<string, string>;
      }
    }

    if (errorDetails.length > 0) {
      const correlationId = (req.headers['x-correlation-id'] as string) || 'unknown';
      res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: `Input validation failed on ${errorDetails.length} field(s)`,
          details: errorDetails,
        },
        meta: {
          correlationId,
          timestamp: new Date().toISOString(),
          path: req.originalUrl,
        },
      });
      return;
    }

    next();
  };
}
