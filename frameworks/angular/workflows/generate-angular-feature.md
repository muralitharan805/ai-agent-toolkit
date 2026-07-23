---
trigger: manual
description: "Step-by-step execution workflow for generating an end-to-end Angular 19+ domain feature containing signal stores, asynchronous resources, container components, presentational UI components, and lazy-loaded routes."
---
# Generate Angular Feature Workflow

## Purpose
This workflow guides the agent through generating a complete, modular, domain-driven Angular feature implementing modern Signal reactivity (`signal`, `computed`, `resource`), Standalone UI composition, and typed routing.

## Step-by-Step Execution Protocol

### Step 1: Create Domain Models (`features/[feature]/models/`)
Define TypeScript interfaces and domain types:
```typescript
// src/app/features/tasks/models/task.model.ts
export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  createdAt: string;
}

export interface CreateTaskPayload {
  title: string;
  description: string;
}
```

### Step 2: Implement Signal Data Access Store (`features/[feature]/data-access/`)
Create an injectable service leveraging `signal`, `computed`, `rxResource` / `resource` for state management:
```typescript
// src/app/features/tasks/data-access/task-store.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';
import { Task, CreateTaskPayload } from '../models/task.model';

@Injectable({ providedIn: 'root' })
export class TaskStoreService {
  private readonly http = inject(HttpClient);

  readonly statusFilter = signal<'all' | 'pending' | 'completed'>('all');

  readonly tasksResource = rxResource({
    request: () => ({ filter: this.statusFilter() }),
    loader: ({ request }) => 
      this.http.get<Task[]>(`/api/tasks`, { params: { status: request.filter } })
  });

  readonly tasks = computed(() => this.tasksResource.value() ?? []);
  readonly isLoading = computed(() => this.tasksResource.isLoading());
  readonly pendingCount = computed(() => this.tasks().filter(t => t.status === 'pending').length);

  setFilter(filter: 'all' | 'pending' | 'completed'): void {
    this.statusFilter.set(filter);
  }

  addTask(payload: CreateTaskPayload): void {
    this.http.post<Task>('/api/tasks', payload).subscribe(() => {
      this.tasksResource.reload();
    });
  }
}
```

### Step 3: Create Presentational UI Component (`features/[feature]/ui/`)
Build presentational components with `input()`, `output()`, and `ChangeDetectionStrategy.OnPush`:
```typescript
// src/app/features/tasks/ui/task-item.component.ts
import { Component, ChangeDetectionStrategy, input, output } from '@angular/core';
import { Task } from '../models/task.model';

@Component({
  selector: 'app-task-item',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="task-card">
      <h3>{{ task().title }}</h3>
      <p>{{ task().description }}</p>
      <span class="status-tag">{{ task().status }}</span>
      <button type="button" (click)="statusChanged.emit(task().id)">Toggle Status</button>
    </article>
  `
})
export class TaskItemComponent {
  readonly task = input.required<Task>();
  readonly statusChanged = output<string>();
}
```

### Step 4: Create Container / Feature Shell Component (`features/[feature]/feature-shell/`)
Build smart feature component wiring the store to the UI components:
```typescript
// src/app/features/tasks/feature-shell/task-list-container.component.ts
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { TaskStoreService } from '../data-access/task-store.service';
import { TaskItemComponent } from '../ui/task-item.component';

@Component({
  selector: 'app-task-list-container',
  standalone: true,
  imports: [TaskItemComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="task-dashboard">
      <header>
        <h2>Task Dashboard ({{ taskStore.pendingCount() }} Pending)</h2>
        <div class="filters">
          <button (click)="taskStore.setFilter('all')">All</button>
          <button (click)="taskStore.setFilter('pending')">Pending</button>
          <button (click)="taskStore.setFilter('completed')">Completed</button>
        </div>
      </header>

      @if (taskStore.isLoading()) {
        <p>Loading tasks...</p>
      } @else {
        <div class="task-grid">
          @for (task of taskStore.tasks(); track task.id) {
            <app-task-item [task]="task" (statusChanged)="onToggleStatus($event)" />
          } @empty {
            <p>No tasks found.</p>
          }
        </div>
      }
    </section>
  `
})
export class TaskListContainerComponent {
  readonly taskStore = inject(TaskStoreService);

  onToggleStatus(taskId: string): void {
    // Dispatch action to store
  }
}
```

### Step 5: Configure Feature Routes (`features/[feature]/[feature].routes.ts`)
```typescript
// src/app/features/tasks/tasks.routes.ts
import { Routes } from '@angular/router';

export const TASK_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./feature-shell/task-list-container.component').then(m => m.TaskListContainerComponent)
  }
];
```
