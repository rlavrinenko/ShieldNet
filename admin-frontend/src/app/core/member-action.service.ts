import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class MemberActionService {
  constructor(private readonly http: HttpClient) {}

  create(
    guildId: string,
    userId: string,
    actionType: string,
    payload: Record<string, unknown>,
  ): Promise<unknown> {
    return firstValueFrom(
      this.http.post(
        `/api/v1/discord/guilds/${guildId}/members/${userId}/actions`,
        { action_type: actionType, payload },
      ),
    );
  }
}
