import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface SimulatorMember { id:string; username:string; display_name:string; avatar_url?:string|null; bot:boolean }
export interface SimulatorChannel { id:string; name:string; type:string; parent_id?:string|null }
export interface SimulatorOptions { members:SimulatorMember[]; channels:SimulatorChannel[] }
export interface SimulatedPermission { key:string; label:string; bit:number; allowed:boolean }
export interface PermissionSource { stage:string; effect:string; source:string; source_id?:string; permissions?:number; allow?:number; deny?:number; count?:number }
export interface SimulationResult {
  guild_id:string;
  member:SimulatorMember & {owner:boolean};
  channel:SimulatorChannel;
  base_permissions:string;
  effective_permissions:string;
  administrator_bypass:boolean;
  owner_bypass:boolean;
  permissions:SimulatedPermission[];
  sources:PermissionSource[];
  role_count:number;
  snapshot_complete:boolean;
}

@Injectable({providedIn:'root'})
export class PermissionSimulatorService {
  constructor(private readonly http:HttpClient) {}
  options(guildId:string, q=''):Observable<SimulatorOptions> {
    return this.http.get<SimulatorOptions>(`/api/v1/discord/guilds/${guildId}/permission-simulator/options`, {params:new HttpParams().set('q', q)});
  }
  check(guildId:string, memberId:string, channelId:string):Observable<SimulationResult> {
    const params = new HttpParams().set('member_id', memberId).set('channel_id', channelId);
    return this.http.get<SimulationResult>(`/api/v1/discord/guilds/${guildId}/permission-simulator/check`, {params});
  }
}
