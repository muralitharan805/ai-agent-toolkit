import { Injectable, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

/**
 * Enterprise Page Title Strategy.
 * Synchronizes route snapshot `data.title` with the browser window title,
 * appending the standardized enterprise application brand suffix.
 */
@Injectable({ providedIn: 'root' })
export class AppTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private static readonly APP_NAME = 'Enterprise App';

  /**
   * Updates browser document title based on current router state snapshot.
   * @param routerState - Activated router state snapshot.
   */
  override updateTitle(routerState: RouterStateSnapshot): void {
    const pageTitle = this.buildTitle(routerState);
    if (pageTitle) {
      this.title.setTitle(`${pageTitle} | ${AppTitleStrategy.APP_NAME}`);
      return;
    }
    this.title.setTitle(AppTitleStrategy.APP_NAME);
  }
}
