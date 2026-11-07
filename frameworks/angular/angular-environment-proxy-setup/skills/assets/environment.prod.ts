import { EnvironmentConfig } from './environment';

/**
 * Production environment configuration.
 * Targets live production API gateways with full HTTPS / WSS protocols.
 */
export const environment: EnvironmentConfig = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/v1',
  wsUrl: 'wss://api.yourdomain.com/socket.io',
  appName: 'Angular App'
};
