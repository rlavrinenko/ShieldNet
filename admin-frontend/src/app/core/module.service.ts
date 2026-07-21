import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { GuildModule, GuildModuleUpdate } from './module.models';

@Injectable({ providedIn: 'root' })
export class ModuleService {
  constructor(private readonly http: HttpClient) {}

  list(guildId: string): Promise<GuildModule[]> {
    return firstValueFrom(
      this.http.get<GuildModule[]>(
        `/api/v1/discord/guilds/${guildId}/modules`,
      ),
    );
  }

  update(
    guildId: string,
    moduleKey: string,
    enabled: boolean,
    configuration?: Record<string, unknown>,
  ): Promise<GuildModuleUpdate> {
    return firstValueFrom(
      this.http.patch<GuildModuleUpdate>(
        `/api/v1/discord/guilds/${guildId}/modules/${moduleKey}`,
        {
          enabled,
          configuration,
        },
      ),
    );
  }
}
