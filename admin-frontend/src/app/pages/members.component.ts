import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';

import { MemberActionService } from '../core/member-action.service';
import { CaseAppeal, CaseEvidence, Member, MemberAction, MemberCase, MemberService, MemberStats } from '../core/member.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  standalone:true,
  imports:[FormsModule, ShellComponent],
  template:`
  <sn-shell title="Members Control Center">
    <section class="topline">
      <div><div class="eyebrow">SHIELDNET v5.1</div><h2>Members Control Center</h2><p>Search, inspect and manage Discord members from one secure console.</p></div>
      <button class="btn secondary" (click)="reload()">↻ Refresh</button>
    </section>

    @if (stats()) {
      <section class="stats">
        <button (click)="setStatus('active')"><strong>{{stats()!.total}}</strong><span>Active</span></button>
        <button (click)="setType('human')"><strong>{{stats()!.humans}}</strong><span>Humans</span></button>
        <button (click)="setType('bot')"><strong>{{stats()!.bots}}</strong><span>Bots</span></button>
        <button (click)="setStatus('active')"><strong>{{stats()!.active_24h}}</strong><span>Active 24h</span></button>
        <button (click)="setStatus('inactive')"><strong>{{stats()!.inactive_30d}}</strong><span>Inactive 30d</span></button>
        <button (click)="setStatus('blocked')"><strong>{{stats()!.blocked}}</strong><span>Blocked</span></button>
        <button (click)="setStatus('watchlist')"><strong>{{stats()!.watchlisted}}</strong><span>Watchlist</span></button>
        <button (click)="setStatus('review_due')"><strong>{{stats()!.review_due}}</strong><span>Review due</span></button>
        <button (click)="setStatus('watchlist')"><strong>{{stats()!.high_risk}}</strong><span>High risk</span></button>
      </section>
    }

    <section class="card filters">
      <input [(ngModel)]="query" (keyup.enter)="loadMembers()" placeholder="Search Discord name, game nickname, alliance, language or ID">
      <select [(ngModel)]="memberType" (change)="loadMembers()"><option value="all">All types</option><option value="human">Humans</option><option value="bot">Bots</option></select>
      <select [(ngModel)]="statusFilter" (change)="loadMembers()"><option value="active">Active</option><option value="pending">Pending</option><option value="timed_out">Timed out</option><option value="blocked">ShieldNet blocked</option><option value="inactive">Inactive 30d</option><option value="watchlist">Watchlist</option><option value="review_due">Review due</option><option value="left">Left server</option></select>
      <select [(ngModel)]="sort" (change)="loadMembers()"><option value="activity">Recent activity</option><option value="name">Name A–Z</option><option value="joined">Newest joined</option><option value="oldest">Oldest joined</option></select>
      <button class="btn" (click)="loadMembers()">Search</button>
    </section>

    @if (selectedIds.size) {
      <section class="card bulk">
        <strong>{{selectedIds.size}} selected</strong>
        <input [(ngModel)]="bulkMessage" placeholder="Message for selected members">
        <button class="btn secondary" (click)="bulk('send_dm')">Send DM</button>
        <button class="btn secondary" (click)="bulk('shieldnet_block')">Block</button>
        <button class="btn secondary" (click)="bulk('shieldnet_unblock')">Unblock</button>
        <button class="link" (click)="clearSelection()">Clear</button>
      </section>
    }

    @if (error()) { <section class="card alert">{{error()}}</section> }

    <section class="workspace">
      <div class="card table-card">
        <div class="table-head"><label><input type="checkbox" [checked]="allSelected()" (change)="toggleAll($event)"> Select all</label><span>{{total}} members</span></div>
        @if (loading()) { <div class="empty">Loading members…</div> }
        @for (member of members(); track member.discord_user_id) {
          <article class="member" [class.active]="selected()?.discord_user_id===member.discord_user_id" (click)="open(member)">
            <input type="checkbox" [checked]="selectedIds.has(member.discord_user_id)" (click)="$event.stopPropagation()" (change)="toggle(member.discord_user_id)">
            <div class="avatar">@if(member.avatar_url){<img [src]="member.avatar_url" alt="">}@else{<span>{{initial(member)}}</span>}</div>
            <div class="identity"><strong>{{displayName(member)}}</strong><span>@{{member.username}} · {{member.discord_user_id}}</span><div class="chips">@if(member.bot){<i>BOT</i>} @if(member.pending){<i>Pending</i>} @if(member.shieldnet_blocked){<i class="danger">Blocked</i>} @if(member.watchlisted){<i class="risk" [class]="member.risk_level">{{member.risk_level}} risk</i>} @for(tag of member.tags; track tag){<i>{{tag}}</i>}</div></div>
            <div class="roles">@for(role of member.roles.slice(0,2); track role.discord_role_id){<span>{{role.role_name}}</span>} @if(member.roles.length>2){<span>+{{member.roles.length-2}}</span>}</div>
            <div class="activity"><strong>{{relative(member.last_activity_at)}}</strong><span>Last activity</span></div>
          </article>
        } @empty { @if(!loading()){<div class="empty">No members match these filters.</div>} }
        <div class="pager"><button [disabled]="page===1" (click)="changePage(-1)">Previous</button><span>Page {{page}} / {{pages}}</span><button [disabled]="page>=pages" (click)="changePage(1)">Next</button></div>
      </div>

      <aside class="card inspector" [class.open]="selected()">
        @if (selected(); as member) {
          <div class="profile"><div class="avatar large">@if(member.avatar_url){<img [src]="member.avatar_url" alt="">}@else{<span>{{initial(member)}}</span>}</div><h3>{{displayName(member)}}</h3><p>@{{member.username}}</p><code>{{member.discord_user_id}}</code><button class="btn secondary" (click)="openFullInspector(member)">Open full inspector</button></div>
          <div class="quick-actions"><button (click)="promptAction('send_dm')">Message</button><button (click)="promptAction('rename')">Rename</button><button (click)="promptAction(member.shieldnet_blocked?'shieldnet_unblock':'shieldnet_block')">{{member.shieldnet_blocked?'Unblock':'Block'}}</button><button class="danger" (click)="promptAction('kick')">Kick</button><button class="danger" (click)="promptAction('ban')">Ban</button></div>
          <div class="facts"><div><span>Joined</span><strong>{{date(member.joined_at)}}</strong></div><div><span>Last activity</span><strong>{{date(member.last_activity_at)}}</strong></div><div><span>Roles</span><strong>{{member.roles.length}}</strong></div><div><span>Status</span><strong>{{member.is_active?'Active':'Left'}}</strong></div></div>
          <div class="review-grid"><label class="check"><input type="checkbox" [(ngModel)]="watchlisted"> Watchlist member</label><label class="field">Risk level<select [(ngModel)]="riskLevel"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></label></div>
          <label class="field">Review due<input type="datetime-local" [(ngModel)]="reviewDueAt"></label>
          <label class="field">Review reason<textarea [(ngModel)]="reviewReason" rows="3" placeholder="Reason for monitoring or follow-up"></textarea></label>
          <label class="field">Tags<input [(ngModel)]="tagsText" placeholder="trusted, vip, review"></label>
          <label class="field">Private admin note<textarea [(ngModel)]="adminNote" rows="5" placeholder="Visible only to authorized ShieldNet staff"></textarea></label>
          <button class="btn save" (click)="saveProfile()">Save profile</button>
          <div class="section"><h4>Member cases</h4>
            <div class="case-form">
              <input [(ngModel)]="caseTitle" placeholder="Case title">
              <select [(ngModel)]="caseCategory"><option value="warning">Warning</option><option value="spam">Spam</option><option value="harassment">Harassment</option><option value="security">Security</option><option value="appeal">Appeal</option><option value="other">Other</option></select>
              <select [(ngModel)]="caseSeverity"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select>
              <textarea [(ngModel)]="caseDescription" rows="3" placeholder="Incident details"></textarea>
              <button class="btn" (click)="createCase()">Create case</button>
            </div>
            @for(item of cases(); track item.id){<article class="case-item" [class.selected-case]="selectedCaseId===item.id"><div><strong>{{item.title}}</strong><span>{{item.category}} · {{item.severity}}</span></div><select [ngModel]="item.status" (ngModelChange)="changeCaseStatus(item,$event)"><option value="open">Open</option><option value="investigating">Investigating</option><option value="resolved">Resolved</option><option value="dismissed">Dismissed</option></select><p>{{item.description||'No description'}}</p><small>{{date(item.created_at)}}</small><button class="case-open" (click)="openCase(item)">Evidence & appeals</button></article>} @empty {<p class="muted">No cases recorded.</p>}
          </div>
          @if(selectedCaseId){
            <div class="section case-center"><h4>Evidence & Appeals</h4>
              <div class="case-form"><strong>Evidence</strong><input [(ngModel)]="evidenceTitle" placeholder="Evidence title"><select [(ngModel)]="evidenceType"><option value="link">Link</option><option value="screenshot">Screenshot</option><option value="message">Message</option><option value="document">Document</option><option value="other">Other</option></select><input [(ngModel)]="evidenceUrl" placeholder="https://..."><textarea [(ngModel)]="evidenceNotes" rows="2" placeholder="Evidence notes"></textarea><button class="btn" (click)="createEvidence()">Add evidence</button></div>
              @for(item of evidence(); track item.id){<article class="evidence-item"><div><strong>{{item.title}}</strong><span>{{item.evidence_type}} · {{date(item.created_at)}}</span></div>@if(item.source_url){<a [href]="item.source_url" target="_blank" rel="noopener">Open source</a>}<p>{{item.notes||'No notes'}}</p><button class="danger-link" (click)="removeEvidence(item)">Delete</button></article>} @empty {<p class="muted">No evidence attached.</p>}
              <div class="case-form"><strong>Appeal</strong><input [(ngModel)]="appealName" placeholder="Submitted by"><textarea [(ngModel)]="appealStatement" rows="3" placeholder="Appeal statement"></textarea><button class="btn secondary" (click)="createAppeal()">Register appeal</button></div>
              @for(item of appeals(); track item.id){<article class="appeal-item"><div><strong>{{item.submitted_by_name||'Member appeal'}}</strong><span>{{date(item.created_at)}}</span></div><select [ngModel]="item.status" (ngModelChange)="changeAppealStatus(item,$event)"><option value="submitted">Submitted</option><option value="under_review">Under review</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option><option value="withdrawn">Withdrawn</option></select><p>{{item.statement}}</p>@if(item.decision){<small>Decision: {{item.decision}}</small>}<button class="case-open" (click)="setAppealDecision(item)">Set decision</button></article>} @empty {<p class="muted">No appeals registered.</p>}
            </div>
          }
          <div class="section"><h4>Roles</h4><div class="role-list">@for(role of member.roles; track role.discord_role_id){<span>{{role.role_name}}</span>}</div></div>
          <div class="section"><h4>Action history</h4>@for(action of actions(); track action.id){<div class="history"><span>{{action.action_type}}</span><b [class]="action.status">{{action.status}}</b><small>{{action.result_message||'Queued through Discord bot'}}</small></div>} @empty {<p class="muted">No actions recorded.</p>}</div>
        } @else { <div class="empty inspector-empty">Select a member to open the control panel.</div> }
      </aside>
    </section>
  </sn-shell>`,
  styles:[`
    h2,h3,h4,p{margin:.2rem 0}.topline{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}.topline p,.eyebrow{color:var(--muted)}.eyebrow{font-size:.72rem;letter-spacing:.18em;font-weight:800;color:#8e9aff}
    .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin-bottom:1rem}.stats button{background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:14px;padding:1rem;text-align:left}.stats strong{display:block;font-size:1.45rem}.stats span{color:var(--muted);font-size:.8rem}
    .profile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem}.filters{display:grid;grid-template-columns:minmax(260px,2fr) repeat(3,minmax(130px,1fr)) auto;gap:.7rem;padding:.8rem;margin-bottom:1rem}.filters input,.filters select,.bulk input,.field input,.field textarea{width:100%;background:var(--panel-2);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:.72rem}.bulk{display:flex;align-items:center;gap:.7rem;padding:.8rem;margin-bottom:1rem}.bulk input{flex:1}.link{background:none;color:var(--muted)}.alert{padding:1rem;color:#ffd0d6;margin-bottom:1rem}
    .workspace{display:grid;grid-template-columns:minmax(0,1fr) 390px;gap:1rem}.table-card{overflow:hidden}.table-head,.pager{display:flex;justify-content:space-between;padding:.8rem 1rem;color:var(--muted);border-bottom:1px solid var(--line)}.member{display:grid;grid-template-columns:24px 48px minmax(220px,1fr) minmax(130px,.6fr) 110px;gap:.8rem;align-items:center;padding:.8rem 1rem;border-bottom:1px solid var(--line);cursor:pointer}.member:hover,.member.active{background:var(--primary-soft)}
    .avatar{width:46px;height:46px;border-radius:14px;overflow:hidden;background:linear-gradient(135deg,var(--primary),#9a64ff);display:grid;place-items:center;font-weight:900}.avatar img{width:100%;height:100%;object-fit:cover}.identity{min-width:0}.identity>strong,.identity>span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.identity>span,.activity span{color:var(--muted);font-size:.78rem}.chips,.role-list{display:flex;gap:.3rem;flex-wrap:wrap;margin-top:.35rem}.chips i,.roles span,.role-list span{font-style:normal;font-size:.68rem;padding:.2rem .42rem;border-radius:999px;background:var(--panel-2);border:1px solid var(--line)}.chips .danger{color:#ff8997}.chips .risk.medium{color:#ffc76b}.chips .risk.high,.chips .risk.critical{color:#ff8997}.review-grid{display:grid;grid-template-columns:1fr 1fr;gap:.7rem;align-items:end}.check{display:flex;align-items:center;gap:.5rem;color:var(--muted);font-size:.8rem;padding:.75rem 0}.field select{width:100%;background:var(--panel-2);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:.72rem}.roles{display:flex;gap:.3rem;flex-wrap:wrap}.activity{text-align:right}.activity strong{display:block;font-size:.82rem}.empty{padding:2rem;text-align:center;color:var(--muted)}.pager{border:0}.pager button{background:var(--panel-2);border:1px solid var(--line);color:var(--text);padding:.5rem .8rem;border-radius:8px}.pager button:disabled{opacity:.4}
    .inspector{padding:1rem;align-self:start;position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto}.profile{text-align:center;padding:.5rem}.avatar.large{width:76px;height:76px;border-radius:22px;margin:auto}.profile p,.profile code{color:var(--muted)}.quick-actions{display:grid;grid-template-columns:repeat(3,1fr);gap:.4rem;margin:1rem 0}.quick-actions button{padding:.6rem .3rem;border-radius:9px;background:var(--panel-2);border:1px solid var(--line);color:var(--text)}button.danger,.quick-actions .danger{color:#ff8997}.facts{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:1rem}.facts div{background:var(--panel-2);border-radius:10px;padding:.7rem}.facts span,.facts strong{display:block}.facts span{font-size:.7rem;color:var(--muted)}.field{display:grid;gap:.35rem;color:var(--muted);font-size:.8rem;margin:.8rem 0}.save{width:100%}.section{border-top:1px solid var(--line);margin-top:1rem;padding-top:1rem}.history{display:grid;grid-template-columns:1fr auto;gap:.25rem;padding:.55rem 0;border-bottom:1px solid var(--line);font-size:.8rem}.history small{grid-column:1/-1;color:var(--muted)}.history b{font-size:.68rem;text-transform:uppercase}.case-form{display:grid;gap:.45rem;margin:.6rem 0}.case-form input,.case-form select,.case-form textarea,.case-item select{width:100%;background:var(--panel-2);border:1px solid var(--line);border-radius:9px;color:var(--text);padding:.6rem}.case-item{display:grid;grid-template-columns:1fr 130px;gap:.35rem;padding:.7rem 0;border-bottom:1px solid var(--line)}.case-item div span,.case-item small{display:block;color:var(--muted);font-size:.72rem}.case-item p,.case-item small{grid-column:1/-1}.case-item p{margin:.25rem 0;font-size:.82rem}.case-open,.danger-link{background:none;border:0;color:#91a2ff;text-align:left;padding:.25rem 0;cursor:pointer}.danger-link{color:#ff8997}.selected-case{background:var(--primary-soft)}.case-center{display:grid;gap:.55rem}.evidence-item,.appeal-item{display:grid;grid-template-columns:1fr auto;gap:.35rem;padding:.7rem;border:1px solid var(--line);border-radius:10px;background:var(--panel-2)}.evidence-item span,.appeal-item span,.appeal-item small{display:block;color:var(--muted);font-size:.72rem}.evidence-item p,.appeal-item p,.evidence-item .danger-link,.appeal-item .case-open,.appeal-item small{grid-column:1/-1}.appeal-item select{background:var(--panel);border:1px solid var(--line);border-radius:8px;color:var(--text);padding:.45rem}.completed{color:var(--success)}.failed{color:var(--danger)}.processing{color:var(--warning)}
    @media(max-width:1200px){.stats{grid-template-columns:repeat(3,1fr)}.workspace{grid-template-columns:1fr}.inspector{position:static;max-height:none}}@media(max-width:760px){.profile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem}.filters{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.member{grid-template-columns:24px 46px 1fr}.roles,.activity{display:none}.bulk{flex-wrap:wrap}.topline{align-items:flex-start}.topline p{display:none}}
  `]
})
export class MembersComponent implements OnInit {
  readonly guildId=this.route.snapshot.paramMap.get('guildId') ?? '';
  readonly members=signal<Member[]>([]); readonly selected=signal<Member|null>(null); readonly stats=signal<MemberStats|null>(null); readonly actions=signal<MemberAction[]>([]); readonly cases=signal<MemberCase[]>([]); readonly evidence=signal<CaseEvidence[]>([]); readonly appeals=signal<CaseAppeal[]>([]); readonly loading=signal(false); readonly error=signal('');
  query=''; memberType='all'; statusFilter='active'; sort='activity'; page=1; pageSize=50; total=0; selectedIds=new Set<string>(); adminNote=''; tagsText=''; bulkMessage=''; gameNickname=''; allianceTag=''; leadershipRank:'R5'|'R4'|'member'|null=null; preferredLanguage=''; verificationStatus:'not_verified'|'pending'|'verified'|'rejected'|'expired'='not_verified'; watchlisted=false; riskLevel:'low'|'medium'|'high'|'critical'='low'; reviewDueAt=''; reviewReason=''; caseTitle=''; caseCategory:'warning'|'spam'|'harassment'|'security'|'appeal'|'other'='other'; caseSeverity:'low'|'medium'|'high'|'critical'='medium'; caseDescription=''; selectedCaseId=''; evidenceTitle=''; evidenceType:'link'|'screenshot'|'message'|'document'|'other'='link'; evidenceUrl=''; evidenceNotes=''; appealName=''; appealStatement='';
  constructor(private route:ActivatedRoute,private service:MemberService,private actionService:MemberActionService,private router:Router){}
  async ngOnInit(){await this.reload();}
  get pages(){return Math.max(1,Math.ceil(this.total/this.pageSize));}
  async reload(){await Promise.all([this.loadMembers(),this.loadStats()]);}
  async loadStats(){try{this.stats.set(await this.service.stats(this.guildId));}catch{}}
  async loadMembers(){this.loading.set(true);this.error.set('');try{const r=await this.service.list(this.guildId,{query:this.query,page:this.page,page_size:this.pageSize,member_type:this.memberType,status_filter:this.statusFilter,sort:this.sort});this.members.set(r.items);this.total=r.total;}catch(error){this.error.set(this.requestError(error,'Unable to load members.'));}finally{this.loading.set(false)}}
  private requestError(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 401) return 'Your session has expired. Sign in again.';
      if (error.status === 403) return 'You do not have permission to manage this server.';
      if (error.status === 0) return 'The server is temporarily unavailable.';
      const detail = typeof error.error?.detail === 'string' ? error.error.detail : '';
      if (detail) return detail;
    }
    return fallback;
  }

  async open(m:Member){try{const full=await this.service.detail(this.guildId,m.discord_user_id);this.selected.set(full);this.gameNickname=full.game_nickname||'';this.allianceTag=full.alliance_tag||'';this.leadershipRank=full.leadership_rank;this.preferredLanguage=full.preferred_language||'';this.verificationStatus=full.verification_status;this.adminNote=full.admin_note||'';this.tagsText=full.tags.join(', ');this.watchlisted=full.watchlisted;this.riskLevel=full.risk_level;this.reviewDueAt=this.toLocalInput(full.review_due_at);this.reviewReason=full.review_reason||'';this.actions.set(await this.service.actions(this.guildId,m.discord_user_id));this.cases.set(await this.service.cases(this.guildId,m.discord_user_id));this.selectedCaseId='';this.evidence.set([]);this.appeals.set([]);}catch{this.error.set('Unable to open member profile.')}}
  displayName(m:Member){return m.nickname||m.global_name||m.username} initial(m:Member){return this.displayName(m).slice(0,1).toUpperCase()}
  relative(value:string|null){if(!value)return 'No activity';const ms=Date.now()-new Date(value).getTime(),d=Math.floor(ms/86400000),h=Math.floor(ms/3600000);return d>0?`${d}d ago`:h>0?`${h}h ago`:'Recently'}
  date(value:string|null){return value?new Date(value).toLocaleString():'—'}
  toLocalInput(value:string|null){if(!value)return '';const d=new Date(value),pad=(v:number)=>String(v).padStart(2,'0');return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`}
  toIso(value:string){return value?new Date(value).toISOString():null}
  setStatus(v:string){this.statusFilter=v;this.page=1;this.loadMembers()} setType(v:string){this.memberType=v;this.page=1;this.loadMembers()}
  toggle(id:string){this.selectedIds.has(id)?this.selectedIds.delete(id):this.selectedIds.add(id)} allSelected(){return this.members().length>0&&this.members().every(m=>this.selectedIds.has(m.discord_user_id))}
  toggleAll(e:Event){const checked=(e.target as HTMLInputElement).checked;this.members().forEach(m=>checked?this.selectedIds.add(m.discord_user_id):this.selectedIds.delete(m.discord_user_id))} clearSelection(){this.selectedIds.clear()}
  async changePage(delta:number){this.page+=delta;await this.loadMembers()}
  async saveProfile(){const m=this.selected();if(!m)return;try{const tags=this.tagsText.split(',').map(v=>v.trim()).filter(Boolean);const updated=await this.service.updateProfile(this.guildId,m.discord_user_id,{game_nickname:this.gameNickname||null,alliance_tag:this.allianceTag||null,leadership_rank:this.leadershipRank,preferred_language:this.preferredLanguage||null,verification_status:this.verificationStatus,admin_note:this.adminNote||null,tags,watchlisted:this.watchlisted,risk_level:this.riskLevel,review_due_at:this.toIso(this.reviewDueAt),review_reason:this.reviewReason||null});this.selected.set(updated);await this.loadMembers();}catch{this.error.set('Unable to save member profile.')}}
  async promptAction(type:string){const m=this.selected();if(!m)return;let payload:Record<string,unknown>={};if(type==='send_dm'){const message=window.prompt('Direct message');if(!message)return;payload={message}}if(type==='rename'){const nickname=window.prompt('New nickname',m.nickname||'');if(nickname===null)return;payload={nickname}}if((type==='kick'||type==='ban')&&!window.confirm(`Confirm ${type} for ${this.displayName(m)}?`))return;await this.actionService.create(this.guildId,m.discord_user_id,type,payload);this.actions.set(await this.service.actions(this.guildId,m.discord_user_id));this.cases.set(await this.service.cases(this.guildId,m.discord_user_id));}

  async createCase(){const m=this.selected();if(!m||!this.caseTitle.trim())return;try{await this.service.createCase(this.guildId,m.discord_user_id,{title:this.caseTitle,category:this.caseCategory,severity:this.caseSeverity,description:this.caseDescription||null});this.caseTitle='';this.caseDescription='';this.cases.set(await this.service.cases(this.guildId,m.discord_user_id));}catch{this.error.set('Unable to create member case.')}}
  async changeCaseStatus(item:MemberCase,status:string){const m=this.selected();if(!m)return;try{await this.service.updateCase(this.guildId,m.discord_user_id,item.id,{status});this.cases.set(await this.service.cases(this.guildId,m.discord_user_id));}catch{this.error.set('Unable to update member case.')}}
  async openCase(item:MemberCase){const m=this.selected();if(!m)return;this.selectedCaseId=item.id;try{const [evidence,appeals]=await Promise.all([this.service.evidence(this.guildId,m.discord_user_id,item.id),this.service.appeals(this.guildId,m.discord_user_id,item.id)]);this.evidence.set(evidence);this.appeals.set(appeals);}catch{this.error.set('Unable to load case evidence and appeals.')}}
  async createEvidence(){const m=this.selected();if(!m||!this.selectedCaseId||!this.evidenceTitle.trim())return;try{await this.service.createEvidence(this.guildId,m.discord_user_id,this.selectedCaseId,{title:this.evidenceTitle,evidence_type:this.evidenceType,source_url:this.evidenceUrl||null,notes:this.evidenceNotes||null});this.evidenceTitle='';this.evidenceUrl='';this.evidenceNotes='';this.evidence.set(await this.service.evidence(this.guildId,m.discord_user_id,this.selectedCaseId));}catch{this.error.set('Unable to add evidence. Verify that the URL is valid.')}}
  async removeEvidence(item:CaseEvidence){const m=this.selected();if(!m||!this.selectedCaseId||!window.confirm('Delete this evidence record?'))return;try{await this.service.deleteEvidence(this.guildId,m.discord_user_id,this.selectedCaseId,item.id);this.evidence.set(await this.service.evidence(this.guildId,m.discord_user_id,this.selectedCaseId));}catch{this.error.set('Unable to delete evidence.')}}
  async createAppeal(){const m=this.selected();if(!m||!this.selectedCaseId||!this.appealStatement.trim())return;try{await this.service.createAppeal(this.guildId,m.discord_user_id,this.selectedCaseId,{statement:this.appealStatement,submitted_by_name:this.appealName||null});this.appealName='';this.appealStatement='';this.appeals.set(await this.service.appeals(this.guildId,m.discord_user_id,this.selectedCaseId));}catch{this.error.set('Unable to register appeal.')}}
  async changeAppealStatus(item:CaseAppeal,status:string){const m=this.selected();if(!m||!this.selectedCaseId)return;try{await this.service.updateAppeal(this.guildId,m.discord_user_id,this.selectedCaseId,item.id,{status});this.appeals.set(await this.service.appeals(this.guildId,m.discord_user_id,this.selectedCaseId));}catch{this.error.set('Unable to update appeal.')}}
  async setAppealDecision(item:CaseAppeal){const m=this.selected();if(!m||!this.selectedCaseId)return;const decision=window.prompt('Appeal decision',item.decision||'');if(decision===null)return;try{await this.service.updateAppeal(this.guildId,m.discord_user_id,this.selectedCaseId,item.id,{decision});this.appeals.set(await this.service.appeals(this.guildId,m.discord_user_id,this.selectedCaseId));}catch{this.error.set('Unable to save appeal decision.')}}
  openFullInspector(member:Member){this.router.navigate(['/guild',this.guildId,'members',member.discord_user_id]);}
  async bulk(type:string){if(type==='send_dm'&&!this.bulkMessage.trim())return;const ids=[...this.selectedIds];try{await Promise.all(ids.map(id=>this.actionService.create(this.guildId,id,type,type==='send_dm'?{message:this.bulkMessage}:{})));this.clearSelection();this.bulkMessage='';}catch{this.error.set('One or more bulk actions could not be queued.')}}
}
