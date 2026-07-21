import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PlatformNotification {
  id: string;
  guild_id: string | null;
  severity: string;
  category: string;
  source: string;
  title: string;
  message: string;
  status: string;
  metadata: Record<string, unknown>;
  first_seen_at: string;
  last_seen_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

export interface NotificationList {
  items: PlatformNotification[];
  total: number;
  page: number;
  page_size: number;
}

export interface NotificationSummary {
  open: number;
  acknowledged: number;
  resolved: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  constructor(private readonly http: HttpClient) {}

  list(status = '', severity = ''): Observable<NotificationList> {
    let params = new HttpParams().set('page_size', 100);
    if (status) params = params.set('status', status);
    if (severity) params = params.set('severity', severity);
    return this.http.get<NotificationList>('/api/v1/platform/notifications', { params });
  }

  summary(): Observable<NotificationSummary> {
    return this.http.get<NotificationSummary>('/api/v1/platform/notifications/summary');
  }

  evaluate(): Observable<Record<string, number>> {
    return this.http.post<Record<string, number>>('/api/v1/platform/notifications/evaluate', {});
  }

  acknowledge(id: string): Observable<PlatformNotification> {
    return this.http.post<PlatformNotification>(`/api/v1/platform/notifications/${id}/acknowledge`, {});
  }

  resolve(id: string): Observable<PlatformNotification> {
    return this.http.post<PlatformNotification>(`/api/v1/platform/notifications/${id}/resolve`, {});
  }
}
