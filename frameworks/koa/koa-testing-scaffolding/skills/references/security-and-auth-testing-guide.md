# Security, Authentication & IDOR Testing Guide (JavaScript)

## Purpose
This guide details testing strategies for Authentication, Role-Based Access Control (RBAC), and Object-Level Authorization (Insecure Direct Object References - IDOR) in Koa.js APIs in JavaScript.

---

## 1. Authentication Testing Standards

Every authenticated endpoint MUST be tested against the complete spectrum of token validity:

| Test Scenario | Input Authorization Header | Expected Status | Response Assertion |
| :--- | :--- | :--- | :--- |
| **Missing Header** | Omitted | `401 Unauthorized` | `{ success: false, message: 'Authentication required' }` |
| **Malformed Header** | `Bearer abc` (invalid JWT structure) | `401 Unauthorized` | `{ success: false, message: 'Malformed token' }` |
| **Expired Token** | Signed JWT with expired `exp` timestamp | `401 Unauthorized` | `{ success: false, message: 'Token expired' }` |
| **Tampered Signature** | Valid JWT payload with mismatched signature | `401 Unauthorized` | `{ success: false, message: 'Invalid token signature' }` |
| **Disabled User** | Valid JWT belonging to inactive/banned account | `401 Unauthorized` | `{ success: false, message: 'Account deactivated' }` |
| **Valid Token** | Valid cryptographically signed JWT | `200 OK` | Expected payload returned |

---

## 2. Role-Based Access Control (RBAC) Matrix Testing

When endpoints require specific roles (e.g. `ADMIN`, `AGENT`, `USER`), execute parameterized matrix tests:

```javascript
const { describe, it, expect } = require('vitest');
const request = require('supertest');
const { app } = require('../setup/app');
const { generateAuthToken } = require('../fixtures/auth.fixture');

describe('Admin User Deletion - RBAC Matrix', () => {
  const rolesAndExpectations = [
    { role: 'ADMIN', expectedStatus: 200 },
    { role: 'AGENT', expectedStatus: 403 },
    { role: 'USER', expectedStatus: 403 },
  ];

  rolesAndExpectations.forEach(({ role, expectedStatus }) => {
    it(`should return status ${expectedStatus} when invoked by role: ${role}`, async () => {
      const token = generateAuthToken({ userId: 999, role });

      const res = await request(app.callback())
        .delete('/api/users/123')
        .set('Authorization', `Bearer ${token}`);

      expect(res.status).toBe(expectedStatus);
    });
  });
});
```

---

## 3. Object-Level Authorization (IDOR Prevention) Testing

### IDOR Test Implementation Pattern
```javascript
const { describe, it, expect, beforeAll } = require('vitest');
const request = require('supertest');
const { app } = require('../setup/app');
const { generateAuthToken } = require('../fixtures/auth.fixture');
const { Property } = require('../../src/models/property.model');

describe('IDOR Prevention - Property Mutations', () => {
  let userAToken;
  let userBToken;
  let userAPropertyId;

  beforeAll(async () => {
    // Generate credentials for two distinct valid users
    userAToken = generateAuthToken({ userId: 101, role: 'AGENT' });
    userBToken = generateAuthToken({ userId: 102, role: 'AGENT' });

    // Seed property owned strictly by User A
    const property = await Property.create({
      title: 'User A Private Listing',
      ownerId: 101,
      price: 450000
    });
    userAPropertyId = property.id;
  });

  it('should allow Owner (User A) to update their property', async () => {
    const res = await request(app.callback())
      .put(`/api/properties/${userAPropertyId}`)
      .set('Authorization', `Bearer ${userAToken}`)
      .send({ price: 475000 });

    expect(res.status).toBe(200);
    expect(res.body.data.price).toBe(475000);
  });

  it('should REJECT User B when attempting to update User A property', async () => {
    const res = await request(app.callback())
      .put(`/api/properties/${userAPropertyId}`)
      .set('Authorization', `Bearer ${userBToken}`)
      .send({ price: 200000 }); // Malicious price tampering

    expect(res.status).toBe(403);
    expect(res.body.success).toBe(false);
  });
});
```
