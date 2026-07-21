import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AIGatewayService, AIProvider } from '../core/ai-gateway.service';
import { ShellComponent } from '../shared/shell.component';

@Component({standalone:true,imports:[FormsModule,ShellComponent],template:`
<sn-shell title="AI & Integrations">
  <section class="card intro"><h2>Server AI Gateway</h2><p class="muted">AI is disabled globally. This server uses only provider keys configured here.</p></section>
  @if(error()){<section class="card error">{{error()}}</section>}
  <section class="grid">
    <form class="card form" (ngSubmit)="create()">
      <h3>Add provider</h3>
      <label>Name<input [(ngModel)]="form.name" name="name" required></label>
      <label>Provider<select [(ngModel)]="form.provider_type" name="provider_type"><option value="openai">OpenAI</option><option value="xai">xAI Grok</option><option value="gemini">Google Gemini</option><option value="google_translate">Google Translate</option><option value="deepl">DeepL</option><option value="groq">Groq</option><option value="anthropic">Anthropic</option><option value="libretranslate">LibreTranslate</option><option value="openai_compatible">OpenAI-compatible</option></select></label>
      <label>API key<input [(ngModel)]="form.api_key" name="api_key" type="password" required autocomplete="new-password"></label>
      <label>API base URL<input [(ngModel)]="form.api_base_url" name="api_base_url" placeholder="Optional"></label>
      <label>Default model<input [(ngModel)]="form.default_model" name="default_model"></label>
      <button class="btn" [disabled]="saving()">{{saving()?'Saving…':'Save provider'}}</button>
    </form>
    <section class="providers">
      @if(loading()){<article class="card">Loading…</article>}
      @for(p of providers();track p.id){<article class="card provider"><div><h3>{{p.name}}</h3><div class="muted">{{p.provider_type}} · {{p.key_hint || 'Key stored'}}</div><div class="status">Status: {{p.last_health_status || 'not tested'}} @if(p.last_health_latency_ms){· {{p.last_health_latency_ms}} ms}</div>@if(p.last_error){<div class="error-text">{{p.last_error}}</div>}</div><div class="actions"><button class="btn secondary" (click)="test(p)">Test</button><button class="btn danger" (click)="remove(p)">Delete</button></div></article>} @empty { @if(!loading()){<article class="card muted">No providers configured.</article>} }
    </section>
  </section>
</sn-shell>`,styles:[`.intro{padding:1rem;margin-bottom:1rem}.grid{display:grid;grid-template-columns:minmax(280px,380px) 1fr;gap:1rem}.form,.provider{padding:1rem}.form{display:grid;gap:.8rem}.form label{display:grid;gap:.35rem}.form input,.form select{width:100%;padding:.7rem;border-radius:9px;border:1px solid var(--line);background:var(--panel-2);color:var(--text)}.providers{display:grid;gap:1rem;align-content:start}.provider{display:flex;justify-content:space-between;gap:1rem}.actions{display:flex;gap:.5rem;align-items:flex-start}.danger{background:rgba(255,90,110,.15);color:#ff9daa}.error,.error-text{color:#ffd9de}.status{margin-top:.5rem}@media(max-width:850px){.grid{grid-template-columns:1fr}.provider{flex-direction:column}}` ]})
export class AIIntegrationsComponent implements OnInit { readonly guildId=this.route.snapshot.paramMap.get('guildId')??''; readonly providers=signal<AIProvider[]>([]); readonly loading=signal(false); readonly saving=signal(false); readonly error=signal(''); form:any={name:'',provider_type:'openai',api_key:'',api_base_url:'',default_model:''}; constructor(private route:ActivatedRoute,private service:AIGatewayService){} async ngOnInit(){await this.load()} async load(){this.loading.set(true);this.error.set('');try{this.providers.set(await this.service.list(this.guildId))}catch{this.error.set('Unable to load AI providers.')}finally{this.loading.set(false)}} async create(){this.saving.set(true);this.error.set('');try{await this.service.create(this.guildId,{...this.form,api_base_url:this.form.api_base_url||null,default_model:this.form.default_model||null});this.form={name:'',provider_type:'openai',api_key:'',api_base_url:'',default_model:''};await this.load()}catch(e:any){this.error.set(e?.error?.detail||'Unable to save provider.')}finally{this.saving.set(false)}} async test(p:AIProvider){try{await this.service.test(this.guildId,p.id);await this.load()}catch{this.error.set('Connection test failed.')}} async remove(p:AIProvider){if(!confirm(`Delete ${p.name}?`))return;await this.service.remove(this.guildId,p.id);await this.load()}}
