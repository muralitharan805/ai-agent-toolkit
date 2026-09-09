/**
 * Standard Environment Configuration Interface.
 * Enforces strict typing for runtime application configuration.
 */
export interface EnvironmentConfig {
  /** Indicates whether the application is running in production mode. */
  readonly production: boolean;
  /** Base API endpoint (relative path '/api' in development to utilize dev server proxy). */
  readonly apiUrl: string;
  /** Base WebSocket endpoint URL. */
  readonly wsUrl: string;
  /** Application display name. */
  readonly appName: string;
}

/**
 * Development environment configuration.
 * Uses relative paths to route requests through local development proxy (proxy.dev.json).
 */
export const environment: EnvironmentConfig = {
  production: false,
  apiUrl: '/api',
  wsUrl: '/socket.io',
  appName: 'Angular App (Development)'
};
