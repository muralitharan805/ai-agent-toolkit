/**
 * Developer Experience (DevEx) & Code Quality Tooling Bootstrap Asset.
 *
 * Exports production-ready configurations for Husky, lint-staged, Commitlint,
 * GitLeaks secret scanning, and Docker Compose v2 local backing services.
 */

/**
 * Standard lint-staged configuration mapping file globs to automated format and lint commands.
 */
export const lintStagedConfig: Record<string, string[]> = {
  '*.{ts,tsx}': [
    'eslint --fix --max-warnings=0',
    'prettier --write',
  ],
  '*.{json,md,yml,yaml}': [
    'prettier --write',
  ],
  '*.{py}': [
    'ruff check --fix',
    'ruff format',
  ],
  '*.{go}': [
    'golangci-lint run --fix',
    'gofmt -w',
  ],
};

/**
 * Commitlint configuration enforcing Conventional Commits 1.0.0 rules.
 */
export const commitlintConfig: Record<string, unknown> = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation changes
        'refactor', // Code refactoring without behavior change
        'perf',     // Performance improvement
        'test',     // Adding or updating tests
        'chore',    // Tooling, build system, auxiliary changes
        'ci',       // Continuous integration pipeline changes
        'build',    // Dependencies or package management updates
      ],
    ],
    'type-case': [2, 'always', 'lower-case'],
    'scope-case': [2, 'always', 'lower-case'],
    'subject-case': [2, 'never', ['upper-case', 'pascal-case']],
    'header-max-length': [2, 'always', 72],
    'body-leading-blank': [2, 'always'],
    'footer-leading-blank': [2, 'always'],
  },
};

/**
 * Baseline .gitleaks.toml configuration template preventing accidental secret commits.
 */
export const gitleaksConfigTemplate = `
[extend]
useDefault = true

[allowlist]
description = "Repository-specific test mock allowlist"
paths = [
  '''^\\.env\\.example$''',
  '''evals/.*''',
  '''test/fixtures/.*'''
]
regexes = [
  '''replace_with_[a-z0-9_]+''',
  '''test_secret_[a-z0-9_]+'''
]
`;

/**
 * Baseline Docker Compose v2 configuration template for one-command local backing services.
 */
export const composeDevTemplate = `
# compose.yaml - Local Developer Backing Services
services:
  database:
    image: postgres:16-alpine
    container_name: dev_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: \${DATABASE_USER:-postgres}
      POSTGRES_PASSWORD: \${DATABASE_PASSWORD:-postgres}
      POSTGRES_DB: \${DATABASE_NAME:-dev_db}
    ports:
      - "\${DATABASE_PORT:-5432}:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d dev_db"]
      interval: 5s
      timeout: 3s
      retries: 5

  cache:
    image: redis:7-alpine
    container_name: dev_redis
    restart: unless-stopped
    ports:
      - "\${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_dev_data:
  redis_dev_data:
`;
