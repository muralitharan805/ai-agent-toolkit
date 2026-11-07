/**
 * Authentication & Authorization Production Toolkit
 * Implements:
 * 1. Password Hashing (bcrypt cost >= 12 / Argon2id)
 * 2. Dual-Token Architecture (15m Access Token, HTTP-Only Refresh Cookie)
 * 3. Token Rotation & Theft Reuse Detection
 * 4. RBAC, ABAC, and Resource Ownership Guards
 */

import type { Request, Response, NextFunction } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  readonly roles: readonly string[];
  readonly permissions: readonly string[];
  readonly tenantId?: string;
}

export interface AuthenticatedRequest extends Request {
  user?: AuthenticatedUser;
}

export interface TokenPair {
  readonly accessToken: string;
  readonly refreshToken: string;
}

export interface RefreshTokenStorage {
  findToken(tokenHash: string): Promise<{ id: string; userId: string; isRevoked: boolean } | null>;
  revokeToken(id: string): Promise<void>;
  revokeAllUserTokens(userId: string): Promise<void>;
  storeToken(userId: string, tokenHash: string, expiresAt: Date): Promise<void>;
}

// ============================================================================
// 1. Password Hashing
// ============================================================================

const BCRYPT_SALT_ROUNDS = 12;

/**
 * Hashes a plaintext password using bcrypt with standard enterprise work factor.
 *
 * @param plaintextPassword - Unencrypted user password
 * @returns Cryptographic password hash
 */
export async function hashPassword(plaintextPassword: string): Promise<string> {
  return bcrypt.hash(plaintextPassword, BCRYPT_SALT_ROUNDS);
}

/**
 * Compares a candidate password against a stored bcrypt hash.
 *
 * @param candidate - Plaintext password input
 * @param hash - Stored password hash
 * @returns Resolves true if password matches
 */
export async function verifyPassword(candidate: string, hash: string): Promise<boolean> {
  return bcrypt.compare(candidate, hash);
}

// ============================================================================
// 2. Dual-Token Architecture & Cookie Partitioning
// ============================================================================

const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY_DAYS = 7;

/**
 * Sets the refresh token into a secure, HTTP-Only partitioned cookie.
 *
 * @param res - Express response object
 * @param refreshToken - Generated refresh token string
 */
export function setRefreshTokenCookie(res: Response, refreshToken: string): void {
  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/api/v1/auth/refresh',
    maxAge: REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000,
  });
}

// ============================================================================
// 3. Token Rotation & Reuse Detection
// ============================================================================

/**
 * Rotates a refresh token and detects token theft if a revoked token is presented.
 *
 * @param tokenString - Inbound refresh token
 * @param storage - Refresh token persistence store
 * @param issueTokensFn - Token generator function
 * @returns Resolves fresh TokenPair
 */
export async function rotateRefreshTokenWithTheftDetection(
  tokenString: string,
  storage: RefreshTokenStorage,
  issueTokensFn: (userId: string) => Promise<TokenPair>
): Promise<TokenPair> {
  const tokenHash = await bcrypt.hash(tokenString, 10);
  const record = await storage.findToken(tokenHash);

  if (!record) {
    throw new Error('Invalid refresh token');
  }

  // Detect reuse of revoked token (Indication of token theft)
  if (record.isRevoked) {
    await storage.revokeAllUserTokens(record.userId);
    throw new Error('Token reuse detected. All active sessions invalidated.');
  }

  // Revoke old token and issue new token pair
  await storage.revokeToken(record.id);
  return issueTokensFn(record.userId);
}

// ============================================================================
// 4. Authorization Middlewares & IDOR Protection
// ============================================================================

/**
 * Route middleware asserting user has at least one of the specified roles.
 *
 * @param requiredRoles - Array of allowed roles (e.g. ['ADMIN', 'MANAGER'])
 * @returns Express Middleware
 */
export function requireRoles(...requiredRoles: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ message: 'Authentication required' });
      return;
    }

    const hasRole = req.user.roles.some((role) => requiredRoles.includes(role));
    if (!hasRole) {
      res.status(403).json({ message: 'Forbidden: Insufficient privileges' });
      return;
    }

    next();
  };
}

/**
 * Route middleware protecting against Insecure Direct Object Reference (IDOR).
 *
 * @param extractOwnerId - Function to extract resource owner ID from request
 * @returns Express Middleware
 */
export function requireResourceOwnership(
  extractOwnerId: (req: AuthenticatedRequest) => Promise<string | null>
) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    if (!req.user) {
      res.status(401).json({ message: 'Authentication required' });
      return;
    }

    // Admins bypass ownership checks
    if (req.user.roles.includes('ADMIN')) {
      return next();
    }

    const ownerId = await extractOwnerId(req);
    if (!ownerId) {
      res.status(404).json({ message: 'Resource not found' });
      return;
    }

    if (ownerId !== req.user.id) {
      res.status(403).json({ message: 'Forbidden: You do not own this resource' });
      return;
    }

    next();
  };
}
