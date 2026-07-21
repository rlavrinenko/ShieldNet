import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import { JobDefinition, JobsOverview, JobsService } from '../core/jobs.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  selector: 'sn-jobs-center',
  standalone: true,
  imports: [CommonModule, ShellComponent],
  template: `
    <sn-shell title="Jobs Center & System Health">
      <div class="notice" *ngIf="loading">Loading platform jobs…</div>
      <div class="notice error" *ngIf="error">{{ error }}</div>

      <ng-container *ngIf="overview">
        <section class="health-grid">
          <article><span>Backend</span><strong class="ok">{{ overview.health.backend }}</strong></article>
          <article><span>PostgreSQL</span><strong class="ok">{{ overview.health.database }}</strong><small>{{ overview.health.database_latency_ms }} ms</small></article>
          <article><span>Scheduler</span><strong>{{ overview.health.scheduler }}</strong></article>
          <article><span>Worker</span><strong>{{ overview.health.worker }}</strong></article>
        </section>

        <section class="summary-grid">
          <article><span>Registered jobs</span><strong>{{ overview.totals.registered_jobs }}</strong></article>
          <article><span>Recent runs</span><strong>{{ overview.totals.recent_runs }}</strong></article>
          <article><span>Failed runs</span><strong [class.danger]="overview.totals.failed_runs > 0">{{ overview.totals.failed_runs }}</strong></article>
          <article><span>Running</span><strong>{{ overview.totals.running_runs }}</strong></article>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div><div class="eyebrow">Operations</div><h2>Available jobs</h2></div>
            <button (click)="reload()" [disabled]="loading">Refresh</button>
          </div>

          <div class="jobs">
            <article class="job" *ngFor="let job of overview.jobs">
              <div>
                <div class="category">{{ job.category }}</div>
                <h3>{{ job.name }}</h3>
                <p>{{ job.description }}</p>
                <small>
                  Last run: {{ job.last_run_at ? (job.last_run_at | date:'medium') : 'never' }}
                  <span *ngIf="job.last_duration_ms !== null"> · {{ job.last_duration_ms }} ms</span>
                </small>
              </div>
              <div class="job-actions">
                <span class="status" [class.success]="job.last_status === 'success'" [class.failed]="job.last_status === 'failed'">
                  {{ job.last_status || 'not run' }}
                </span>
                <button (click)="run(job)" [disabled]="runningKey === job.key">
                  {{ runningKey === job.key ? 'Running…' : 'Run now' }}
                </button>
              </div>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="eyebrow">History</div>
          <h2>Recent executions</h2>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Job</th><th>Status</th><th>Trigger</th><th>Duration</th><th>Finished</th><th>Result</th></tr></thead>
              <tbody>
                <tr *ngFor="let run of overview.recent_runs">
                  <td>{{ run.job_key }}</td>
                  <td><span class="status" [class.success]="run.status === 'success'" [class.failed]="run.status === 'failed'">{{ run.status }}</span></td>
                  <td>{{ run.trigger }}</td>
                  <td>{{ run.duration_ms ?? '—' }}<span *ngIf="run.duration_ms !== null"> ms</span></td>
                  <td>{{ run.finished_at ? (run.finished_at | date:'medium') : '—' }}</td>
                  <td><code>{{ run.error_message || formatResult(run.result) }}</code></td>
                </tr>
                <tr *ngIf="!overview.recent_runs.length"><td colspan="6" class="empty">No jobs have been run yet.</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </ng-container>
    </sn-shell>
  `,
  styles: [`
    .notice,.panel,.health-grid article,.summary-grid article{border:1px solid var(--line);background:rgba(16,22,38,.72);border-radius:18px}
    .notice{padding:1rem;margin-bottom:1rem}.error{color:#ff9baa;border-color:rgba(255,80,100,.45)}
    .health-grid,.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;margin-bottom:1rem}
    article{padding:1rem}.health-grid article,.summary-grid article{display:grid;gap:.35rem}.health-grid span,.summary-grid span,small,p{color:var(--muted)}
    strong{font-size:1.35rem}.summary-grid strong{font-size:1.8rem}.ok{color:#72e6a1}.danger{color:#ff8193}
    .panel{padding:1.2rem;margin-top:1rem}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:1rem}
    .eyebrow,.category{text-transform:uppercase;letter-spacing:.12em;color:var(--primary);font-size:.72rem}.category{margin-bottom:.35rem}
    h2,h3{margin:.2rem 0}.jobs{display:grid;gap:.8rem;margin-top:1rem}.job{border:1px solid var(--line);border-radius:14px;display:flex;justify-content:space-between;gap:1rem;align-items:center}
    .job p{margin:.45rem 0}.job-actions{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;justify-content:flex-end}
    button{border:1px solid var(--line);background:var(--primary-soft);color:var(--text);padding:.65rem .9rem;border-radius:10px}button:disabled{opacity:.55}
    .status{display:inline-block;padding:.3rem .55rem;border-radius:999px;border:1px solid var(--line);font-size:.75rem;text-transform:uppercase}.status.success{color:#72e6a1}.status.failed{color:#ff8193}
    .table-wrap{overflow:auto;margin-top:1rem}table{width:100%;border-collapse:collapse;min-width:850px}th,td{text-align:left;padding:.75rem;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-size:.75rem;text-transform:uppercase}code{display:block;max-width:420px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#cbd4ff}.empty{text-align:center;color:var(--muted)}
    @media(max-width:900px){.health-grid,.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.job{align-items:flex-start;flex-direction:column}.job-actions{justify-content:flex-start}}
    @media(max-width:560px){.health-grid,.summary-grid{grid-template-columns:1fr}}
  `],
})
export class JobsCenterComponent implements OnInit {
  overview: JobsOverview | null = null;
  loading = true;
  error = '';
  runningKey = '';

  constructor(private readonly jobs: JobsService) {}

  ngOnInit(): void { this.reload(); }

  reload(): void {
    this.loading = true;
    this.error = '';
    this.jobs.overview().subscribe({
      next: (value) => { this.overview = value; this.loading = false; },
      error: () => { this.error = 'Unable to load Jobs Center. SuperAdmin access is required.'; this.loading = false; },
    });
  }

  run(job: JobDefinition): void {
    this.runningKey = job.key;
    this.error = '';
    this.jobs.run(job.key).subscribe({
      next: () => { this.runningKey = ''; this.reload(); },
      error: () => { this.runningKey = ''; this.error = `Job ${job.name} failed to start.`; },
    });
  }

  formatResult(result: Record<string, unknown>): string {
    return JSON.stringify(result);
  }
}
