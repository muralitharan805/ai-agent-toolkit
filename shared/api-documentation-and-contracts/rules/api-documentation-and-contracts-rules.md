---
trigger: model_decision
description: "Enforces OpenAPI 3.x documentation standards, complete success and error response schemas, consumer-driven contract testing (Pact), and production documentation access restrictions."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# API Documentation & Contract Testing Standards

## Description
Enforces exhaustive OpenAPI 3.x documentation, API contract governance, and consumer-driven contract verification across all backend services, REST APIs, and microservices. Mandates that every public and internal endpoint is fully documented with schema definitions, realistic examples, and complete error response models. Establishes production access restrictions for interactive documentation sandboxes (Swagger UI / Scalar), enforces consumer-driven contract testing (Pact framework) to prevent breaking frontend and downstream consumers, and requires clear deprecation timelines and changelog maintenance.

## Constraints

### 1. Mandatory OpenAPI 3.x Completeness
- All backend HTTP APIs MUST publish a complete, valid OpenAPI 3.x specification (auto-generated from code annotations or maintained as a design-first schema).
- Every endpoint definition MUST include:
  - Summary and detailed description explaining business intent.
  - Operation tags for logical grouping (e.g. `Orders`, `Authentication`, `Billing`).
  - Request body schemas with explicit type assertions and non-empty, realistic examples.
  - Parameter definitions (path, query, and header parameters) with format constraints.
  - Authentication security requirements (`security: [{ BearerAuth: [] }]`).
  - Applicable rate limit constraints.
- Undocumented public or internal API routes are STRICTLY FORBIDDEN.

### 2. Exhaustive Error Response Schema Modeling
- Documenting only HTTP 200/201 success responses while omitting failure responses is STRICTLY FORBIDDEN.
- Every endpoint MUST explicitly declare schemas and examples for all applicable HTTP error statuses:
  - `400 Bad Request` (Validation errors with field details).
  - `401 Unauthorized` (Missing or invalid credentials).
  - `403 Forbidden` (Insufficient role permissions or tenant boundary violation).
  - `404 Not Found` (Target resource identifier does not exist).
  - `409 Conflict` (Duplicate business natural key or idempotency in-progress lock).
  - `422 Unprocessable Entity` (Semantic business invariant failure).
  - `429 Too Many Requests` (Rate limit throttled).
  - `500 Internal Server Error` (Unhandled operational failure).
- Error schemas MUST conform to the standard error response envelope (`{ success: false, error: { code, message, details } }`).

### 3. Production Documentation Sandbox Lockdown
- Publicly exposing interactive API sandboxes (e.g. Swagger UI, Scalar, Redoc at `GET /docs`) or raw OpenAPI specifications (`GET /docs/openapi.json`) in production environments is STRICTLY FORBIDDEN.
- **Security Justification**: Interactive documentation discloses internal architecture routes, administrative endpoints, schema shapes, parameter validations, and dependency versions directly to attackers, facilitating automated vulnerability scanning.
- **Production Requirement**: Documentation routes MUST either be disabled in production (`NODE_ENV === 'production'`) or protected behind an internal VPN, IP whitelist, or administrative authentication gate.

### 4. Consumer-Driven Contract Testing (Pact Framework)
- Critical API boundaries between frontend applications, mobile clients, and upstream microservices MUST be governed by Consumer-Driven Contract Tests (using the Pact framework or equivalent).
- **Workflow Invariant**:
  1. API consumers define contract expectations (pact files) in their test suites.
  2. The provider backend executes pact verification as an automated CI/CD gate before merge.
  3. Pull requests that introduce breaking changes (removed fields, altered types, modified route paths) MUST fail the CI pipeline (`pact-broker can-i-deploy`).

### 5. Non-Breaking Evolution, Deprecation & CHANGELOG
- API changes MUST be strictly additive (adding optional fields or new endpoints).
- Renaming existing fields, removing fields, or altering parameter types are classified as BREAKING CHANGES and require incrementing the major API version (`/api/v1` $\rightarrow$ `/api/v2`).
- Deprecated endpoints MUST be explicitly annotated with `deprecated: true` in the OpenAPI spec and emit standard `Deprecation: true` and `Sunset: <date>` HTTP response headers.
- Every release MUST record API additions, deprecations, and fixes in `CHANGELOG.md`.

## Examples

### 1. Complete OpenAPI Endpoint Annotation (NestJS / TypeScript)

```typescript
// ✅ CORRECT: Comprehensive OpenAPI documentation with success, error, and security models
@ApiTags('Orders')
@ApiBearerAuth('BearerAuth')
@Controller('orders')
export class OrdersController {
  @Post()
  @ApiOperation({
    summary: 'Create a new customer order',
    description: 'Validates order items, reserves inventory, and queues order fulfillment.',
  })
  @ApiBody({ type: CreateOrderDto })
  @ApiResponse({ status: 201, description: 'Order successfully created', type: OrderResponseDto })
  @ApiResponse({ status: 400, description: 'Validation failure on order payload', type: ApiErrorEnvelopeDto })
  @ApiResponse({ status: 401, description: 'Missing or expired authentication token', type: ApiErrorEnvelopeDto })
  @ApiResponse({ status: 409, description: 'Duplicate order idempotency key', type: ApiErrorEnvelopeDto })
  @ApiResponse({ status: 500, description: 'Internal server error', type: ApiErrorEnvelopeDto })
  async createOrder(@Body() dto: CreateOrderDto, @Req() req: AuthenticatedRequest): Promise<OrderResponseDto> {
    return this.ordersService.create(dto, req.user.id);
  }
}
```

### 2. Production Documentation Route Guard

```typescript
// ✅ CORRECT: Disabling or IP-restricting Swagger documentation in production
export function setupApiDocumentation(app: INestApplication): void {
  const isProduction = process.env.NODE_ENV === 'production';
  const enableDocsInProd = process.env.ENABLE_INTERNAL_DOCS === 'true';

  if (isProduction && !enableDocsInProd) {
    // Disable Swagger completely in public production environments
    return;
  }

  const config = new DocumentBuilder()
    .setTitle('E-Commerce Core API')
    .setDescription('Production REST API documentation and contracts')
    .setVersion('1.0.0')
    .addBearerAuth({ type: 'http', scheme: 'bearer', bearerFormat: 'JWT' }, 'BearerAuth')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document, {
    swaggerOptions: { persistAuthorization: true },
  });
}
```
