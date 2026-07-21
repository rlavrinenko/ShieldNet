import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DoctorCheck {
  name: string;
  category: string;
  status: 'ok' | 'warning' | 'failed' | 'manual';
  message: string;
  details: Record<string, unknown>;
  remediation: string | null;
}

export interface DoctorReport {
  generated_at: string;
  overall_status: 'healthy' | 'degraded' | 'critical';
  summary: Record<string, number>;
  checks: DoctorCheck[];
}

@Injectable({ providedIn: 'root' })
export class DoctorService {
  constructor(private readonly http: HttpClient) {}
  report(): Observable<DoctorReport> {
    return this.http.get<DoctorReport>('/api/v1/platform/doctor/report');
  }
}
