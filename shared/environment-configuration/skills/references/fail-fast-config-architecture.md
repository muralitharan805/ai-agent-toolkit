# Fail-Fast Environment Configuration & Secrets Management Reference

## 1. Architectural Philosophy

> **Fail-Fast on Boot**: A backend system must NEVER start in an invalid, ambiguous, or incomplete state. If a required credential, database connection string, or port is missing or malformed, the process MUST immediately terminate with an informative error before opening network listeners or initializing stateful connections.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      4-Stage Configuration Order                       │
└────────────────────────────────────────────────────────────────────────┘
  Stage 1: Hardcoded Safe Defaults (Local Port 3000, non-sensitive flags)
     │
  Stage 2: Environment File (.env.development / .env.test)
     │
  Stage 3: Runtime Secrets Injection (AWS Secrets Manager / Vault / K8s)
     │
  Stage 4: Mandatory Schema Validation Gate (Zod / Pydantic / Viper)
     │
     ├──► [VALID]   ──► Initialize Logger, DB Pools & HTTP Listeners
     └──► [INVALID] ──► Log structured error & exit(1) IMMEDIATELY
```

---

## 2. Multi-Language Schema Validation Patterns

### TypeScript / Node.js (Zod)
```typescript
import { z } from 'zod';

export const EnvironmentSchema = z.object({
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  APP_ENV: z.enum(['development', 'test', 'staging', 'production']),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('15m'),
  REDIS_URL: z.string().url(),
});

export type EnvironmentConfig = z.infer<typeof EnvironmentSchema>;

export class ConfigService {
  private static instance: EnvironmentConfig;

  public static initialize(): EnvironmentConfig {
    const result = EnvironmentSchema.safeParse(process.env);
    if (!result.success) {
      console.error(JSON.stringify({
        level: 'FATAL',
        message: 'Startup Configuration Validation Failed',
        errors: result.error.errors.map(e => ({ path: e.path.join('.'), message: e.message }))
      }));
      process.exit(1);
    }
    ConfigService.instance = Object.freeze(result.data);
    return ConfigService.instance;
  }

  public static get<K extends keyof EnvironmentConfig>(key: K): EnvironmentConfig[K] {
    if (!ConfigService.instance) {
      throw new Error('ConfigService must be initialized before accessing values');
    }
    return ConfigService.instance[key];
  }
}
```

### Python (Pydantic Settings)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn
from enum import Enum
import sys

class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

class AppConfig(BaseSettings):
    port: int = Field(default=3000, ge=1, le=65535)
    app_env: AppEnv = AppEnv.DEVELOPMENT
    database_url: PostgresDsn
    jwt_secret: str = Field(min_length=32)
    redis_url: RedisDsn

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    config = AppConfig()
except Exception as e:
    sys.stderr.write(f"FATAL: Application Configuration Error: {e}\n")
    sys.exit(1)
```

### Go (CleanEnv / Viper)
```go
package config

import (
	"log"
	"os"
	"github.com/ilyakaznacheev/cleanenv"
)

type Config struct {
	Port        int    `env:"PORT" env-default:"3000"`
	AppEnv      string `env:"APP_ENV" env-required:"true"`
	DatabaseURL string `env:"DATABASE_URL" env-required:"true"`
	JWTSecret   string `env:"JWT_SECRET" env-required:"true"`
	RedisURL    string `env:"REDIS_URL" env-required:"true"`
}

func LoadConfig() *Config {
	var cfg Config
	err := cleanenv.ReadEnv(&cfg)
	if err != nil {
		log.Fatalf("FATAL: Startup configuration error: %v", err)
		os.Exit(1)
	}
	return &cfg
}
```

---

## 3. Production Secrets Management & Threat Matrix

| Threat / Risk | Insecure Pattern | Production-Grade Mitigation |
| :--- | :--- | :--- |
| **Credential Exfiltration via Git** | Committing `.env` file to Git repository | Strictly include `.env*` in `.gitignore`; enforce pre-commit scan using `gitleaks`. |
| **Silent Runtime Failure** | Accessing missing variable 3 days after deployment inside a payment webhook | Fail-fast startup validation gate checks all variables before application accepts traffic. |
| **Plain-Text Secret Logging** | Logging config object directly (`console.log(config)`) | Implement automated recursive secret masking (`***`) for any key matching `password`, `secret`, `key`, `token`. |
| **Disk Inspection Exploits** | Leaving plaintext `.env` on container production filesystem | Inject secrets in-memory at runtime via orchestrator (Kubernetes Secrets, Vault Agent, ECS Task Definition). |

---

## 4. Junior-Friendly `.env.example` Protocol

Every variable in `.env.example` must adhere to the **3-Point Documentation Standard**:
1. **Purpose**: What feature or subsystem uses this value?
2. **Format / Dialect**: What is the valid syntax, protocol prefix, or allowed enum list?
3. **Local Generation / Source**: Exact CLI command or local service reference (e.g. `docker-compose up -d postgres`) to obtain it.
