import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ServerControlService {
  constructor(private readonly http: HttpClient) {}

  overview(guildId: string): Promise<any> {
    return firstValueFrom(
      this.http.get(
        `/api/v1/discord/guilds/${guildId}/control-center`,
      ),
    );
  }
}
