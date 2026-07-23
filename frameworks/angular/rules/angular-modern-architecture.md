---
trigger: always_on
description: "Enforces modern Angular (v19+) architectural standards including Standalone components, Signals reactivity (signal, computed, input, output, resource), modern control flow (@if, @for), functional dependency injection (inject), and OnPush change detection."
---
# Angular Modern Architecture & Reactivity Rule

## Description
This rule enforces enterprise-grade Angular standards based on modern Angular framework paradigms (v19+). It mandates full adoption of Standalone components, fine-grained Signal reactivity, built-in control flow syntax, functional dependency injection, and OnPush/Zoneless change detection while strictly prohibiting legacy patterns such as `NgModule` declarations, class-based router guards, decorator-based inputs/outputs, and RxJS `BehaviorSubject` for local component state.

## Constraints
- **Standalone Architecture**: ALL components, directives, and pipes MUST be standalone. `NgModule` declarations MUST NOT be used for feature module encapsulation.
- **Signal Inputs & Outputs**: MUST use `input()`, `input.required()`, `output()`, and `model()` signal primitives instead of `@Input()` and `@Output()` property decorators.
- **Signal State & Reactivity**: Local component state MUST be managed using `signal()`, `computed()`, `linkedSignal()`, and asynchronous `resource()` / `rxResource()`. RxJS `BehaviorSubject` or `Subject` MUST NOT be used for component-local reactivity.
- **Control Flow Syntax**: MUST use built-in block syntax (`@if`, `@else`, `@for (item of items; track item.id)`, `@switch`) instead of legacy directive syntax (`*ngIf`, `*ngFor`, `*ngSwitch`).
- **Functional Dependency Injection**: Services, router tokens, and dependencies MUST be injected using the `inject(Token)` function instead of constructor parameter injection.
- **Change Detection**: Components MUST explicitly configure `changeDetection: ChangeDetectionStrategy.OnPush` or run within a zoneless change detection environment (`provideExperimentalZonelessChangeDetection()`).
- **Functional Interceptors & Guards**: Route guards, resolvers, and HTTP interceptors MUST be declared as functional constructs (`CanActivateFn`, `HttpInterceptorFn`) rather than injectable classes.

## Examples

- **Correct implementation:**
```typescript
// user-profile.component.ts
import { Component, ChangeDetectionStrategy, inject, input, output, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserService, User } from './user.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="user-card">
      @if (isLoading()) {
        <div class="skeleton-loader">Loading profile...</div>
      } @else if (user(); as currentUser) {
        <header class="card-header">
          <h2>{{ displayName() }}</h2>
          <span class="badge">{{ currentUser.role }}</span>
        </header>
        <p>{{ currentUser.email }}</p>
        <button type="button" (click)="onSelectUser()">Select Profile</button>
      } @else {
        <p class="empty-state">No profile selected.</p>
      }
    </section>
  `,
  styleUrl: './user-profile.component.scss'
})
export class UserProfileComponent {
  private readonly userService = inject(UserService);

  // Signal Inputs & Outputs
  readonly userId = input.required<string>();
  readonly profileSelected = output<string>();

  // Reactive State & Computed Signals
  readonly isLoading = signal<boolean>(false);
  readonly user = signal<User | null>(null);
  readonly displayName = computed(() => {
    const current = this.user();
    return current ? `${current.firstName} ${current.lastName}` : 'Guest';
  });

  onSelectUser(): void {
    const current = this.user();
    if (current) {
      this.profileSelected.emit(current.id);
    }
  }
}
```

- **Incorrect implementation:**
```typescript
// Legacy Anti-Pattern: NgModule, Constructor DI, @Input/@Output, *ngIf/*ngFor, BehaviorSubject
import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { UserService } from './user.service';

@Component({
  selector: 'app-user-profile',
  template: `
    <div *ngIf="isLoading">Loading...</div>
    <div *ngIf="user">
      <h2>{{ user.name }}</h2>
      <button (click)="select.emit(user.id)">Select</button>
    </div>
  ` // Violation: *ngIf directive, no OnPush, missing track
})
export class UserProfileComponent implements OnInit {
  @Input() userId!: string; // Violation: Decorator @Input instead of input()
  @Output() select = new EventEmitter<string>(); // Violation: EventEmitter instead of output()
  
  user$ = new BehaviorSubject<any>(null); // Violation: BehaviorSubject for local state & 'any' type
  isLoading = false;

  constructor(private userService: UserService) {} // Violation: Constructor DI instead of inject()

  ngOnInit(): void {}
}
```
