---
trigger: always_on
description: "Enforces that all skills and rules generated or edited in this workspace reflect senior principal engineer expertise, modern industry standards, zero duplication, smart upsert behavior, modular directory bundling (references, scripts, assets, evals), progressive disclosure, and strict YAML frontmatter GUI compatibility."
---

# Expert Authoring, Principal Mindset & Technical Rigor Rule

## Description
This rule mandates that whenever the AI agent creates or modifies modular skills or rules, the generated content must reflect the depth, battle-tested foresight, and engineering rigor of a seasoned Principal Software Architect. Generated context must reject superficial "tutorial-ware", strictly enforce current modern framework standards, proactively eliminate deprecated APIs, provide resilient production-ready solutions, maintain zero duplication, and adhere to 100% GUI-compatible YAML frontmatter.

## Constraints

### 1. Principal Architect Mindset & Production-Grade Depth
- **Prohibition of "Tutorial-Ware"**: The agent MUST reject simplistic "Hello World" or superficial happy-path examples that fail under real-world conditions.
- **Enterprise Resilience Standards**: Generated solutions and patterns MUST account for:
  - Robust boundary validation and defensive precondition checks.
  - Concurrency safety, race condition mitigation, and network failure fallbacks.
  - Mandatory lifecycle teardowns and memory leak prevention (e.g. `takeUntilDestroyed()`, stream unsubscriptions, component unmounting).
  - Explicit error boundaries, structured exceptions, and correlation ID tracing.
- **Battle-Tested Perspective**: Context must be authored from the perspective of an engineer maintaining mission-critical production systems, prioritizing maintainability, debuggability, and performance under load.

### 2. Strict Currency & Anti-Deprecation Invariant
- **Current Framework Versions Only**: All generated skills, rules, and code examples MUST reflect the latest stable framework specifications:
  - **Angular (v19+)**: Standalone components ONLY, fine-grained Signals reactivity (`signal`, `computed`, `linkedSignal`, `resource`), native block control flow (`@if`, `@for`, `@switch`), Typed Forms, and functional DI (`inject()`).
  - **NestJS**: Clean Architecture, strict DTO validation with class-validator/Zod, functional route guards, and correlation ID propagation.
  - **Infrastructure**: Modern Compose v2 specifications, multi-stage BuildKit builds, non-root runtime security, and pnpm package management.
- **Strict Prohibition of Deprecated Patterns**: The agent MUST NOT generate or recommend obsolete patterns, including:
  - Angular `NgModule` encapsulation, `@Input()`/`@Output()` decorators, `BehaviorSubject` for local component state, or untyped forms.
  - Node.js legacy CommonJS `require()` in modern TypeScript ESM projects.
  - Legacy Docker `links` or single-stage root-user image builds.
- **Legacy vs. Modern Matrix**: Every skill's `## Gotchas` section MUST contrast common legacy/deprecated pitfalls against modern recommended production replacements.

### 3. Linguistic & Technical Rigor
- The agent MUST write all generated skills and rules in professional technical English with zero conversational fluff.
- Generated code snippets MUST be production-ready and strictly typed (zero `any` types).
- Public APIs and architectural services MUST include TSDoc / JSDoc block comments explaining business purpose, parameters, return types, and exceptions.

### 4. Deduplication & Smart Upsert
- Before creating a new file, the agent MUST inspect the workspace (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`) for existing skills or rules covering the target topic.
- If a related file exists, the agent MUST update and merge new requirements into the existing file instead of creating duplicate files.

### 5. Modular Skill Bundling & Progressive Disclosure (5-Pillar Standard)
- **3-Tier Progressive Disclosure**: Skills MUST be structured so `name` and `description` act as Tier 1 metadata, `SKILL.md` body (< 500 lines) acts as Tier 2 core guidance, and deep documentation lives in Tier 3 on-demand files.
- **5-Pillar Bundle Architecture**: Complex domain or procedural skills MUST scaffold a modular bundle:
  - `SKILL.md`: Core procedures, relative links, and mandatory `## Gotchas`.
  - `references/[topic].md`: Granular technical guides, runbooks, and API specs.
  - `scripts/[tool].py|sh`: Self-contained, idempotent automation tools emitting JSON to `stdout` and diagnostics to `stderr`.
  - `assets/[template].json`: Concrete output templates, starter files, and JSON schemas.
  - `evals/evals.json`: Quality verification test cases with objective, binary assertions.

### 6. Rule Size, Triggers & Validation
- Rule files MUST target 6,000–8,000 characters (optimal for token economy; hard ceiling 12,000 characters).
- Rules MUST select the most token-efficient trigger: `model_decision` for situational logic, `glob` with `globs: [...]` for filetype patterns, or `manual`. Avoid blanket `always_on` defaults except for universal workspace invariants.
- All rules MUST validate cleanly via `python3 shared/generators/skills/generate-rule/scripts/validate_rule.py`.

### 7. Workflows Sunset & Procedural Skills Mandate
- Standalone `.agents/workflows/*.md` files are deprecated by Google Antigravity IDE and STRICTLY FORBIDDEN for new workflows.
- All sequential processes MUST be authored as **Procedural Skills** under `skills/[skill-name]/` with bundled scripts and checklists.
- All skills MUST validate cleanly via `python3 shared/generators/skills/generate-skill/scripts/validate_skill.py`.

### 8. YAML Frontmatter GUI Compatibility
- **Skills**: Must include `name` (kebab-case, matching directory) and `description` (1–1024 characters, imperative phrasing).
- **Rules**: Must include `description` and valid `trigger` (`model_decision`, `glob`, `always_on`, or `manual`). When `trigger: glob`, `globs: [...]` is mandatory.

## Examples

### 1. Naive Tutorial-Ware vs. Principal Architect Implementation

```typescript
// ❌ INCORRECT: Naive "Tutorial-Ware" (Deprecated APIs, memory leak, unmanaged errors, any type)
@Component({ selector: 'app-user', template: `<div *ngIf="user">{{ user.name }}</div>` })
export class UserComponent implements OnInit {
  @Input() userId: any;
  user: any;
  constructor(private http: HttpClient) {}
  ngOnInit() {
    this.http.get('/api/users/' + this.userId).subscribe(res => this.user = res); // Memory leak!
  }
}

// ✅ CORRECT: Principal Architect Production-Grade (Angular 19+ Signals, Zoneless, Clean Memory Teardown, Strict Types)
@Component({
  selector: 'app-user',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
  template: `
    @if (userResource.isLoading()) {
      <div class="skeleton-loader" aria-busy="true">Loading profile...</div>
    } @else if (userResource.value(); as user) {
      <article class="user-card">
        <h3>{{ user.displayName }}</h3>
        <p>{{ user.email }}</p>
      </article>
    } @else if (userResource.error()) {
      <div class="error-banner" role="alert">Unable to load user profile.</div>
    }
  `
})
export class UserComponent {
  private readonly userService = inject(UserService);
  readonly userId = input.required<string>();

  // Asynchronous reactive resource with automatic abort/cancellation semantics
  readonly userResource = rxResource({
    request: () => this.userId(),
    loader: ({ request: id }) => this.userService.getUserById(id)
  });
}
```

### 2. Valid Procedural Skill Definition
```yaml
---
name: deploy-angular-spa-cloudflare
description: "Executes 4-step deployment pipeline for Angular SPA to Cloudflare Pages. Triggered by '/deploy-angular-spa-cloudflare' or 'deploy-spa:'."
---
```
