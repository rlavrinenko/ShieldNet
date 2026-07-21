import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ServerControlService } from '../core/server-control.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  standalone: true,
  imports: [RouterLink, ShellComponent],
  template: `
    <sn-shell title="Server Control Center">
      @if (loading()) {
        <section class="card state">Loading…</section>
      }

      @if (error()) {
        <section class="card error">{{ error() }}</section>
      }

      @if (data()) {
        <section class="card hero">
          <div class="identity">
            @if (data().guild.icon_url) {
              <img [src]="data().guild.icon_url" alt="">
            } @else {
              <div class="placeholder">
                {{ data().guild.name.slice(0, 1) }}
              </div>
            }

            <div>
              <div class="muted">Discord server</div>
              <h2>{{ data().guild.name }}</h2>
              <div class="muted">{{ data().guild.guild_id }}</div>
            </div>
          </div>

          <div class="hero-actions">
            <span class="badge">Bot {{ data().guild.bot_status }}</span>
            <button class="btn secondary" (click)="load()">Refresh</button>
          </div>
        </section>

        <section class="grid services">
          <article class="card metric"><strong>{{ data().services.backend }}</strong><span>Backend</span></article>
          <article class="card metric"><strong>{{ data().services.database }}</strong><span>PostgreSQL</span></article>
          <article class="card metric"><strong>{{ data().services.bot }}</strong><span>Discord Bot</span></article>
        </section>

        <section class="grid totals">
          <article class="card metric"><strong>{{ data().guild.member_count }}</strong><span>Members</span></article>
          <article class="card metric"><strong>{{ data().guild.role_count }}</strong><span>Roles</span></article>
          <article class="card metric"><strong>{{ data().guild.channel_count }}</strong><span>Channels</span></article>
          <article class="card metric"><strong>{{ data().audit.events_24h }}</strong><span>Audit / 24h</span></article>
        </section>

        <section class="card panel">
          <div class="panel-head">
            <h3>Verification</h3>
            <a class="btn secondary" [routerLink]="['/guild', guildId, 'verification']">Open</a>
          </div>

          <div class="grid verify">
            <div><strong>{{ data().verification.pending }}</strong><span>Pending</span></div>
            <div><strong>{{ data().verification.processing }}</strong><span>Processing</span></div>
            <div><strong>{{ data().verification.completed }}</strong><span>Completed</span></div>
            <div><strong>{{ data().verification.failed }}</strong><span>Failed</span></div>
          </div>
        </section>

        <section class="card panel">
          <h3>Server management</h3>
          <div class="grid nav">
            <a [routerLink]="['/guild', guildId, 'members']">Members</a>
            <a [routerLink]="['/guild', guildId, 'roles']">Roles</a>
            <a [routerLink]="['/guild', guildId, 'modules']">Modules</a>
            <a [routerLink]="['/guild', guildId, 'audit']">Audit</a>
            <a [routerLink]="['/guild', guildId, 'verification']">Verification</a>
            <a [routerLink]="['/guild', guildId, 'settings']">Settings</a>
          </div>
        </section>
      }
    </sn-shell>
  `,
  styles: [`
    .state,.error,.hero,.panel,.metric{padding:1rem}.error{color:#ffd9de}
    .hero,.identity,.hero-actions,.panel-head{display:flex;align-items:center}
    .hero,.panel-head{justify-content:space-between;gap:1rem}.identity,.hero-actions{gap:.8rem}
    .identity img,.placeholder{width:4rem;height:4rem;border-radius:16px}.identity img{object-fit:cover}
    .placeholder{display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);font-weight:900}
    h2,h3{margin:.2rem 0}.badge{padding:.35rem .7rem;border-radius:999px;background:rgba(75,214,155,.16);color:#74e9b3}
    .grid{display:grid;gap:1rem}.services{margin-top:1rem;grid-template-columns:repeat(3,1fr)}
    .totals{margin-top:1rem;grid-template-columns:repeat(4,1fr)}.metric{display:grid;gap:.25rem}.metric strong{font-size:1.5rem}
    .metric span,.verify span{color:var(--muted)}.panel{margin-top:1rem}.verify{margin-top:1rem;grid-template-columns:repeat(4,1fr)}
    .verify div{padding:.75rem;display:grid;gap:.2rem;background:var(--panel-2);border-radius:10px}
    .nav{margin-top:1rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
    .nav a{padding:1rem;text-decoration:none;color:var(--text);background:var(--panel-2);border:1px solid var(--line);border-radius:12px}
    @media(max-width:750px){.services,.totals,.verify{grid-template-columns:repeat(2,1fr)}.hero{align-items:stretch;flex-direction:column}}
    @media(max-width:480px){.services,.totals,.verify{grid-template-columns:1fr}}
  `],
})
export class ServerControlComponent implements OnInit {
  readonly guildId = this.route.snapshot.paramMap.get('guildId') ?? '';
  readonly data = signal<any | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  constructor(
    private readonly route: ActivatedRoute,
    private readonly service: ServerControlService,
  ) {}

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set('');
    try {
      this.data.set(await this.service.overview(this.guildId));
    } catch {
      this.error.set('Unable to load the Server Control Center.');
    } finally {
      this.loading.set(false);
    }
  }
}
