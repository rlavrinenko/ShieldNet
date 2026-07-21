import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class GuildRoleService {
  constructor(private readonly http: HttpClient) {}
  list(guildId: string): Promise<any[]> {
    return firstValueFrom(
      this.http.get<any[]>(`/api/v1/discord/guilds/${guildId}/roles`),
    );
  }
}
