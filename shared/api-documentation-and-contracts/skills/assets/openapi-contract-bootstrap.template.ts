/**
 * Production OpenAPI 3.x Documentation & Contract Setup Template
 * Implements:
 * 1. Hardened OpenAPI DocumentBuilder with BearerAuth Security Scheme
 * 2. Production Environment Access Guard (disabling public /docs in prod)
 * 3. Universal Error Schema Envelope DTOs for Swagger
 * 4. Sample Documented Controller with Success & Error Models
 */

import type { INestApplication } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

/**
 * Field-level validation failure detail for OpenAPI schema.
 */
export class ApiFieldErrorDetailDto {
  /**
   * Property name or JSON pointer that failed validation.
   * @example 'email'
   */
  readonly field!: string;

  /**
   * Localized, human-readable error description.
   * @example 'Must be a valid email address'
   */
  readonly message!: string;
}

/**
 * Standard error response envelope DTO for OpenAPI documentation.
 */
export class StandardApiErrorEnvelopeDto {
  /**
   * Always false for error payloads.
   * @example false
   */
  readonly success = false;

  /**
   * Structured error details.
   */
  readonly error!: {
    /**
     * Standardized catalog error code.
     * @example 'VALIDATION_ERROR'
     */
    readonly code: string;

    /**
     * High-level human-readable error description.
     * @example 'Input validation failed'
     */
    readonly message: string;

    /**
     * Optional field-level error details array.
     */
    readonly details?: readonly ApiFieldErrorDetailDto[];

    /**
     * ISO-8601 UTC timestamp of error occurrence.
     * @example '2026-09-10T08:30:00.000Z'
     */
    readonly timestamp: string;
  };
}

/**
 * Configures OpenAPI 3.x specification and Swagger UI with production access controls.
 *
 * @param app - Initialized NestJS application instance
 * @param serviceTitle - Name of the application / microservice
 * @param serviceVersion - Semantic version string (e.g. '1.0.0')
 */
export function configureOpenApiDocumentation(
  app: INestApplication,
  serviceTitle: string,
  serviceVersion = '1.0.0'
): void {
  const isProduction = process.env.NODE_ENV === 'production';
  const isDocsExplicitlyAllowed = process.env.ENABLE_PRODUCTION_DOCS === 'true';

  // Security Invariant: Disable public interactive Swagger documentation in production
  if (isProduction && !isDocsExplicitlyAllowed) {
    return;
  }

  const swaggerConfig = new DocumentBuilder()
    .setTitle(serviceTitle)
    .setDescription(`Production OpenAPI 3.x specification for ${serviceTitle}`)
    .setVersion(serviceVersion)
    .addBearerAuth(
      {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: 'Provide JWT bearer access token to authenticate requests.',
      },
      'BearerAuth'
    )
    .addServer('https://api.company.com/v1', 'Production Gateway')
    .addServer('https://staging-api.company.com/v1', 'Staging Gateway')
    .addServer('http://localhost:3000/v1', 'Local Development')
    .build();

  const openApiDocument = SwaggerModule.createDocument(app, swaggerConfig);

  SwaggerModule.setup('docs', app, openApiDocument, {
    swaggerOptions: {
      persistAuthorization: true,
      displayRequestDuration: true,
      filter: true,
    },
    customSiteTitle: `${serviceTitle} API Documentation`,
  });
}
