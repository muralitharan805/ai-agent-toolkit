import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

/**
 * Singleton database service managing Prisma ORM connection lifecycle
 * and ensuring clean connection pool drainage on container shutdown.
 */
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PrismaService.name);

  /**
   * Connects to the database when the host module initializes.
   */
  async onModuleInit(): Promise<void> {
    try {
      await this.$connect();
      this.logger.log('✅ Database connection pool initialized successfully');
    } catch (error) {
      this.logger.error('❌ Failed to connect to database', error);
      throw error;
    }
  }

  /**
   * Disconnects and releases active database connections when the application terminates.
   */
  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
    this.logger.log('🛑 Database connection pool closed gracefully');
  }
}
