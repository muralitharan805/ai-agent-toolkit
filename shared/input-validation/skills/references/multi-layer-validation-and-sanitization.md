# Multi-Layer Input Validation, Mass Assignment & Sanitization Reference

## 1. Architectural Philosophy

> **Fail at the Gate**: Never permit unvalidated, malformed, or malicious user input to penetrate the transport layer and reach domain services or database repositories. Inbound validation is the first line of defense against data corruption, injection, and privilege escalation.

```
Incoming HTTP Request (Body, Query, Params)
        │
┌───────▼─────────────────────────────────────────────────┐
│ Layer 1: Schema / Type Validation (Transport Boundary)  │
│ - Correct types, required fields, lengths, regex enums  │
│ - Strict Whitelist Mode (Strip / reject unknown props)  │
└───────┬─────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────┐
│ Layer 2: Business Rule Validation (Domain Boundary)     │
│ - Entity exists? Account has sufficient balance?        │
│ - Verified inside Application Services & Domain Models  │
└───────┬─────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────┐
│ Layer 3: Persistence Boundary                           │
│ - Unique constraints, foreign keys, database triggers   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Mass Assignment Attack Mechanics & Mitigation

### The Attack
In an application updating a user profile:
1. Expected fields: `{ displayName: string, bio: string }`
2. An attacker submits:
   ```json
   {
     "displayName": "Hacker",
     "bio": "Malicious",
     "role": "SUPERADMIN",
     "isEmailVerified": true,
     "accountBalance": 1000000
   }
   ```
3. If the backend passes `req.body` directly to an ORM update query (`userRepo.update(id, req.body)`), the attacker escalates privileges and alters sensitive database columns.

### The Mitigation: Whitelist Mode
- **Zod**: `.strict()` rejects unexpected keys; `.strip()` silently drops unexpected keys.
- **class-validator / class-transformer**: `{ whitelist: true, forbidNonWhitelisted: true }`.
- **Pydantic v2**: `model_config = SettingsConfigDict(extra='forbid')`.

---

## 3. Standard Regex & Formatting Catalog

```typescript
// E.164 International Phone Number Standard
export const E164_PHONE_REGEX = /^\+[1-9]\d{1,14}$/;

// Standard RFC-5322 Simplified Email Pattern
export const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// UUIDv4 Format Pattern
export const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Secure Alphanumeric Slug Pattern
export const SLUG_REGEX = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
```

---

## 4. Multi-Language Validation Implementations

### TypeScript / Node.js (Zod)
```typescript
import { z } from 'zod';

export const CreateOrderDtoSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(z.object({
    productId: z.string().uuid(),
    quantity: z.number().int().positive().max(999),
    unitPriceInCents: z.number().int().nonnegative(),
  })).min(1, 'Order must contain at least one item'),
  shippingAddress: z.object({
    street: z.string().trim().min(3).max(200),
    postalCode: z.string().trim().min(3).max(20),
    countryCode: z.string().length(2).toUpperCase(),
  }),
}).strict(); // Enforce whitelist mode
```

### Python (Pydantic v2)
```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID

class CreateUserDto(BaseModel):
    model_config = ConfigDict(extra='forbid') # Reject unknown keys

    email_address: EmailStr
    display_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(pattern=r'^\+[1-9]\d{1,14}$')
    age: int = Field(ge=18, le=120)
```

### Go (go-playground/validator)
```go
package dto

type CreateUserRequest struct {
    Email       string `json:"email" validate:"required,email"`
    DisplayName string `json:"displayName" validate:"required,min=2,max=100"`
    Phone       string `json:"phone" validate:"required,e164"`
    Age         int    `json:"age" validate:"required,gte=18,lte=120"`
}
```
