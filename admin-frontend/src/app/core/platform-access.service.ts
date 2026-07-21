import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PlatformAccessIdentity {
  user_id: string;
  discord_user_id: string | null;
  roles: string[];
  highest_role: string | null;
  is_superadmin: boolean;
  superadmin_source: string | null;
}

export interface PlatformAccessOverview {
  guild_count: number;
  active_memberships: number;
  user_count: number;
  configured_superadmins: number;
  configuration_key: string;
}

@Injectable({ providedIn: 'root' })
export class PlatformAccessService {
  constructor(private readonly http: HttpClient) {}

  identity(): Observable<PlatformAccessIdentity> {
    return this.http.get<PlatformAccessIdentity>('/api/v1/platform/access/me');
  }

  overview(): Observable<PlatformAccessOverview> {
    return this.http.get<PlatformAccessOverview>('/api/v1/platform/access/overview');
  }
}
