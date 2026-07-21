import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface SecurityFinding {
  id: string;
  finding_key: string;
  category: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  resource_type: string | null;
  resource_id: string | null;
  resource_name: string | null;
  recommendation: string | null;
  status: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface SecuritySummary {
  guild_id: string;
  snapshot_id: string | null;
  collected_at: string | null;
  role_count: number;
  channel_count: number;
  webhook_count: number;
  risk_score: number;
  counts: Record<string, number>;
  findings: SecurityFinding[];
}

@Injectable({ providedIn: 'root' })
export class SecurityService {
  constructor(private readonly http: HttpClient) {}

  summary(guildId: string): Observable<SecuritySummary> {
    return this.http.get<SecuritySummary>(`/api/v1/discord/guilds/${guildId}/security`);
  }
}
