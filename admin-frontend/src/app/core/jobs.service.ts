import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface JobDefinition {
  key: string;
  name: string;
  description: string;
  category: string;
  safe_manual_run: boolean;
  last_status: string | null;
  last_run_at: string | null;
  last_duration_ms: number | null;
}

export interface JobRun {
  id: string;
  job_key: string;
  status: string;
  trigger: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  result: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
}

export interface JobsOverview {
  generated_at: string;
  totals: {
    registered_jobs: number;
    recent_runs: number;
    failed_runs: number;
    running_runs: number;
  };
  jobs: JobDefinition[];
  recent_runs: JobRun[];
  health: {
    backend: string;
    database: string;
    database_latency_ms: number;
    scheduler: string;
    worker: string;
  };
}

@Injectable({ providedIn: 'root' })
export class JobsService {
  constructor(private readonly http: HttpClient) {}

  overview(): Observable<JobsOverview> {
    return this.http.get<JobsOverview>('/api/v1/platform/jobs/overview');
  }

  run(jobKey: string): Observable<JobRun> {
    return this.http.post<JobRun>(`/api/v1/platform/jobs/${encodeURIComponent(jobKey)}/run`, {});
  }
}
