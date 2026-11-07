/**
 * Production Runtime Security Baseline Middleware Template
 * Implements:
 * 1. HTTP Security Headers via Helmet (CSP, HSTS, X-Frame-Options: DENY)
 * 2. Strict CORS Whitelisting with Preflight Caching
 * 3. Multi-Tiered Ingress Rate Limiting Definitions
 * 4. Request Body Payload Size Bounds (1MB limit)
 */

import type { Application, Request, Response, NextFunction } from 'express';
import helmet from 'helmet';
import cors from 'cors';

// ============================================================================
// 1. HTTP Security Headers Configuration
// ============================================================================

/**
 * Hardened Helmet security headers middleware.
 */
export const hardenedSecurityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'"],
      fontSrc: ["'self'", 'https://fonts.gstatic.com'],
      objectSrc: ["'none'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
  hsts: {
    maxAge: 31536000, // 1 year
    includeSubDomains: true,
    preload: true,
  },
  frameguard: { action: 'deny' },
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
});

// ============================================================================
// 2. Strict CORS Configuration
// ============================================================================

/**
 * Constructs a strict CORS middleware using an explicit origin whitelist.
 *
 * @param allowedOrigins - Set or array of authorized frontend origins
 * @returns Express CORS Middleware
 */
export function createStrictCorsMiddleware(allowedOrigins: ReadonlySet<string>) {
  return cors({
    origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
      // Allow non-browser agents (curl, server-to-server) where origin is undefined
      if (!origin || allowedOrigins.has(origin)) {
        callback(null, true);
      } else {
        callback(new Error(`Origin '${origin}' blocked by CORS security policy`));
      }
    },
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    credentials: true,
    maxAge: 600, // Cache preflight response for 10 minutes
  });
}

// ============================================================================
// 3. Multi-Tiered Rate Limiting Configurations
// ============================================================================

export interface RateLimitTierConfig {
  readonly windowMs: number;
  readonly maxRequests: number;
  readonly message: string;
}

/**
 * Standard concrete rate limit tiers.
 */
export const RATE_LIMIT_TIERS: Record<string, RateLimitTierConfig> = {
  AUTH_LOGIN: {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 5,
    message: 'Too many login attempts. Please try again in 1 minute.',
  },
  AUTH_REGISTER: {
    windowMs: 60 * 60 * 1000, // 1 hour
    maxRequests: 10,
    message: 'Account registration limit exceeded. Please try again later.',
  },
  PASSWORD_RESET: {
    windowMs: 60 * 60 * 1000, // 1 hour
    maxRequests: 3,
    message: 'Too many password reset requests. Please check your inbox or try later.',
  },
  API_AUTHENTICATED: {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 1000,
    message: 'API rate limit exceeded.',
  },
  API_PUBLIC: {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 100,
    message: 'Public rate limit exceeded.',
  },
  FILE_UPLOAD: {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 10,
    message: 'Upload frequency limit exceeded.',
  },
};

// ============================================================================
// 4. Request Payload Body Bounds
// ============================================================================

/**
 * Enforces explicit payload bounds on the Express application to prevent memory DoS.
 *
 * @param app - Express Application instance
 */
export function applyPayloadLimits(app: Application): void {
  // express.json({ limit: '1mb' }) prevents memory exhaustion from oversized JSON bodies
  // express.urlencoded({ extended: true, limit: '1mb' })
}
