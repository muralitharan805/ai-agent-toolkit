import { Module } from '@nestjs/common';
import { FeatureController } from './feature.controller';
import { FeatureService } from './feature.service';
import { FeaturePrismaRepository } from './feature-prisma.repository';
import { FEATURE_REPOSITORY } from './feature-repository.interface';

/**
 * Domain module configuring FeatureController, FeatureService,
 * and binding the concrete repository adapter to the injection token.
 */
@Module({
  controllers: [FeatureController],
  providers: [
    FeatureService,
    {
      provide: FEATURE_REPOSITORY,
      useClass: FeaturePrismaRepository,
    },
  ],
  exports: [FeatureService, FEATURE_REPOSITORY],
})
export class FeatureModule {}
