import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ThemeService } from './theme.service';

/**
 * Header Theme Toggle Component.
 * Accessible interactive button providing one-click switching between Light and Dark themes.
 */
@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button mat-icon-button
            [matTooltip]="themeService.isDarkMode() ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            [attr.aria-label]="themeService.isDarkMode() ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            (click)="themeService.toggleTheme()">
      <mat-icon>{{ themeService.isDarkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `
})
export class ThemeToggleComponent {
  readonly themeService = inject(ThemeService);
}
