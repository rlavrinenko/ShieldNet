import { Component, signal } from '@angular/core';

import { AuthService } from '../core/auth.service';

@Component({
  standalone: true,
  template: `
    <main class="login-page">
      <section class="login-card card">
        <div class="logo">S</div>
        <div class="eyebrow">ShieldNet Control Plane</div>
        <h1>Manage Discord securely</h1>
        <p>
          Servers, modules, members and administration in one private console.
        </p>

        <button class="btn discord" [disabled]="loading()" (click)="login()">
          {{ loading() ? 'Connecting…' : 'Continue with Discord' }}
        </button>

        @if (error()) {
          <div class="error">{{ error() }}</div>
        }

        <div class="footer muted">
          Only server owners and trusted moderators can access this panel.
        </div>
      </section>
    </main>
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 1.2rem;
    }

    .login-card {
      width: min(460px, 100%);
      padding: 2.2rem;
      text-align: center;
    }

    .logo {
      width: 4rem;
      height: 4rem;
      margin: 0 auto 1.2rem;
      display: grid;
      place-items: center;
      border-radius: 18px;
      background: linear-gradient(135deg, var(--primary), #9a64ff);
      font-size: 1.6rem;
      font-weight: 900;
      box-shadow: 0 18px 45px rgba(104,119,255,.35);
    }

    .eyebrow {
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: .12em;
      font-size: .75rem;
      font-weight: 800;
    }

    h1 { font-size: 2rem; margin: .75rem 0; }
    p { color: var(--muted); line-height: 1.65; }
    .discord { width: 100%; margin-top: 1.1rem; }
    .discord:disabled { opacity: .65; cursor: wait; }

    .error {
      margin-top: 1rem;
      padding: .8rem;
      border-radius: 10px;
      color: #ffd9de;
      background: rgba(255,107,125,.14);
      border: 1px solid rgba(255,107,125,.35);
    }

    .footer {
      margin-top: 1.4rem;
      font-size: .82rem;
      line-height: 1.5;
    }
  `],
})
export class LoginComponent {
  readonly loading = signal(false);
  readonly error = signal('');

  constructor(private readonly auth: AuthService) {}

  async login(): Promise<void> {
    this.loading.set(true);
    this.error.set('');

    try {
      await this.auth.startDiscordLogin();
    } catch (error) {
      this.error.set(
        error instanceof Error ? error.message : 'Discord login failed.',
      );
    } finally {
      this.loading.set(false);
    }
  }
}
