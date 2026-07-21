import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { TokenPair, UserProfile } from './api.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly accessKey = 'shieldnet_access_token';
  private readonly refreshKey = 'shieldnet_refresh_token';

  readonly profile = signal<UserProfile | null>(null);
  readonly authenticated = computed(() => Boolean(this.accessToken));

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router,
  ) {}

  get accessToken(): string | null {
    return sessionStorage.getItem(this.accessKey);
  }

  get refreshToken(): string | null {
    return sessionStorage.getItem(this.refreshKey);
  }

  async startDiscordLogin(): Promise<void> {
    const response = await firstValueFrom(
      this.http.get<{ authorization_url: string }>(
        '/api/v1/auth/discord/start',
      ),
    );

    const popup = window.open(
      response.authorization_url,
      'shieldnet-discord-oauth',
      'width=540,height=760',
    );

    if (!popup) {
      throw new Error('Popup was blocked by the browser.');
    }

    await new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        window.removeEventListener('message', listener);
        reject(new Error('Discord authentication timed out.'));
      }, 120000);

      const listener = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) {
          return;
        }

        const payload = event.data as {
          type?: string;
          tokens?: TokenPair;
          error?: string;
        };

        if (payload.type !== 'shieldnet-oauth-result') {
          return;
        }

        window.clearTimeout(timeout);
        window.removeEventListener('message', listener);

        if (payload.error || !payload.tokens) {
          reject(new Error(payload.error || 'Discord login failed.'));
          return;
        }

        this.saveTokens(payload.tokens);
        resolve();
      };

      window.addEventListener('message', listener);
    });

    await this.loadProfile();
    await this.router.navigateByUrl('/');
  }

  saveTokens(tokens: TokenPair): void {
    sessionStorage.setItem(this.accessKey, tokens.access_token);
    sessionStorage.setItem(this.refreshKey, tokens.refresh_token);
  }

  async loadProfile(): Promise<UserProfile> {
    const profile = await firstValueFrom(
      this.http.get<UserProfile>('/api/v1/auth/me'),
    );
    this.profile.set(profile);
    return profile;
  }

  logout(): void {
    sessionStorage.removeItem(this.accessKey);
    sessionStorage.removeItem(this.refreshKey);
    this.profile.set(null);
    void this.router.navigateByUrl('/login');
  }
}
