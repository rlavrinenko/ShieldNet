import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import {
  PlatformAccessIdentity,
  PlatformAccessOverview,
  PlatformAccessService,
} from '../core/platform-access.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  selector: 'sn-platform-access',
  standalone: true,
  imports: [CommonModule, ShellComponent],
  template: `
    <sn-shell title="Platform Access">
      <div class="notice" *ngIf="loading">Checking platform access…</div>
      <div class="notice error" *ngIf="error">{{ error }}</div>

      <section class="hero" *ngIf="identity">
        <div>
          <div class="eyebrow">Global RBAC</div>
          <h2>{{ identity.is_superadmin ? 'SuperAdmin access active' : 'Standard platform access' }}</h2>
          <p>
            Discord ID: <strong>{{ identity.discord_user_id || 'not linked' }}</strong>
            · Source: <strong>{{ identity.superadmin_source || 'membership / database roles' }}</strong>
          </p>
        </div>
        <span class="badge" [class.active]="identity.is_superadmin">
          {{ identity.highest_role || 'no global role' }}
        </span>
      </section>

      <div class="cards" *ngIf="overview">
        <article><span>Registered servers</span><strong>{{ overview.guild_count }}</strong></article>
        <article><span>Platform users</span><strong>{{ overview.user_count }}</strong></article>
        <article><span>Active memberships</span><strong>{{ overview.active_memberships }}</strong></article>
        <article><span>Configured SuperAdmins</span><strong>{{ overview.configured_superadmins }}</strong></article>
      </div>

      <section class="panel" *ngIf="identity">
        <h3>Effective roles</h3>
        <div class="roles" *ngIf="identity.roles.length; else noRoles">
          <span *ngFor="let role of identity.roles">{{ role }}</span>
        </div>
        <ng-template #noRoles><p class="muted">No global roles assigned.</p></ng-template>
      </section>

      <section class="panel setup" *ngIf="identity?.is_superadmin">
        <h3>Server configuration</h3>
        <p>Add one or more Discord user IDs to the backend environment:</p>
        <code>SHIELDNET_SUPERADMIN_IDS=123456789012345678,987654321098765432</code>
        <p class="muted">Restart shieldnet-backend after changing the environment file.</p>
      </section>
    </sn-shell>
  `,
  styles: [`
    .hero, .panel, .notice, article {
      border: 1px solid var(--line);
      background: rgba(16,22,38,.72);
      border-radius: 18px;
    }
    .hero { padding: 1.4rem; display:flex; justify-content:space-between; gap:1rem; align-items:center; }
    h2 { margin:.25rem 0; }
    p { color:var(--muted); }
    .eyebrow { text-transform:uppercase; letter-spacing:.12em; color:var(--primary); font-size:.75rem; }
    .badge { padding:.55rem .8rem; border-radius:999px; border:1px solid var(--line); text-transform:uppercase; font-size:.75rem; }
    .badge.active { background:var(--primary-soft); color:#cfd5ff; }
    .cards { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1rem; margin:1rem 0; }
    article { padding:1rem; display:grid; gap:.45rem; }
    article span { color:var(--muted); }
    article strong { font-size:1.7rem; }
    .panel { padding:1.2rem; margin-top:1rem; }
    .roles { display:flex; flex-wrap:wrap; gap:.55rem; }
    .roles span { padding:.4rem .65rem; border-radius:9px; background:var(--primary-soft); }
    code { display:block; overflow:auto; padding:1rem; border-radius:12px; background:#080c17; color:#cbd4ff; }
    .notice { padding:1rem; margin-bottom:1rem; }
    .error { border-color:rgba(255,80,100,.5); color:#ff9baa; }
    @media(max-width:900px){ .cards{grid-template-columns:repeat(2,minmax(0,1fr));} }
    @media(max-width:600px){ .hero{align-items:flex-start;flex-direction:column}.cards{grid-template-columns:1fr;} }
  `],
})
export class PlatformAccessComponent implements OnInit {
  identity: PlatformAccessIdentity | null = null;
  overview: PlatformAccessOverview | null = null;
  loading = true;
  error = '';

  constructor(private readonly access: PlatformAccessService) {}

  ngOnInit(): void {
    this.access.identity().subscribe({
      next: (identity) => {
        this.identity = identity;
        if (!identity.is_superadmin) {
          this.loading = false;
          return;
        }
        this.access.overview().subscribe({
          next: (overview) => { this.overview = overview; this.loading = false; },
          error: () => { this.error = 'Unable to load SuperAdmin overview.'; this.loading = false; },
        });
      },
      error: () => { this.error = 'Unable to verify platform access.'; this.loading = false; },
    });
  }
}
