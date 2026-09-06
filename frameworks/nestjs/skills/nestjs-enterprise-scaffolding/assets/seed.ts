import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

/**
 * Database seeding script populating initial roles and administrative accounts.
 * Safe to execute idempotently across staging and local development.
 */
async function main(): Promise<void> {
  console.log('🌱 Starting database seeding...');

  const hashedPassword = await bcrypt.hash('AdminP@ss123!', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@example.com' },
    update: {},
    create: {
      email: 'admin@example.com',
      name: 'System Administrator',
      password: hashedPassword,
      role: 'ADMIN',
    },
  });

  console.log(`✅ Seeded Admin User: ${admin.email}`);
}

main()
  .catch((e: unknown) => {
    console.error('❌ Seeding error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
