import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface PermissionRule {
  id: string;
  guild_id: string;
  module_key: string;
  permission: 'view' | 'manage' | 'execute' | 'configure';
  effect: 'allow' | 'deny';
  subject_type: 'everyone' | 'shieldnet_role' | 'discord_role' | 'discord_user';
  subject_value: string;
  enabled: boolean;
  priority: number;
}

@Injectable({ providedIn: 'root' })
export class PermissionService {
  constructor(private readonly http: HttpClient) {}

  list(guildId: string): Promise<PermissionRule[]> {
    return firstValueFrom(
      this.http.get<PermissionRule[]>(
        `/api/v1/discord/guilds/${guildId}/permissions`,
      ),
    );
  }

  save(
    guildId: string,
    moduleKey: string,
    permission: string,
    payload: Record<string, unknown>,
  ): Promise<PermissionRule> {
    return firstValueFrom(
      this.http.put<PermissionRule>(
        `/api/v1/discord/guilds/${guildId}/permissions/${moduleKey}/${permission}`,
        payload,
      ),
    );
  }

  remove(guildId: string, ruleId: string): Promise<void> {
    return firstValueFrom(
      this.http.delete<void>(
        `/api/v1/discord/guilds/${guildId}/permissions/${ruleId}`,
      ),
    );
  }
}
