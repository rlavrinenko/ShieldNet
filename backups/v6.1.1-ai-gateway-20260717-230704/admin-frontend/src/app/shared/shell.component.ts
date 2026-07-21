import { Component, Input, computed } from '@angular/core';
import { ActivatedRoute, RouterLink, RouterLinkActive } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'sn-shell',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <div class="shell">
      <aside class="sidebar">
        <a routerLink="/" class="brand">
          <span class="brand-mark">S</span>
          <span>ShieldNet</span>
        </a>

        <nav aria-label="Main navigation">
          <a
            routerLink="/"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: true }"
          >My servers</a>

          @if (guildId()) {
            <div class="nav-caption">Server management</div>

            <a
              [routerLink]="['/guild', guildId()]"
              routerLinkActive="active"
              [routerLinkActiveOptions]="{ exact: true }"
            >Overview</a>

            <a
              [routerLink]="['/guild', guildId(), 'members']"
              routerLinkActive="active"
            >Members</a>

            <a
              [routerLink]="['/guild', guildId(), 'verification']"
              routerLinkActive="active"
            >Verification</a>

            <a
              [routerLink]="['/guild', guildId(), 'leadership']"
              routerLinkActive="active"
            >R5/R4 applications</a>

            <a
              [routerLink]="['/guild', guildId(), 'moderation']"
              routerLinkActive="active"
            >Moderation</a>

            <a
              [routerLink]="['/guild', guildId(), 'control']"
              routerLinkActive="active"
            >Server settings</a>

            <a
              [routerLink]="['/guild', guildId(), 'ai']"
              routerLinkActive="active"
            >AI & Integrations</a>
          }
        </nav>

        <div class="sidebar-footer">
          <div class="status"><span></span> Online</div>
          <button class="logout" type="button" (click)="auth.logout()">Logout</button>
        </div>
      </aside>

      <main>
        <header>
          <div>
            <div class="muted">ShieldNet</div>
            <h1>{{ title }}</h1>
          </div>

          <div class="user">
            @if (auth.profile()?.avatar_url) {
              <img [src]="auth.profile()?.avatar_url" alt="" />
            }
            <span>{{ auth.profile()?.display_name || auth.profile()?.login }}</span>
          </div>
        </header>

        <section class="content"><ng-content /></section>
      </main>
    </div>
  `,
  styles: [`
    .shell { min-height:100vh; display:grid; grid-template-columns:240px minmax(0,1fr); }
    .sidebar { position:sticky; top:0; height:100vh; padding:1.2rem; background:rgba(8,12,23,.92); border-right:1px solid var(--line); display:flex; flex-direction:column; backdrop-filter:blur(18px); overflow:auto; }
    .brand { display:flex; align-items:center; gap:.8rem; font-weight:800; font-size:1.12rem; padding:.6rem; }
    .brand-mark { display:grid; place-items:center; width:2.2rem; height:2.2rem; border-radius:11px; background:linear-gradient(135deg,var(--primary),#9a64ff); box-shadow:0 10px 30px rgba(104,119,255,.35); }
    nav { display:grid; gap:.3rem; margin-top:1.5rem; }
    .nav-caption { margin:1.1rem .9rem .35rem; color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    nav a { padding:.78rem .9rem; border-radius:11px; color:var(--muted); display:flex; align-items:center; border:1px solid transparent; }
    nav a:hover { color:var(--text); background:var(--primary-soft); }
    nav a.active { color:var(--text); background:var(--primary-soft); border-color:rgba(122,133,255,.22); }
    .sidebar-footer { margin-top:auto; display:grid; gap:1rem; padding-top:1.2rem; }
    .status { color:var(--muted); font-size:.78rem; display:flex; align-items:center; gap:.45rem; }
    .status span { width:.55rem; height:.55rem; border-radius:50%; background:#74e9b3; box-shadow:0 0 12px #74e9b3; }
    .logout { background:transparent; color:var(--muted); text-align:left; padding:0; }
    main { min-width:0; }
    header { min-height:84px; padding:1.1rem 2rem; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); background:rgba(8,12,23,.58); backdrop-filter:blur(18px); }
    h1 { margin:.25rem 0 0; font-size:1.35rem; }
    .user { border:1px solid var(--line); border-radius:999px; padding:.45rem .75rem; color:var(--muted); display:flex; align-items:center; gap:.55rem; }
    .user img { width:28px; height:28px; border-radius:50%; object-fit:cover; }
    .content { padding:2rem; }
    @media (max-width:900px) {
      .shell { grid-template-columns:1fr; }
      .sidebar { position:static; height:auto; overflow:visible; }
      .sidebar nav { display:flex; overflow:auto; gap:.35rem; }
      .nav-caption, .sidebar-footer { display:none; }
      .brand { margin-bottom:.5rem; }
      header { padding:1rem; }
      .content { padding:1rem; }
      nav a { white-space:nowrap; }
    }
  `],
})
export class ShellComponent {
  @Input({ required: true }) title = '';

  readonly guildId = computed(() => {
    let route: ActivatedRoute | null = this.route;
    while (route) {
      const value = route.snapshot.paramMap.get('guildId');
      if (value) return value;
      route = route.parent;
    }
    return null;
  });

  constructor(public readonly auth: AuthService, private readonly route: ActivatedRoute) {}
}
