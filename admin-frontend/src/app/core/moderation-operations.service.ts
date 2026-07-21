import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface ModerationCase {
  id:string; guild_id:string; discord_user_id:string; member_name:string; member_avatar_url:string|null;
  title:string; category:string; severity:string; priority:'low'|'normal'|'high'|'urgent'; status:'open'|'investigating'|'resolved'|'dismissed';
  assigned_to:string|null; assignee_name:string|null; due_at:string|null; first_response_at:string|null; resolved_at:string|null;
  created_at:string; updated_at:string; overdue:boolean;
}
export interface ModerationCaseList { items:ModerationCase[]; total:number; page:number; page_size:number; }
export interface ModerationStats { total_open:number; investigating:number; overdue:number; urgent:number; unassigned:number; due_today:number; resolved_7d:number; }
export interface ModeratorWorkload { user_id:string|null; display_name:string; open_cases:number; overdue_cases:number; urgent_cases:number; }

@Injectable({providedIn:'root'})
export class ModerationOperationsService {
  constructor(private readonly http:HttpClient) {}
  list(guildId:string, filters:Record<string,string|number|boolean|undefined>):Promise<ModerationCaseList> {
    let params=new HttpParams();
    Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!=='')params=params.set(k,String(v));});
    return firstValueFrom(this.http.get<ModerationCaseList>(`/api/v1/discord/guilds/${guildId}/moderation/cases`,{params}));
  }
  stats(guildId:string):Promise<ModerationStats>{return firstValueFrom(this.http.get<ModerationStats>(`/api/v1/discord/guilds/${guildId}/moderation/stats`));}
  workload(guildId:string):Promise<ModeratorWorkload[]>{return firstValueFrom(this.http.get<ModeratorWorkload[]>(`/api/v1/discord/guilds/${guildId}/moderation/workload`));}
  update(guildId:string,item:ModerationCase,payload:Record<string,unknown>):Promise<unknown>{
    return firstValueFrom(this.http.patch(`/api/v1/discord/guilds/${guildId}/members/${item.discord_user_id}/cases/${item.id}`,payload));
  }
}
