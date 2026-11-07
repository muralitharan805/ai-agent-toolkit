import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { AppModule } from './app.module';

/**
 * Bootstraps the enterprise NestJS application with production security,
 * global pipes, OpenAPI documentation, and graceful shutdown hooks.
 */
async function bootstrap(): Promise<void> {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // Enable graceful container shutdown handling (SIGTERM, SIGINT)
  app.enableShutdownHooks();

  // Production Security Headers & CORS
  app.use(helmet());
  app.enableCors({ origin: true, credentials: true });

  // Uniform API Routing Prefix
  app.setGlobalPrefix('api/v1');

  // Strict Request Body Validation Pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // OpenAPI / Swagger Documentation Setup
  const swaggerConfig = new DocumentBuilder()
    .setTitle('Enterprise NestJS API')
    .setDescription('Production Backend API Documentation')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env['PORT'] ? parseInt(process.env['PORT'], 10) : 3000;
  await app.listen(port);
  logger.log(`🚀 Application running on http://localhost:${port}/api/v1`);
  logger.log(`📚 Swagger Docs available on http://localhost:${port}/api/docs`);
}

void bootstrap();
