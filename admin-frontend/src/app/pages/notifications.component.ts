import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { NotificationService, NotificationSummary, PlatformNotification } from '../core/notification.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  selector: 'sn-notifications',
  standalone: true,
  imports: [CommonModule, FormsModule, ShellComponent],
  template: `
    <sn-shell title="Notification Center">
      <div class="topline">
        <div><div class="eyebrow">ALERT ROUTING & RESPONSE</div><h2>Platform notifications</h2></div>
        <button (click)="evaluate()" [disabled]="busy()">{{ busy() ? 'Evaluating…' : 'Evaluate alert rules' }}</button>
      </div>

      @if (summary(); as stats) {
        <div class="cards">
          <article><span>Open</span><b>{{ stats.open }}</b></article>
          <article class="critical"><span>Critical</span><b>{{ stats.critical }}</b></article>
          <article class="high"><span>High</span><b>{{ stats.high }}</b></article>
          <article><span>Acknowledged</span><b>{{ stats.acknowledged }}</b></article>
          <article><span>Resolved</span><b>{{ stats.resolved }}</b></article>
        </div>
      }

      <div class="filters">
        <select [(ngModel)]="status" (change)="load()">
          <option value="">All statuses</option><option value="open">Open</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option>
        </select>
        <select [(ngModel)]="severity" (change)="load()">
          <option value="">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="info">Info</option>
        </select>
        <button class="secondary" (click)="load()">Refresh</button>
      </div>

      <section class="panel">
        @for (item of items(); track item.id) {
          <article class="alert" [class]="item.severity">
            <div class="severity">{{ item.severity }}</div>
            <div class="body">
              <div class="head"><h3>{{ item.title }}</h3><span>{{ item.status }}</span></div>
              <p>{{ item.message }}</p>
              <small>{{ item.category }} · {{ item.source }} · {{ item.last_seen_at | date:'medium' }} @if(item.guild_id){ · Guild {{ item.guild_id }} }</small>
            </div>
            <div class="actions">
              @if (item.status === 'open') { <button class="secondary" (click)="acknowledge(item)">Acknowledge</button> }
              @if (item.status !== 'resolved') { <button (click)="resolve(item)">Resolve</button> }
            </div>
          </article>
        } @empty { <div class="empty">No notifications match the selected filters.</div> }
      </section>

      @if (message()) { <div class="toast">{{ message() }}</div> }
    </sn-shell>
  `,
  styles: [`
    .topline{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.4rem}.eyebrow{font-size:.72rem;letter-spacing:.14em;color:#7f8cff;font-weight:800}h2{margin:.35rem 0 0;font-size:2rem}button,select{border:1px solid var(--line);border-radius:11px;padding:.7rem .9rem;background:#6675f4;color:white}button:disabled{opacity:.55}.secondary,select{background:rgba(255,255,255,.045);color:var(--text)}.cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.8rem;margin-bottom:1rem}.cards article,.panel{background:rgba(14,20,37,.78);border:1px solid var(--line);border-radius:16px;padding:1rem}.cards span{color:var(--muted)}.cards b{display:block;font-size:1.8rem;margin-top:.35rem}.cards .critical b{color:#ff7f91}.cards .high b{color:#ffb15c}.filters{display:flex;gap:.7rem;margin-bottom:1rem}.panel{padding:.2rem 1rem}.alert{display:grid;grid-template-columns:92px minmax(0,1fr) auto;gap:1rem;padding:1rem 0;border-bottom:1px solid rgba(255,255,255,.06);align-items:center}.severity{text-transform:uppercase;font-size:.72rem;font-weight:900;letter-spacing:.08em;color:#8fa0bf}.alert.critical .severity{color:#ff7f91}.alert.high .severity{color:#ffb15c}.alert.medium .severity{color:#ffe178}.head{display:flex;justify-content:space-between;gap:1rem}.head h3{margin:0}.head span{font-size:.72rem;text-transform:uppercase;color:#92a0bf}.body p{color:var(--muted);margin:.4rem 0}.body small{color:#7784a4}.actions{display:flex;gap:.5rem}.empty{padding:2rem;text-align:center;color:var(--muted)}.toast{position:fixed;right:2rem;bottom:2rem;background:#19213a;border:1px solid var(--line);padding:.8rem 1rem;border-radius:12px}@media(max-width:950px){.cards{grid-template-columns:repeat(2,1fr)}.alert{grid-template-columns:1fr}.actions,.filters,.topline{flex-wrap:wrap}.head{flex-direction:column}}
  `],
})
export class NotificationsComponent implements OnInit {
  readonly items = signal<PlatformNotification[]>([]);
  readonly summary = signal<NotificationSummary | null>(null);
  readonly busy = signal(false);
  readonly message = signal('');
  status = '';
  severity = '';

  constructor(private readonly notifications: NotificationService) {}

  ngOnInit(): void { void this.load(); }

  async load(): Promise<void> {
    const [list, summary] = await Promise.all([
      firstValueFrom(this.notifications.list(this.status, this.severity)),
      firstValueFrom(this.notifications.summary()),
    ]);
    this.items.set(list.items);
    this.summary.set(summary);
  }

  async evaluate(): Promise<void> {
    this.busy.set(true);
    try {
      const result = await firstValueFrom(this.notifications.evaluate());
      this.message.set(`Rules evaluated: ${result['alerts_created_or_refreshed'] || 0} alert(s) refreshed.`);
      await this.load();
    } finally { this.busy.set(false); window.setTimeout(() => this.message.set(''), 3500); }
  }

  async acknowledge(item: PlatformNotification): Promise<void> { await firstValueFrom(this.notifications.acknowledge(item.id)); await this.load(); }
  async resolve(item: PlatformNotification): Promise<void> { await firstValueFrom(this.notifications.resolve(item.id)); await this.load(); }
}
