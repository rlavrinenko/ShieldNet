import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface PluginManifest {
  plugin_key: string;
  name: string;
  version: string;
  description: string | null;
  author: string | null;
  min_core_version: string | null;
  manifest_path: string;
  signature_status: string;
  enabled: boolean;
  healthy: boolean;
  last_error: string | null;
  capabilities: string[];
  components: Record<string, boolean>;
  manifest: Record<string, unknown>;
  updated_at: string;
}

export interface PluginScanResult {
  discovered: number;
  updated: number;
  missing: number;
  errors: string[];
}

@Injectable({ providedIn: 'root' })
export class PluginService {
  constructor(private readonly http: HttpClient) {}

  list(): Promise<PluginManifest[]> {
    return firstValueFrom(this.http.get<PluginManifest[]>('/api/v1/platform/plugins'));
  }

  scan(): Promise<PluginScanResult> {
    return firstValueFrom(this.http.post<PluginScanResult>('/api/v1/platform/plugins/scan', {}));
  }

  setEnabled(pluginKey: string, enabled: boolean): Promise<PluginManifest> {
    return firstValueFrom(
      this.http.patch<PluginManifest>(`/api/v1/platform/plugins/${pluginKey}`, { enabled }),
    );
  }
}
