import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  constructor(private readonly http: HttpClient) {}

  overview(): Promise<any> {
    return firstValueFrom(
      this.http.get('/api/v1/dashboard/overview'),
    );
  }
}
