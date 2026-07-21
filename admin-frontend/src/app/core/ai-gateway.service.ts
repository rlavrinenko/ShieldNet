import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface AIProvider {
  id: string; guild_id: string; name: string; provider_type: string; api_base_url?: string | null;
  key_hint?: string | null; default_model?: string | null; enabled: boolean; priority: number;
  last_health_status?: string | null; last_health_latency_ms?: number | null; last_error?: string | null;
}

@Injectable({ providedIn: 'root' })
export class AIGatewayService {
  constructor(private readonly http: HttpClient) {}
  list(guildId: string): Promise<AIProvider[]> { return firstValueFrom(this.http.get<AIProvider[]>(`/api/v1/discord/guilds/${guildId}/ai/providers`)); }
  create(guildId: string, payload: any): Promise<AIProvider> { return firstValueFrom(this.http.post<AIProvider>(`/api/v1/discord/guilds/${guildId}/ai/providers`, payload)); }
  test(guildId: string, providerId: string): Promise<any> { return firstValueFrom(this.http.post(`/api/v1/discord/guilds/${guildId}/ai/providers/${providerId}/test`, {})); }
  remove(guildId: string, providerId: string): Promise<void> { return firstValueFrom(this.http.delete<void>(`/api/v1/discord/guilds/${guildId}/ai/providers/${providerId}`)); }
}
