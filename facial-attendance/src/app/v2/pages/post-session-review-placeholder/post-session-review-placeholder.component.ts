import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-v2-post-session-review-placeholder',
  template: `
    <section class="v2-review-placeholder">
      <div class="fras-v2-panel">
        <p>Post Session Review</p>
        <h1>Session #{{ sessionId }}</h1>
        <span>The full review workflow will be implemented next. The live session ended and routed here successfully.</span>
      </div>
    </section>
  `,
  styles: [`
    .v2-review-placeholder {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: var(--space-12);
      background: var(--color-page-bg);
    }

    .fras-v2-panel {
      max-width: 520px;
      width: 100%;
      padding: var(--space-10);
      border: 1px solid var(--color-border);
      border-left: 5px solid var(--color-primary-maroon);
      border-radius: var(--radius-xl);
      background: var(--color-surface);
      box-shadow: var(--shadow-card-lg);
    }

    p {
      margin: 0;
      color: var(--color-text-subtle);
      font-size: var(--font-size-label);
      font-weight: var(--font-weight-heavy);
      letter-spacing: .05em;
      text-transform: uppercase;
    }

    h1 {
      margin: var(--space-2) 0 var(--space-4);
      color: var(--color-maroon-dark);
      font-size: var(--font-size-display);
      font-weight: var(--font-weight-black);
    }

    span {
      color: var(--color-text-muted);
      font-size: var(--font-size-body);
      font-weight: var(--font-weight-bold);
      line-height: 1.55;
    }
  `]
})
export class V2PostSessionReviewPlaceholderComponent {
  sessionId = '';

  constructor(private route: ActivatedRoute) {
    this.sessionId = this.route.snapshot.paramMap.get('sessionId') || '';
  }
}
