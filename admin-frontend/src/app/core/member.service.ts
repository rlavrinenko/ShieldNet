import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface MemberRole { discord_role_id:string; role_name:string; role_position:number; role_color:number; }
export interface Member {
  discord_user_id:string; username:string; global_name:string|null; nickname:string|null; avatar_url:string|null;
  bot:boolean; pending:boolean; is_active:boolean; joined_at:string|null; left_at:string|null; last_activity_at:string|null;
  communication_disabled_until:string|null; presence_status:string; activity_type:string|null; activity_name:string|null;
  voice_channel_id:string|null; voice_channel_name:string|null; client_desktop:boolean; client_mobile:boolean; client_web:boolean; last_presence_at:string|null; admin_note:string|null; game_nickname:string|null; alliance_tag:string|null; leadership_rank:'R5'|'R4'|'member'|null; preferred_language:string|null; verification_status:'not_verified'|'pending'|'verified'|'rejected'|'expired'; verification_updated_at:string|null; tags:string[]; shieldnet_blocked:boolean;
  watchlisted:boolean; risk_level:'low'|'medium'|'high'|'critical'; review_due_at:string|null; review_reason:string|null; roles:MemberRole[];
}
export interface MemberList { items:Member[]; total:number; page:number; page_size:number; }
export interface MemberStats { total:number; humans:number; bots:number; pending:number; timed_out:number; blocked:number; active_24h:number; inactive_30d:number; watchlisted:number; high_risk:number; review_due:number; }

export interface MemberTimelineItem { id:string; kind:string; title:string; detail:string|null; status:string|null; severity:string|null; occurred_at:string; metadata:Record<string,unknown>; }
export interface MemberInspector { member:Member; summary:{open_cases:number;resolved_cases:number;appeals:number;evidence:number;actions:number;verification_requests:number}; permissions:string[]; verification:Array<Record<string,unknown>>; timeline:MemberTimelineItem[]; }

export interface MemberAction { id:string; action_type:string; status:string; result_message:string|null; attempt_count:number; payload:Record<string,unknown>; }

export interface MemberCase {
  id:string; guild_id:string; discord_user_id:string; title:string; category:'warning'|'spam'|'harassment'|'security'|'appeal'|'other';
  severity:'low'|'medium'|'high'|'critical'; status:'open'|'investigating'|'resolved'|'dismissed'; priority:'low'|'normal'|'high'|'urgent'; description:string|null; resolution:string|null;
  assigned_to:string|null; created_by:string|null; due_at:string|null; first_response_at:string|null; resolved_at:string|null; created_at:string; updated_at:string;
}

export interface CaseEvidence {
  id:string; guild_id:string; case_id:string; evidence_type:'link'|'screenshot'|'message'|'document'|'other'; title:string; source_url:string|null; notes:string|null; created_by:string|null; created_at:string;
}
export interface CaseAppeal {
  id:string; guild_id:string; case_id:string; status:'submitted'|'under_review'|'accepted'|'rejected'|'withdrawn'; statement:string; decision:string|null; submitted_by_name:string|null; reviewed_by:string|null; reviewed_at:string|null; created_by:string|null; created_at:string; updated_at:string;
}

@Injectable({providedIn:'root'})
export class MemberService {
  constructor(private readonly http:HttpClient) {}

  list(guildId:string, filters:Record<string,string|number|undefined>):Promise<MemberList> {
    let params = new HttpParams();
    Object.entries(filters).forEach(([key,value]) => { if (value !== undefined && value !== '') params = params.set(key, String(value)); });
    return firstValueFrom(this.http.get<MemberList>(`/api/v1/discord/guilds/${guildId}/members`, {params}));
  }
  stats(guildId:string):Promise<MemberStats> { return firstValueFrom(this.http.get<MemberStats>(`/api/v1/discord/guilds/${guildId}/members/stats`)); }
  detail(guildId:string,userId:string):Promise<Member> { return firstValueFrom(this.http.get<Member>(`/api/v1/discord/guilds/${guildId}/members/${userId}`)); }
  updateProfile(guildId:string,userId:string,payload:{game_nickname:string|null;alliance_tag:string|null;leadership_rank:string|null;preferred_language:string|null;verification_status:string;admin_note:string|null;tags:string[];watchlisted:boolean;risk_level:string;review_due_at:string|null;review_reason:string|null}):Promise<Member> {
    return firstValueFrom(this.http.patch<Member>(`/api/v1/discord/guilds/${guildId}/members/${userId}/profile`, payload));
  }
  inspector(guildId:string,userId:string):Promise<MemberInspector> { return firstValueFrom(this.http.get<MemberInspector>(`/api/v1/discord/guilds/${guildId}/members/${userId}/inspector`)); }
  actions(guildId:string,userId:string):Promise<MemberAction[]> { return firstValueFrom(this.http.get<MemberAction[]>(`/api/v1/discord/guilds/${guildId}/members/${userId}/actions`)); }
  cases(guildId:string,userId:string):Promise<MemberCase[]> { return firstValueFrom(this.http.get<MemberCase[]>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases`)); }
  createCase(guildId:string,userId:string,payload:Record<string,unknown>):Promise<MemberCase> { return firstValueFrom(this.http.post<MemberCase>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases`, payload)); }
  updateCase(guildId:string,userId:string,caseId:string,payload:Record<string,unknown>):Promise<MemberCase> { return firstValueFrom(this.http.patch<MemberCase>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}`, payload)); }
  evidence(guildId:string,userId:string,caseId:string):Promise<CaseEvidence[]> { return firstValueFrom(this.http.get<CaseEvidence[]>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/evidence`)); }
  createEvidence(guildId:string,userId:string,caseId:string,payload:Record<string,unknown>):Promise<CaseEvidence> { return firstValueFrom(this.http.post<CaseEvidence>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/evidence`, payload)); }
  deleteEvidence(guildId:string,userId:string,caseId:string,evidenceId:string):Promise<void> { return firstValueFrom(this.http.delete<void>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/evidence/${evidenceId}`)); }
  appeals(guildId:string,userId:string,caseId:string):Promise<CaseAppeal[]> { return firstValueFrom(this.http.get<CaseAppeal[]>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/appeals`)); }
  createAppeal(guildId:string,userId:string,caseId:string,payload:Record<string,unknown>):Promise<CaseAppeal> { return firstValueFrom(this.http.post<CaseAppeal>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/appeals`, payload)); }
  updateAppeal(guildId:string,userId:string,caseId:string,appealId:string,payload:Record<string,unknown>):Promise<CaseAppeal> { return firstValueFrom(this.http.patch<CaseAppeal>(`/api/v1/discord/guilds/${guildId}/members/${userId}/cases/${caseId}/appeals/${appealId}`, payload)); }
}
