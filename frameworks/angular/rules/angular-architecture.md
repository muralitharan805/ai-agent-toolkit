---
trigger: always_on
---

# Angular Architecture Rules

When implementing Angular features, you MUST follow these architectural rules:

## 1. Centralized API Communications
- **No Direct HttpClient in Components:** Components must NEVER inject `HttpClient` directly to fetch data.
- **Dedicated Services:** All API requests must be encapsulated within dedicated API or feature-specific data services (e.g., `ApiService`, `UserService`).
- **Generic/Base Services:** Common API patterns (GET, POST, PUT, DELETE, query params serialization, headers) should be delegated to a central generic service or class to reuse logic.

## 2. Centralized Exception Handling
- **No Ad-Hoc Console Errors:** Avoid catching and logging errors directly inside components unless it requires specific local recovery UI state.
- **Global Error Handler:** Use a custom implementation of Angular's `ErrorHandler` (e.g., `GlobalErrorHandler`) to catch and report all uncaught runtime exceptions globally (to logging services, toast notifications, etc.).
- **HTTP Interceptors:** Use an `HttpInterceptor` to intercept HTTP errors globally (e.g., handling 401 Unauthorized, 403 Forbidden, 500 Server Error) and dispatch them to notification systems or authentication handlers.

## 3. Separation of Concerns
- **Dumb Components:** Keep components focused purely on rendering the UI and handling user interactions. 
- **Business Logic in Services:** Move all heavy business logic, state transformations, API communications, and error handling orchestration to injectable services.
