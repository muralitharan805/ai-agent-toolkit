/**
 * @file signal-store-template.ts
 * Enterprise Lightweight Angular Signal Store Template.
 * Demonstrates strict typing, Clean Architecture encapsulation,
 * rxResource integration, and synchronized linkedSignals.
 */

import { Injectable, inject, signal, computed, linkedSignal, Signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { rxResource } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';

/**
 * Domain entity model representing an item in the store.
 */
export interface EntityItem {
  readonly id: string;
  readonly title: string;
  readonly category: string;
  readonly price: number;
  readonly isAvailable: boolean;
}

/**
 * DTO for filtering and paginating the entity collection.
 */
export interface EntityFilterCriteria {
  readonly searchKeyword: string;
  readonly selectedCategory: string;
  readonly pageIndex: number;
  readonly pageSize: number;
}

/**
 * Immutable default filter state.
 */
export const DEFAULT_FILTER_CRITERIA: Readonly<EntityFilterCriteria> = Object.freeze({
  searchKeyword: '',
  selectedCategory: 'ALL',
  pageIndex: 0,
  pageSize: 20
});

/**
 * Enterprise state store managing domain entity lifecycle and queries.
 */
@Injectable({ providedIn: 'root' })
export class EntityStoreService {
  private readonly httpClient = inject(HttpClient);

  // 1. Private mutable state nodes
  private readonly searchKeywordState = signal<string>(DEFAULT_FILTER_CRITERIA.searchKeyword);
  private readonly selectedCategoryState = signal<string>(DEFAULT_FILTER_CRITERIA.selectedCategory);
  private readonly pageSizeState = signal<number>(DEFAULT_FILTER_CRITERIA.pageSize);

  // 2. Synchronized writable signals: Reset page to 0 when search term or category changes
  readonly activePageIndex = linkedSignal<string, number>({
    source: () => `${this.searchKeywordState()}_${this.selectedCategoryState()}`,
    computation: (_sourceKey, prev) => (prev ? 0 : 0)
  });

  // 3. Asynchronous Resource Loader
  readonly entityResource = rxResource<readonly EntityItem[], EntityFilterCriteria>({
    request: () => ({
      searchKeyword: this.searchKeywordState(),
      selectedCategory: this.selectedCategoryState(),
      pageIndex: this.activePageIndex(),
      pageSize: this.pageSizeState()
    }),
    loader: ({ request }): Observable<readonly EntityItem[]> => {
      return this.fetchEntitiesFromApi(request);
    }
  });

  // 4. Public Readonly & Computed Projections
  readonly entities: Signal<readonly EntityItem[]> = computed(() => this.entityResource.value() ?? []);
  readonly isLoading: Signal<boolean> = computed(() => this.entityResource.isLoading());
  readonly error: Signal<unknown> = computed(() => this.entityResource.error());

  readonly totalItemCount: Signal<number> = computed(() => this.entities().length);

  readonly availableItems: Signal<readonly EntityItem[]> = computed(() =>
    this.entities().filter(item => item.isAvailable)
  );

  readonly searchKeyword: Signal<string> = this.searchKeywordState.asReadonly();
  readonly selectedCategory: Signal<string> = this.selectedCategoryState.asReadonly();

  /**
   * Dispatches an updated search keyword and triggers query invalidation.
   * @param keyword Search term entered by the user.
   */
  setSearchKeyword(keyword: string): void {
    const sanitized = keyword.trim();
    if (sanitized === this.searchKeywordState()) {
      return;
    }
    this.searchKeywordState.set(sanitized);
  }

  /**
   * Sets the active category filter.
   * @param category Category identifier.
   */
  setSelectedCategory(category: string): void {
    if (!category || category === this.selectedCategoryState()) {
      return;
    }
    this.selectedCategoryState.set(category);
  }

  /**
   * Advances or rewinds the pagination page index.
   * @param targetPage Desired zero-indexed page number.
   */
  setPageIndex(targetPage: number): void {
    if (targetPage < 0 || targetPage === this.activePageIndex()) {
      return;
    }
    this.activePageIndex.set(targetPage);
  }

  /**
   * Manually re-executes the active resource fetcher.
   */
  refresh(): void {
    this.entityResource.reload();
  }

  /**
   * Optimistically updates a single item title in local state.
   * @param itemId Target item unique identifier.
   * @param newTitle Updated title string.
   */
  optimisticUpdateTitle(itemId: string, newTitle: string): void {
    this.entityResource.update(currentList => {
      if (!currentList) {
        return [];
      }
      return currentList.map(item =>
        item.id === itemId ? { ...item, title: newTitle } : item
      );
    });
  }

  /**
   * Helper method encapsulating HTTP communication.
   * @param criteria Filter criteria payload.
   * @returns Observable stream of domain entities.
   */
  private fetchEntitiesFromApi(criteria: EntityFilterCriteria): Observable<readonly EntityItem[]> {
    return this.httpClient.get<readonly EntityItem[]>('/api/v1/entities', {
      params: {
        q: criteria.searchKeyword,
        category: criteria.selectedCategory,
        page: String(criteria.pageIndex),
        size: String(criteria.pageSize)
      }
    });
  }
}
