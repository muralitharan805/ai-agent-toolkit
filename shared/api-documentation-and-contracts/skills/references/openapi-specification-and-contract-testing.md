# OpenAPI Specification Architecture & Consumer-Driven Contract Testing

## Overview

APIs serve as formal contracts between backend services, frontend web apps, mobile clients, and third-party partners. Unclear documentation, undocumented error payloads, and breaking schema changes cause silent client regressions, frontend blank screens, and integration delays.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    API Contract & Documentation Governance                   │
└──────────────────────────────────────────────────────────────────────────────┘
  Backend Service (Provider)                   Frontend / Mobile (Consumer)
         │                                                    │
         ├─────────────────── OpenAPI 3.x Spec ───────────────┤ (Client SDK Gen)
         │                    (Schemas + Examples)            │
         │                                                    │
         ▼                                                    ▼
  [Pact Verification Suite] ◄──── Pact Contract JSON ──── [Consumer Pact Tests]
         │
         ▼
  [CI/CD can-i-deploy Gate] ──► Passes? Safe to deploy to production!
```

---

## 1. OpenAPI 3.x Core Architecture

### Structure of an Enterprise OpenAPI Document
```yaml
openapi: 3.1.0
info:
  title: Core Orders Service API
  version: 1.0.0
  description: Handles order placement, inventory reservations, and billing.
servers:
  - url: https://api.example.com/v1
    description: Production Environment
  - url: https://staging-api.example.com/v1
    description: Staging Environment
paths:
  /orders:
    post:
      summary: Create an order
      operationId: createOrder
      tags: [Orders]
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Order created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderResponse'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 2. Code-First vs. Design-First Approaches

| Approach | Advantages | Disadvantages | Best Used For |
| :--- | :--- | :--- | :--- |
| **Code-First** (Decorators / Annotations) | Code and docs never drift; automatic sync on compilation; zero context-switching for developers. | API design is coupled to programming language types; frontend cannot review before code is written. | Internal REST APIs, agile full-stack teams. |
| **Design-First** (OpenAPI YAML authored first) | Frontend and backend agree on contract upfront; mock servers (Prism) allow parallel development. | Requires rigorous discipline to ensure backend implementation does not drift from YAML spec. | Public partner APIs, multi-team enterprise platforms. |

---

## 3. Consumer-Driven Contract Testing (Pact Framework)

In microservices and decoupled web/mobile architectures, traditional end-to-end (E2E) testing environments are brittle, slow, and expensive. Mocks in unit tests inevitably drift from the real provider.

### The Pact Testing Flow
1. **Consumer Defines Expectations**:
   Frontend runs tests against a local Pact mock server:
   `"When I send POST /orders with payload X, I expect 201 Created with schema Y"`.
2. **Pact Generates Contract**:
   A `.json` pact file is committed to a central Pact Broker.
3. **Provider Verifies Contract**:
   In CI/CD, the backend provider downloads consumer pacts and replays the requests against its actual controller:
   `pact-broker verify --provider-base-url http://localhost:3000`.
4. **Pre-Deployment Gate**:
   `pact-broker can-i-deploy --pacticipant orders-service --version 2.1.0 --to-environment production`.

---

## 4. Breaking vs. Non-Breaking Schema Evolution

| Mutation Type | Classification | Governance Requirement |
| :--- | :--- | :--- |
| Adding an optional request parameter | **Non-Breaking** | Document in OpenAPI; safe to release. |
| Adding a new response field | **Non-Breaking** | Safe (assuming consumers ignore unknown properties). |
| Renaming an existing field | **BREAKING** | Forbidden in same version. Must support alias or bump major version (`v2`). |
| Removing an existing field | **BREAKING** | Deprecate with `Sunset` header first; remove only in next major version. |
| Changing field type (`string` $\rightarrow$ `number`) | **BREAKING** | Major version increment required. |
| Making an optional parameter required | **BREAKING** | Major version increment required. |
| Changing HTTP response status code | **BREAKING** | Major version increment required. |
