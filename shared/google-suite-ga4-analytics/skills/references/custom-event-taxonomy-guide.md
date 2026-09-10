# GA4 Custom Event Taxonomy & Parameter Standard

## Overview
GA4 uses an event-based architecture where every user interaction is logged as an event. Developing a consistent, well-structured event taxonomy prevents naming fragmentation and ensures analytical dashboards scale seamlessly.

---

## 1. Naming Conventions & Rules
- **Casing**: Use strictly `snake_case` (lowercase letters and underscores). Never use PascalCase, camelCase, or spaces.
- **Length Limits**: Event names MUST NOT exceed 40 characters. Parameter names MUST NOT exceed 40 characters. Parameter string values MUST NOT exceed 100 characters.
- **Reserved Prefix**: NEVER prefix event names with `_`, `ga_`, `google_`, or `firebase_`. These are reserved for internal Google Analytics use.
- **Syntax Pattern**: Follow the `entity_action` pattern (e.g., `button_click`, `form_submit`, `file_download`, `report_generate`).

---

## 2. Standard Event Catalog

### Interaction Events
| Event Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `cta_click` | `cta_name`, `cta_location`, `target_url` | Tracks primary conversion buttons (e.g., "Sign Up Now"). |
| `modal_open` | `modal_id`, `trigger_source` | Tracks dialog modal appearances. |
| `file_download` | `file_name`, `file_extension`, `file_size_kb` | Tracks asset downloads (PDF, CSV, JSON). |

### Core Workflow Events
| Event Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `tool_execute` | `tool_id`, `input_type`, `execution_time_ms`, `status` | Tracks utility execution and performance. |
| `form_submit` | `form_id`, `form_step`, `submission_status` | Tracks multi-step form completion. |
| `search_perform` | `search_term_hash`, `results_count` | Tracks internal query searches (without PII). |

### Error & Exception Events
| Event Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `app_error` | `error_code`, `error_category`, `route_path` | Tracks client-side UI and network failures. |

---

## 3. Safe Wrapper Implementation (TypeScript)
Ensure tracking code never throws unhandled errors if `gtag` is blocked by ad blockers or privacy extensions:

```typescript
export interface AnalyticsEventPayload {
  readonly [paramName: string]: string | number | boolean | undefined;
}

/**
 * Safely dispatches custom GA4 event without risking runtime exceptions.
 *
 * @param eventName - Normalized snake_case event name
 * @param payload - Structured event parameter map
 */
export function dispatchSafeAnalyticsEvent(
  eventName: string,
  payload: AnalyticsEventPayload
): void {
  if (typeof window === 'undefined' || typeof window.gtag !== 'function') {
    return;
  }

  // Sanitize payload to strip undefined keys
  const sanitizedParams: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(payload)) {
    if (value !== undefined) {
      sanitizedParams[key] = value;
    }
  }

  window.gtag('event', eventName, sanitizedParams);
}
```

---

## 4. Custom Dimensions & Metric Registration
Emitting custom parameters in `gtag('event', ...)` is not sufficient for custom reporting. In GA4:
1. Navigate to **Admin > Data Display > Custom Definitions**.
2. Create **Custom Dimensions** for categorical parameters (e.g., `tool_id`, `error_category`).
3. Create **Custom Metrics** for numerical values (e.g., `execution_time_ms`, `results_count`).
