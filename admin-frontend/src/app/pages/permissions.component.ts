import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { PermissionRule, PermissionService } from '../core/permission.service';
import { GuildRoleService } from '../core/guild-role.service';
import { ShellComponent } from '../shared/shell.component';

@Component({
  standalone: true,
  imports: [FormsModule, ShellComponent],
  template: `
    <sn-shell title="Permissions">
      <div class="card heading">
        <div>
          <h2>Permissions Engine</h2>
          <p class="muted">Module access rules for ShieldNet and Discord roles.</p>
        </div>
        <button class="btn" (click)="dialog.set(true)">Add rule</button>
      </div>

      <div class="rules">
        @for (rule of rules(); track rule.id) {
          <article class="card rule">
            <div>
              <strong>{{ rule.module_key }} · {{ rule.permission }}</strong>
              <div class="muted">
                {{ rule.effect }} · {{ label(rule) }} · priority {{ rule.priority }}
              </div>
            </div>
            <button class="danger" (click)="remove(rule)">Delete</button>
          </article>
        }
      </div>

      @if (dialog()) {
        <div class="overlay" (click)="dialog.set(false)">
          <section class="dialog card" (click)="$event.stopPropagation()">
            <h3>New permission rule</h3>

            <label>Module
              <select [(ngModel)]="moduleKey">
                <option value="*">All modules</option>
                <option value="core">Core</option>
                <option value="verification">Verification</option>
                <option value="translator">Translator</option>
                <option value="moderation">Moderation</option>
                <option value="welcome">Welcome</option>
                <option value="tickets">Tickets</option>
              </select>
            </label>

            <label>Permission
              <select [(ngModel)]="permission">
                <option value="view">View</option>
                <option value="manage">Manage</option>
                <option value="execute">Execute</option>
                <option value="configure">Configure</option>
              </select>
            </label>

            <label>Effect
              <select [(ngModel)]="effect">
                <option value="allow">Allow</option>
                <option value="deny">Deny</option>
              </select>
            </label>

            <label>Subject
              <select [(ngModel)]="subjectType" (ngModelChange)="subjectChanged()">
                <option value="shieldnet_role">ShieldNet role</option>
                <option value="discord_role">Discord role</option>
                <option value="discord_user">Discord user ID</option>
                <option value="everyone">Everyone</option>
              </select>
            </label>

            @if (subjectType === 'shieldnet_role') {
              <label>ShieldNet role
                <select [(ngModel)]="subjectValue">
                  <option value="moderator">Moderator</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
            }

            @if (subjectType === 'discord_role') {
              <label>Discord role
                <select [(ngModel)]="subjectValue">
                  <option value="">Select role</option>
                  @for (role of discordRoles(); track role.discord_role_id) {
                    <option [value]="role.discord_role_id">{{ role.name }}</option>
                  }
                </select>
              </label>
            }

            @if (subjectType === 'discord_user') {
              <label>Discord user ID
                <input [(ngModel)]="subjectValue">
              </label>
            }

            <label>Priority
              <input type="number" [(ngModel)]="priority">
            </label>

            <footer>
              <button class="btn secondary" (click)="dialog.set(false)">Close</button>
              <button class="btn" (click)="save()">Save</button>
            </footer>
          </section>
        </div>
      }
    </sn-shell>
  `,
  styles: [`
    .heading,.rule{padding:1rem;display:flex;justify-content:space-between;gap:1rem}
    .rules{margin-top:1rem;display:grid;gap:.7rem}
    .danger{color:#ffd9de;background:var(--panel-2);border:1px solid rgba(255,107,125,.35);border-radius:8px;padding:.4rem .65rem}
    .overlay{position:fixed;inset:0;display:grid;place-items:center;background:rgba(0,0,0,.7);padding:1rem;z-index:1000}
    .dialog{width:min(560px,100%);padding:1.2rem;display:grid;gap:.8rem}
    label{display:grid;gap:.35rem;color:var(--muted)}
    select,input{padding:.8rem;color:var(--text);background:var(--panel-2);border:1px solid var(--line);border-radius:10px}
    footer{display:flex;justify-content:flex-end;gap:.6rem}
  `],
})
export class PermissionsComponent implements OnInit {
  readonly guildId = this.route.snapshot.paramMap.get('guildId') ?? '';
  readonly rules = signal<PermissionRule[]>([]);
  readonly discordRoles = signal<any[]>([]);
  readonly dialog = signal(false);

  moduleKey = '*';
  permission = 'view';
  effect = 'allow';
  subjectType = 'shieldnet_role';
  subjectValue = 'moderator';
  priority = 100;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly permissions: PermissionService,
    private readonly guildRoles: GuildRoleService,
  ) {}

  async ngOnInit(): Promise<void> {
    this.rules.set(await this.permissions.list(this.guildId));
    this.discordRoles.set(await this.guildRoles.list(this.guildId));
  }

  subjectChanged(): void {
    this.subjectValue =
      this.subjectType === 'everyone'
        ? '*'
        : this.subjectType === 'shieldnet_role'
          ? 'moderator'
          : '';
  }

  label(rule: PermissionRule): string {
    if (rule.subject_type !== 'discord_role') {
      return `${rule.subject_type}: ${rule.subject_value}`;
    }
    const role = this.discordRoles().find(
      item => String(item.discord_role_id) === rule.subject_value,
    );
    return `discord_role: ${role?.name || rule.subject_value}`;
  }

  async save(): Promise<void> {
    await this.permissions.save(
      this.guildId,
      this.moduleKey,
      this.permission,
      {
        effect: this.effect,
        subject_type: this.subjectType,
        subject_value: this.subjectValue,
        enabled: true,
        priority: Number(this.priority),
      },
    );
    this.rules.set(await this.permissions.list(this.guildId));
    this.dialog.set(false);
  }

  async remove(rule: PermissionRule): Promise<void> {
    if (!confirm('Delete this permission rule?')) return;
    await this.permissions.remove(this.guildId, rule.id);
    this.rules.set(await this.permissions.list(this.guildId));
  }
}
