# Prisma Migrations, Connection Lifecycle & Database Seeding

This reference details the standards for version-controlled database migrations, seed data pipelines, and connection lifecycle management in enterprise NestJS backends.

---

## 1. Migration-Only Database Schema Changes

All schema alterations (table creations, column additions, indexes) must be tracked through version-controlled migration files.

### Development Workflow:
```bash
# 1. Update schema.prisma
# 2. Generate and apply migration:
pnpm prisma migrate dev --name add_user_roles

# 3. Generate updated Prisma Client types:
pnpm prisma generate
```

### Production CI/CD Workflow:
In production environments, never run `prisma migrate dev`. Use the non-interactive deployment command:
```bash
pnpm prisma migrate deploy
```

---

## 2. Automated Database Seeder Architecture (`prisma/seed.ts`)

Seed scripts must be idempotent so that running them multiple times does not corrupt existing data or fail with duplicate key errors.

### Upsert Pattern for Seeders:
```typescript
await prisma.user.upsert({
  where: { email: 'admin@example.com' },
  update: {},
  create: {
    email: 'admin@example.com',
    name: 'System Administrator',
    password: hashedPassword,
    role: 'ADMIN',
  },
});
```

### `package.json` Configuration:
```json
{
  "scripts": {
    "db:migrate": "prisma migrate dev",
    "db:seed": "ts-node prisma/seed.ts"
  },
  "prisma": {
    "seed": "ts-node prisma/seed.ts"
  }
}
```

---

## 3. NestJS Prisma Service Lifecycle Management

```typescript
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit(): Promise<void> {
    await this.$connect();
  }

  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
  }
}
```

By binding connection management to NestJS module lifecycle hooks, connections cleanly drain during container restarts without hanging active transactions.
