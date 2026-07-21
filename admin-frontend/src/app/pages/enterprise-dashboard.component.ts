import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { EnterpriseDashboardOverview, EnterpriseDashboardService } from '../core/enterprise-dashboard.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  standalone: true,
  imports: [ShellComponent, RouterLink, DatePipe, DecimalPipe],
  template: `
    <sn-shell title="Enterprise Dashboard">
      <section class="hero card" [class.critical]="data()?.overall_status === 'critical'">
        <div>
          <div class="eyebrow">ShieldNet command center</div>
          <h2>Platform overview</h2>
          <p>Infrastructure, Discord estate, moderation and security in one workspace.</p>
        </div>
        <div class="hero-actions">
          <span class="health" [class]="'health ' + (data()?.overall_status || 'loading')">
            <i></i>{{ data()?.overall_status || 'loading' }}
          </span>
          <button class="btn secondary" [disabled]="loading()" (click)="load()">
            {{ loading() ? 'Refreshing…' : 'Refresh' }}
          </button>
        </div>
      </section>

      @if (error()) {
        <section class="card error">{{ error() }}</section>
      }

      @if (data(); as overview) {
        <section class="infra-grid">
          <article class="card component">
            <span class="pulse online"></span><div><b>Backend API</b><small>online</small></div>
          </article>
          <article class="card component">
            <span class="pulse online"></span><div><b>PostgreSQL</b><small>{{ overview.components.postgresql.latency_ms }} ms</small></div>
          </article>
          <article class="card component">
            <span class="pulse" [class.online]="overview.components.valkey.status === 'online'" [class.offline]="overview.components.valkey.status !== 'online'"></span>
            <div><b>Valkey</b><small>{{ overview.components.valkey.latency_ms ?? '—' }} ms</small></div>
          </article>
          @for (worker of overview.workers; track worker.name) {
            <article class="card component">
              <span class="pulse" [class.online]="worker.status === 'online'" [class.warning]="worker.status !== 'online'"></span>
              <div><b>{{ worker.type }}</b><small>{{ worker.name }} · {{ worker.status }}</small></div>
            </article>
          }
        </section>

        <section class="metric-grid">
          <article class="card metric primary"><span>Discord servers</span><strong>{{ overview.metrics['guilds'] | number }}</strong><small>{{ overview.scope }} scope</small></article>
          <article class="card metric"><span>Active members</span><strong>{{ overview.metrics['active_members'] | number }}</strong><small>{{ overview.metrics['members'] | number }} indexed</small></article>
          <article class="card metric"><span>Open cases</span><strong>{{ overview.metrics['open_cases'] | number }}</strong><small>{{ overview.metrics['overdue_cases'] | number }} overdue</small></article>
          <article class="card metric danger"><span>Security risks</span><strong>{{ overview.metrics['security_risks'] | number }}</strong><small>high + critical</small></article>
          <article class="card metric"><span>Open alerts</span><strong>{{ overview.metrics['open_alerts'] | number }}</strong><small>{{ overview.metrics['critical_alerts'] | number }} critical</small></article>
          <article class="card metric"><span>Queue depth</span><strong>{{ overview.metrics['queue_depth'] | number }}</strong><small>Discord jobs</small></article>
          <article class="card metric"><span>Audit / 24h</span><strong>{{ overview.metrics['audit_24h'] | number }}</strong><small>recorded actions</small></article>
          <article class="card metric"><span>Jobs / 7d</span><strong>{{ overview.metrics['successful_jobs_7d'] | number }}</strong><small>{{ overview.metrics['failed_jobs_24h'] | number }} failed today</small></article>
        </section>

        <section class="workspace-grid">
          <article class="card quick-panel">
            <div class="section-head"><div><span class="eyebrow">Operations</span><h3>Control centers</h3></div></div>
            <div class="quick-grid">
              <a routerLink="/platform/operations"><b>Live operations</b><span>Runtime, queue and event stream</span></a>
              <a routerLink="/platform/notifications"><b>Notifications</b><span>Alerts and incident signals</span></a>
              <a routerLink="/platform/jobs"><b>Jobs & health</b><span>Run and inspect system jobs</span></a>
              <a routerLink="/platform/access"><b>Platform access</b><span>Global roles and privileges</span></a>
            </div>
          </article>

          <article class="card status-panel">
            <div class="section-head"><div><span class="eyebrow">Capacity</span><h3>Platform telemetry</h3></div></div>
            <div class="telemetry"><span>Valkey memory</span><b>{{ formatBytes(overview.components.valkey.memory_bytes) }}</b></div>
            <div class="telemetry"><span>Bot accounts</span><b>{{ overview.metrics['bots'] | number }}</b></div>
            <div class="telemetry"><span>Watchlisted members</span><b>{{ overview.metrics['watchlisted'] | number }}</b></div>
            <div class="telemetry"><span>Generated</span><b>{{ overview.generated_at | date:'mediumTime' }}</b></div>
          </article>
        </section>

        <section class="section-head guild-title"><div><span class="eyebrow">Discord estate</span><h3>Managed servers</h3></div><span>{{ overview.guilds.length }} shown</span></section>
        @if (overview.guilds.length === 0) {
          <section class="card empty">No Discord servers are available for this account.</section>
        } @else {
          <section class="guild-grid">
            @for (guild of overview.guilds; track guild.guild_id) {
              <article class="card guild">
                <div class="guild-head">
                  @if (guild.icon_url) { <img [src]="guild.icon_url" alt=""> }
                  @else { <div class="avatar">{{ guild.name.slice(0, 1) }}</div> }
                  <div><h4>{{ guild.name }}</h4><small>{{ guild.guild_id }}</small></div>
                  <span class="badge" [class.online]="guild.bot_status === 'online'">{{ guild.bot_status }}</span>
                </div>
                <div class="guild-data"><span>Members <b>{{ guild.member_count | number }}</b></span><span>Sync <b>{{ guild.last_sync_at ? (guild.last_sync_at | date:'short') : 'Never' }}</b></span></div>
                <div class="guild-actions"><a class="btn" [routerLink]="['/guild', guild.guild_id]">Open server</a><a class="btn secondary" [routerLink]="['/guild', guild.guild_id, 'security']">Security</a></div>
              </article>
            }
          </section>
        }
      }
    </sn-shell>
  `,
  styles: [`
    .hero{padding:1.6rem;display:flex;justify-content:space-between;align-items:center;gap:1rem;background:radial-gradient(circle at 80% 20%,rgba(108,121,255,.2),transparent 38%),var(--panel)}
    .hero h2{font-size:2rem;margin:.25rem 0}.hero p{margin:0;color:var(--muted)}.hero-actions{display:flex;gap:.75rem;align-items:center}
    .eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.68rem;font-weight:800;color:#9da8ff}.health{display:flex;align-items:center;gap:.45rem;text-transform:uppercase;font-size:.72rem;font-weight:800;padding:.55rem .75rem;border-radius:999px;background:rgba(116,233,179,.1);color:#74e9b3}.health i,.pulse{width:.65rem;height:.65rem;border-radius:50%;background:currentColor;box-shadow:0 0 13px currentColor}.health.degraded{color:#ffd27a}.health.critical{color:#ff7b8f}
    .infra-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.8rem;margin-top:1rem}.component{padding:.9rem 1rem;display:flex;align-items:center;gap:.75rem}.component div{display:grid;gap:.2rem}.component small{color:var(--muted);text-transform:capitalize}.pulse{color:#718096}.pulse.online{color:#74e9b3}.pulse.warning{color:#ffd27a}.pulse.offline{color:#ff7b8f}
    .metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:1rem}.metric{padding:1.15rem;display:grid;gap:.4rem;min-height:125px}.metric span,.metric small{color:var(--muted)}.metric strong{font-size:2rem}.metric.primary{background:linear-gradient(145deg,rgba(96,111,255,.22),rgba(15,22,42,.86))}.metric.danger strong{color:#ff96a6}
    .workspace-grid{display:grid;grid-template-columns:2fr 1fr;gap:1rem;margin-top:1rem}.quick-panel,.status-panel{padding:1.2rem}.section-head{display:flex;justify-content:space-between;align-items:end}.section-head h3{margin:.25rem 0 0}.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:1rem}.quick-grid a{padding:1rem;border:1px solid var(--line);border-radius:12px;display:grid;gap:.3rem;background:rgba(255,255,255,.018)}.quick-grid a:hover{background:var(--primary-soft);border-color:rgba(122,133,255,.3)}.quick-grid span{color:var(--muted);font-size:.82rem}.telemetry{display:flex;justify-content:space-between;padding:.9rem 0;border-bottom:1px solid var(--line)}.telemetry:last-child{border-bottom:0}.telemetry span{color:var(--muted)}
    .guild-title{margin:1.8rem 0 .8rem}.guild-title>span{color:var(--muted)}.guild-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.guild{padding:1.1rem}.guild-head{display:grid;grid-template-columns:44px 1fr auto;gap:.75rem;align-items:center}.guild-head img,.avatar{width:44px;height:44px;border-radius:13px}.avatar{display:grid;place-items:center;background:var(--primary-soft);font-weight:800}.guild h4{margin:0}.guild small{color:var(--muted)}.badge{font-size:.68rem;text-transform:uppercase;padding:.35rem .5rem;border-radius:999px;background:rgba(255,210,122,.12);color:#ffd27a}.badge.online{background:rgba(116,233,179,.12);color:#74e9b3}.guild-data{display:grid;gap:.55rem;margin:1rem 0}.guild-data span{display:flex;justify-content:space-between;color:var(--muted)}.guild-data b{color:var(--text)}.guild-actions{display:flex;gap:.6rem}.empty{padding:2rem;text-align:center;color:var(--muted)}
    @media(max-width:1100px){.metric-grid{grid-template-columns:repeat(2,1fr)}.guild-grid{grid-template-columns:repeat(2,1fr)}}
    @media(max-width:760px){.hero{align-items:flex-start;flex-direction:column}.hero-actions{width:100%;justify-content:space-between}.metric-grid,.workspace-grid,.guild-grid,.quick-grid{grid-template-columns:1fr}}
  `],
})
export class EnterpriseDashboardComponent implements OnInit, OnDestroy {
  readonly data = signal<EnterpriseDashboardOverview | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');
  private timer?: ReturnType<typeof setInterval>;

  constructor(private readonly dashboard: EnterpriseDashboardService) {}

  ngOnInit(): void {
    void this.load();
    this.timer = setInterval(() => void this.load(false), 30000);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }

  async load(showLoader = true): Promise<void> {
    if (showLoader) this.loading.set(true);
    this.error.set('');
    try { this.data.set(await this.dashboard.overview()); }
    catch (error) { this.error.set(error instanceof Error ? error.message : 'Unable to load the dashboard.'); }
    finally { this.loading.set(false); }
  }

  formatBytes(value: number | null): string {
    if (value === null || value === undefined) return '—';
    if (value < 1024) return `${value} B`;
    const units = ['KB', 'MB', 'GB', 'TB'];
    let size = value / 1024;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit += 1; }
    return `${size.toFixed(size >= 10 ? 1 : 2)} ${units[unit]}`;
  }
}
