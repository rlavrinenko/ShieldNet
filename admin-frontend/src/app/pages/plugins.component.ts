import { Component, OnInit, computed, signal } from '@angular/core';

import { PluginManifest, PluginScanResult, PluginService } from '../core/plugin.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  selector: 'sn-plugins',
  standalone: true,
  imports: [ShellComponent],
  template: `
    <sn-shell title="Plugin Platform">
      <section class="page-head">
        <div>
          <h2>Installed plugins</h2>
          <p class="muted">Discover local plugin manifests and control their global state.</p>
        </div>
        <button type="button" (click)="scan()" [disabled]="scanning()">
          {{ scanning() ? 'Scanning…' : 'Scan plugin directory' }}
        </button>
      </section>

      <section class="metrics">
        <article class="card"><span class="muted">Discovered</span><strong>{{ plugins().length }}</strong></article>
        <article class="card"><span class="muted">Enabled</span><strong>{{ enabledCount() }}</strong></article>
        <article class="card"><span class="muted">Healthy</span><strong>{{ healthyCount() }}</strong></article>
        <article class="card"><span class="muted">Unsigned</span><strong>{{ unsignedCount() }}</strong></article>
      </section>

      @if (scanResult()) {
        <div class="notice card">
          Scan complete: {{ scanResult()?.discovered }} discovered, {{ scanResult()?.updated }} updated,
          {{ scanResult()?.missing }} missing.
        </div>
      }

      @if (error()) { <div class="error card">{{ error() }}</div> }
      @if (loading()) { <div class="card loading">Loading plugins…</div> }

      <section class="plugin-grid">
        @for (plugin of plugins(); track plugin.plugin_key) {
          <article class="plugin card" [class.unhealthy]="!plugin.healthy">
            <div class="plugin-main">
              <div class="title-row">
                <h3>{{ plugin.name }}</h3>
                <span class="badge">v{{ plugin.version }}</span>
                <span class="badge" [class.good]="plugin.healthy">{{ plugin.healthy ? 'Healthy' : 'Unhealthy' }}</span>
                <span class="badge">{{ plugin.signature_status }}</span>
              </div>
              <p class="muted">{{ plugin.description || 'No description supplied.' }}</p>
              <div class="meta">
                <span>ID: {{ plugin.plugin_key }}</span>
                <span>Author: {{ plugin.author || 'Unknown' }}</span>
                <span>Core: {{ plugin.min_core_version || 'Any' }}</span>
              </div>
              <div class="chips">
                @for (capability of plugin.capabilities; track capability) {
                  <span>{{ capability }}</span>
                }
              </div>
              @if (plugin.last_error) { <div class="plugin-error">{{ plugin.last_error }}</div> }
            </div>
            <button
              class="toggle"
              [class.on]="plugin.enabled"
              [disabled]="savingKey() === plugin.plugin_key || !plugin.healthy"
              (click)="toggle(plugin)"
              [attr.aria-label]="'Toggle ' + plugin.name"
            ><span></span></button>
          </article>
        } @empty {
          @if (!loading()) {
            <div class="empty card">No plugins found. Place manifests under <code>/opt/shieldnet/plugins/&lt;plugin&gt;/plugin.json</code> and scan again.</div>
          }
        }
      </section>
    </sn-shell>
  `,
  styles: [`
    .page-head{display:flex;justify-content:space-between;align-items:end;gap:1rem;margin-bottom:1rem}.page-head h2,.page-head p{margin:0}.page-head p{margin-top:.35rem}.page-head button{padding:.75rem 1rem;border-radius:11px;background:var(--primary);color:#fff;font-weight:750}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;margin-bottom:1rem}.metrics article{padding:1rem;display:grid;gap:.4rem}.metrics strong{font-size:1.45rem}.notice,.error,.loading,.empty{padding:1rem;margin-bottom:1rem}.error,.plugin-error{color:#ffd9de}.plugin-grid{display:grid;gap:.8rem}.plugin{padding:1rem;display:grid;grid-template-columns:1fr auto;gap:1rem;align-items:center}.plugin.unhealthy{border-color:rgba(255,107,125,.45)}.title-row{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}.title-row h3{margin:0}.plugin p{margin:.45rem 0}.meta{display:flex;gap:1rem;flex-wrap:wrap;color:var(--muted);font-size:.75rem}.badge,.chips span{padding:.22rem .5rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:.7rem}.badge.good{color:#b9f4dc;border-color:rgba(75,214,155,.35)}.chips{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.7rem}.plugin-error{margin-top:.7rem;font-size:.8rem}.toggle{width:3.1rem;height:1.75rem;padding:.2rem;border-radius:999px;background:#2a344b}.toggle span{display:block;width:1.35rem;height:1.35rem;border-radius:50%;background:white;transition:.2s}.toggle.on{background:var(--success)}.toggle.on span{transform:translateX(1.35rem)}code{color:#cfd5ff}@media(max-width:760px){.page-head{align-items:stretch;flex-direction:column}.metrics{grid-template-columns:1fr 1fr}.plugin{grid-template-columns:1fr}.toggle{justify-self:end}}
  `],
})
export class PluginsComponent implements OnInit {
  readonly plugins = signal<PluginManifest[]>([]);
  readonly loading = signal(true);
  readonly scanning = signal(false);
  readonly savingKey = signal<string | null>(null);
  readonly error = signal('');
  readonly scanResult = signal<PluginScanResult | null>(null);
  readonly enabledCount = computed(() => this.plugins().filter((p) => p.enabled).length);
  readonly healthyCount = computed(() => this.plugins().filter((p) => p.healthy).length);
  readonly unsignedCount = computed(() => this.plugins().filter((p) => p.signature_status === 'unsigned').length);

  constructor(private readonly pluginService: PluginService) {}

  async ngOnInit(): Promise<void> { await this.load(); }

  async load(): Promise<void> {
    this.loading.set(true); this.error.set('');
    try { this.plugins.set(await this.pluginService.list()); }
    catch { this.error.set('Unable to load plugins.'); }
    finally { this.loading.set(false); }
  }

  async scan(): Promise<void> {
    this.scanning.set(true); this.error.set('');
    try { this.scanResult.set(await this.pluginService.scan()); await this.load(); }
    catch { this.error.set('Plugin scan failed. Superadmin access is required.'); }
    finally { this.scanning.set(false); }
  }

  async toggle(plugin: PluginManifest): Promise<void> {
    this.savingKey.set(plugin.plugin_key); this.error.set('');
    try {
      const updated = await this.pluginService.setEnabled(plugin.plugin_key, !plugin.enabled);
      this.plugins.update((items) => items.map((item) => item.plugin_key === updated.plugin_key ? updated : item));
    } catch { this.error.set(`Unable to update ${plugin.name}.`); }
    finally { this.savingKey.set(null); }
  }
}
