import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MemberInspector, MemberService } from '../core/member.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  standalone:true,
  imports:[ShellComponent, DatePipe, RouterLink],
  template:`
  <sn-shell title="Live Member Inspector">
    @if(loading()){<section class="card empty">Loading member profile…</section>}
    @if(error()){<section class="card error">{{error()}}</section>}
    @if(data(); as d){
      <section class="hero card">
        <a class="back" [routerLink]="['/guild',guildId,'members']">← Members</a>
        <div class="avatar">@if(d.member.avatar_url){<img [src]="d.member.avatar_url" alt="">}@else{<span>{{initial(d.member.username)}}</span>}</div>
        <div class="identity"><div class="eyebrow">Discord member</div><h2>{{d.member.nickname||d.member.global_name||d.member.username}}</h2><p>@{{d.member.username}} · <code>{{d.member.discord_user_id}}</code></p>
          <div class="badges"><b [class]="'presence '+d.member.presence_status">{{d.member.presence_status}}</b>@if(d.member.bot){<b>BOT</b>}@if(d.member.watchlisted){<b [class]="'risk '+d.member.risk_level">{{d.member.risk_level}} risk</b>}@if(d.member.shieldnet_blocked){<b class="blocked">Blocked</b>}</div>
        </div>
        <button class="refresh" (click)="load()">↻ Refresh</button>
      </section>

      <section class="metrics">
        <article><strong>{{d.summary.open_cases}}</strong><span>Open cases</span></article><article><strong>{{d.summary.resolved_cases}}</strong><span>Resolved</span></article>
        <article><strong>{{d.summary.actions}}</strong><span>Actions</span></article><article><strong>{{d.summary.appeals}}</strong><span>Appeals</span></article>
        <article><strong>{{d.summary.evidence}}</strong><span>Evidence</span></article><article><strong>{{d.summary.verification_requests}}</strong><span>Verifications</span></article>
      </section>

      <section class="grid">
        <article class="card panel"><h3>Live presence</h3>
          <div class="facts"><div><span>Status</span><strong>{{d.member.presence_status}}</strong></div><div><span>Activity</span><strong>{{d.member.activity_name||'None'}}</strong></div><div><span>Activity type</span><strong>{{d.member.activity_type||'—'}}</strong></div><div><span>Voice channel</span><strong>{{d.member.voice_channel_name||'Not connected'}}</strong></div></div>
          <h4>Connected clients</h4><div class="clients"><span [class.on]="d.member.client_desktop">Desktop</span><span [class.on]="d.member.client_mobile">Mobile</span><span [class.on]="d.member.client_web">Web</span></div>
          <small>Presence updated {{d.member.last_presence_at | date:'medium'}}</small>
        </article>
        <article class="card panel"><h3>Account & membership</h3><div class="facts"><div><span>Joined</span><strong>{{d.member.joined_at | date:'medium'}}</strong></div><div><span>Last activity</span><strong>{{d.member.last_activity_at | date:'medium'}}</strong></div><div><span>Timeout until</span><strong>{{d.member.communication_disabled_until ? (d.member.communication_disabled_until|date:'medium') : 'No timeout'}}</strong></div><div><span>State</span><strong>{{d.member.is_active?'Active':'Left server'}}</strong></div></div></article>
        <article class="card panel roles"><h3>Roles</h3>@for(role of d.member.roles; track role.discord_role_id){<div><i [style.background]="roleColor(role.role_color)"></i><span>{{role.role_name}}</span><code>{{role.discord_role_id}}</code></div>}@empty{<p>No synchronized roles.</p>}</article>
        <article class="card panel permissions"><h3>Effective server permissions</h3><div class="permission-list">@for(permission of d.permissions; track permission){<span>{{permission}}</span>}@empty{<p>No elevated synchronized permissions.</p>}</div></article>
        <article class="card panel"><h3>Risk & review</h3><div class="facts"><div><span>Watchlist</span><strong>{{d.member.watchlisted?'Yes':'No'}}</strong></div><div><span>Risk level</span><strong>{{d.member.risk_level}}</strong></div><div><span>Review due</span><strong>{{d.member.review_due_at ? (d.member.review_due_at|date:'medium') : 'Not scheduled'}}</strong></div><div><span>Tags</span><strong>{{d.member.tags.join(', ')||'None'}}</strong></div></div>@if(d.member.review_reason){<p class="note">{{d.member.review_reason}}</p>}@if(d.member.admin_note){<p class="note private">{{d.member.admin_note}}</p>}</article>
      </section>

      <section class="card timeline"><div class="section-title"><div><div class="eyebrow">Unified history</div><h3>Member timeline</h3></div><span>{{d.timeline.length}} events</span></div>
        @for(item of d.timeline; track item.id){<article><div class="dot" [class]="item.kind"></div><div><strong>{{item.title}}</strong><p>{{item.detail||item.kind}}</p><div class="meta"><span>{{item.kind}}</span>@if(item.status){<span>{{item.status}}</span>}@if(item.severity){<span>{{item.severity}}</span>}</div></div><time>{{item.occurred_at|date:'medium'}}</time></article>}@empty{<div class="empty">No timeline events.</div>}
      </section>
    }
  </sn-shell>`,
  styles:[`
    .card{background:rgba(16,22,38,.82);border:1px solid var(--line);border-radius:18px}.hero{display:grid;grid-template-columns:auto auto 1fr auto;gap:1.2rem;align-items:center;padding:1.4rem;position:relative}.back{position:absolute;top:1rem;right:1rem;color:var(--muted)}.avatar{width:88px;height:88px;border-radius:22px;background:var(--primary-soft);display:grid;place-items:center;font-size:2rem;overflow:hidden}.avatar img{width:100%;height:100%;object-fit:cover}.identity h2{margin:.2rem 0}.identity p{color:var(--muted)}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.7rem;color:#8e9bff;font-weight:800}.badges{display:flex;gap:.45rem;flex-wrap:wrap}.badges b,.clients span{font-size:.72rem;padding:.3rem .55rem;border:1px solid var(--line);border-radius:999px}.presence.online,.clients .on{color:#74e9b3;border-color:#327c61}.presence.idle{color:#ffd36e}.presence.dnd,.blocked{color:#ff7b8d}.refresh{align-self:start;margin-top:2.5rem}.metrics{display:grid;grid-template-columns:repeat(6,1fr);gap:.8rem;margin:1rem 0}.metrics article{padding:1rem;background:rgba(16,22,38,.72);border:1px solid var(--line);border-radius:15px}.metrics strong{font-size:1.55rem;display:block}.metrics span,.facts span,small{color:var(--muted);font-size:.78rem}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.panel{padding:1.2rem}.panel h3{margin-top:0}.facts{display:grid;grid-template-columns:repeat(2,1fr);gap:.8rem}.facts div{padding:.8rem;background:rgba(255,255,255,.025);border-radius:12px}.facts strong{display:block;margin-top:.25rem}.clients{display:flex;gap:.5rem}.roles>div{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:.7rem;padding:.55rem;border-bottom:1px solid var(--line)}.roles i{width:.65rem;height:.65rem;border-radius:50%}.permission-list{display:flex;gap:.45rem;flex-wrap:wrap}.permission-list span{padding:.35rem .55rem;border:1px solid var(--line);border-radius:999px;font-size:.75rem}.note{padding:.8rem;border-left:3px solid #8090ff;background:rgba(128,144,255,.06)}.private{border-color:#ffb86b}.timeline{margin-top:1rem;padding:1.2rem}.section-title{display:flex;justify-content:space-between;align-items:center}.timeline article{display:grid;grid-template-columns:auto 1fr auto;gap:.8rem;padding:1rem 0;border-top:1px solid var(--line)}.timeline p{margin:.25rem 0;color:var(--muted)}.timeline time{color:var(--muted);font-size:.78rem}.dot{width:.65rem;height:.65rem;border-radius:50%;background:#8090ff;margin-top:.3rem}.dot.case{background:#ff9a62}.dot.action{background:#74e9b3}.dot.appeal{background:#c08cff}.dot.verification{background:#5fc9ff}.meta{display:flex;gap:.35rem}.meta span{font-size:.68rem;padding:.18rem .4rem;border-radius:999px;background:var(--primary-soft)}.error{padding:1rem;color:#ff8a9a}.empty{padding:2rem;text-align:center;color:var(--muted)}
    @media(max-width:1000px){.metrics{grid-template-columns:repeat(3,1fr)}.grid{grid-template-columns:1fr}}@media(max-width:650px){.hero{grid-template-columns:auto 1fr}.refresh{display:none}.metrics{grid-template-columns:repeat(2,1fr)}.timeline article{grid-template-columns:auto 1fr}.timeline time{grid-column:2}.facts{grid-template-columns:1fr}}
  `]
})
export class MemberInspectorComponent implements OnInit{
  guildId=''; userId=''; readonly data=signal<MemberInspector|null>(null); readonly loading=signal(true); readonly error=signal('');
  constructor(private route:ActivatedRoute,private service:MemberService){}
  ngOnInit(){this.guildId=this.route.snapshot.paramMap.get('guildId') ?? '';this.userId=this.route.snapshot.paramMap.get('userId') ?? '';this.load()}
  async load(){this.loading.set(true);this.error.set('');try{this.data.set(await this.service.inspector(this.guildId,this.userId))}catch{this.error.set('Unable to load member inspector. Confirm that the member is synchronized and the bot is online.')}finally{this.loading.set(false)}}
  initial(v:string){return (v||'?').slice(0,1).toUpperCase()} roleColor(v:number){return v?`#${v.toString(16).padStart(6,'0')}`:'#687080'}
}
