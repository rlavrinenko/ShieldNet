import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface AutomationCondition { field:string; operator:string; value:any }
export interface AutomationAction { type:string; parameters:Record<string,any> }
export interface AutomationRule { id:string; guild_id:string; name:string; description?:string; trigger_type:string; conditions:AutomationCondition[]; actions:AutomationAction[]; status:string; stop_on_error:boolean; execution_count:number; failure_count:number; last_executed_at?:string; max_failures:number; disabled_reason?:string; created_at:string; updated_at:string }

@Injectable({providedIn:'root'})
export class AutomationService {
  constructor(private http:HttpClient){}
  catalog(guildId:string):Observable<any>{return this.http.get(`/api/v1/discord/guilds/${guildId}/automations/catalog`)}
  list(guildId:string):Observable<AutomationRule[]>{return this.http.get<AutomationRule[]>(`/api/v1/discord/guilds/${guildId}/automations`)}
  create(guildId:string,payload:any):Observable<AutomationRule>{return this.http.post<AutomationRule>(`/api/v1/discord/guilds/${guildId}/automations`,payload)}
  update(guildId:string,id:string,payload:any):Observable<AutomationRule>{return this.http.put<AutomationRule>(`/api/v1/discord/guilds/${guildId}/automations/${id}`,payload)}
  status(guildId:string,id:string,status:string):Observable<AutomationRule>{return this.http.post<AutomationRule>(`/api/v1/discord/guilds/${guildId}/automations/${id}/status`,{status})}
  dryRun(guildId:string,id:string,context:any):Observable<any>{return this.http.post(`/api/v1/discord/guilds/${guildId}/automations/${id}/dry-run`,{context})}
  runs(guildId:string,id:string):Observable<any[]>{return this.http.get<any[]>(`/api/v1/discord/guilds/${guildId}/automations/${id}/runs`)}
  monitorSummary(guildId:string):Observable<any>{return this.http.get(`/api/v1/discord/guilds/${guildId}/automations-monitor/summary`)}
  monitorRuns(guildId:string,statusFilter:string=''):Observable<any[]>{const q=statusFilter?`?status_filter=${encodeURIComponent(statusFilter)}`:'';return this.http.get<any[]>(`/api/v1/discord/guilds/${guildId}/automations-monitor/runs${q}`)}
  retryRun(guildId:string,id:string):Observable<any>{return this.http.post(`/api/v1/discord/guilds/${guildId}/automations-monitor/runs/${id}/retry`,{})}
  schedules(guildId:string):Observable<any[]>{return this.http.get<any[]>(`/api/v1/discord/guilds/${guildId}/automation-schedules`)}
  saveSchedule(guildId:string,ruleId:string,payload:any):Observable<any>{return this.http.put(`/api/v1/discord/guilds/${guildId}/automations/${ruleId}/schedule`,payload)}
  deleteSchedule(guildId:string,ruleId:string):Observable<void>{return this.http.delete<void>(`/api/v1/discord/guilds/${guildId}/automations/${ruleId}/schedule`)}
  remove(guildId:string,id:string):Observable<void>{return this.http.delete<void>(`/api/v1/discord/guilds/${guildId}/automations/${id}`)}
}
