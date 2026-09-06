import { z } from 'zod';

/**
 * Strict schema for runtime environment variables validated at application bootstrap.
 */
export const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url({ message: 'DATABASE_URL must be a valid connection URI' }),
  JWT_SECRET: z.string().min(16, { message: 'JWT_SECRET must contain at least 16 characters' }),
  JWT_EXPIRES_IN: z.string().default('1d'),
});

/**
 * Inferred TypeScript type derived from the environment schema.
 */
export type EnvConfig = z.infer<typeof envSchema>;

/**
 * Validates raw process.env records against the Zod schema.
 *
 * @param config - Raw environment key-value map
 * @returns Validated and type-coerced environment configuration
 * @throws Error if any required variable is missing or malformed
 */
export function validateEnv(config: Record<string, unknown>): EnvConfig {
  const result = envSchema.safeParse(config);
  if (!result.success) {
    const errorDetails = JSON.stringify(result.error.format(), null, 2);
    throw new Error(`Critical Config validation error:\n${errorDetails}`);
  }
  return result.data;
}
