import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface DiffGuildOption { guild_id:string; name:string; icon_url?:string; member_count:number; bot_status:string }
export interface DiffChange { kind:'source_only'|'target_only'|'changed'; name:string; source?:any; target?:any; details?:Record<string,any> }
export interface DiffSection { name:string; source_count:number; target_count:number; difference_count:number; changes:DiffChange[] }
export interface ServerDiffResult { source:any; target:any; summary:{total_differences:number; similarity_percent:number; sections_with_differences:number}; sections:DiffSection[] }

@Injectable({providedIn:'root'})
export class ServerDiffService {
  constructor(private http:HttpClient){}
  options():Observable<DiffGuildOption[]>{ return this.http.get<DiffGuildOption[]>('/api/v1/discord/server-diff/options'); }
  compare(source:string,target:string):Observable<ServerDiffResult>{
    const params=new HttpParams().set('source_guild_id',source).set('target_guild_id',target);
    return this.http.get<ServerDiffResult>('/api/v1/discord/server-diff/compare',{params});
  }
}
