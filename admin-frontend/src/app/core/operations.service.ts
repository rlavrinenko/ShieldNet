import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface OperationsSnapshot {
  generated_at: string;
  components: Record<string, {
    status: string;
    latency_ms?: number | null;
    queue_depth?: number;
    memory_bytes?: number | null;
  }>;
  workers: Array<{
    worker_name: string;
    worker_type: string;
    status: string;
    reported_status: string;
    metadata: Record<string, unknown>;
    started_at: string;
    last_seen_at: string;
  }>;
  events: Array<{
    id: string;
    guild_id: string | null;
    event_type: string;
    target_type: string | null;
    target_id: string | null;
    result: string;
    message: string | null;
    created_at: string;
  }>;
}

@Injectable({ providedIn: 'root' })
export class OperationsService {
  constructor(private readonly http: HttpClient) {}
  snapshot(): Observable<OperationsSnapshot> {
    return this.http.get<OperationsSnapshot>('/api/v1/platform/operations/snapshot');
  }
}
