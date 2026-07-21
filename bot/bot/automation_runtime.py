from __future__ import annotations

import logging
from typing import Any

import discord
import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


class AutomationRuntimeClient:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.base_url = settings.backend_url.rstrip('/')
        self.headers = {'X-ShieldNet-Service-Token': settings.internal_service_token}

    async def emit(self, guild: discord.Guild, event_type: str, event_id: str, context: dict[str, Any]) -> None:
        payload = {'guild_id': guild.id, 'event_type': event_type, 'event_id': event_id, 'context': context}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f'{self.base_url}/api/v1/internal/automations/events', headers=self.headers, json=payload)
        response.raise_for_status()
        for job in response.json().get('jobs', []):
            await self.execute(guild, job)

    async def execute(self, guild: discord.Guild, job: dict[str, Any]) -> None:
        run_id = str(job['run_id'])
        context = job.get('context') or {}
        outcomes: list[dict[str, Any]] = []
        overall = 'succeeded'
        error_text: str | None = None
        for index, action in enumerate(job.get('actions') or [], start=1):
            try:
                result = await self._action(guild, action, context)
                outcomes.append({'step': index, 'type': action.get('type'), 'status': 'succeeded', 'result': result})
            except Exception as exc:
                logger.exception('Automation action failed: run=%s step=%s', run_id, index)
                outcomes.append({'step': index, 'type': action.get('type'), 'status': 'failed', 'error': str(exc)})
                overall = 'failed' if not outcomes[:-1] else 'partial'
                error_text = str(exc)
                if job.get('stop_on_error', True):
                    break
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f'{self.base_url}/api/v1/internal/automations/runs/{run_id}/complete',
                headers=self.headers,
                json={'status': overall, 'result': {'actions': outcomes}, 'error': error_text},
            )
        response.raise_for_status()

    async def _action(self, guild: discord.Guild, action: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        kind = str(action.get('type') or '')
        p = action.get('parameters') or {}
        member_id = int(p.get('member_id') or context.get('member', {}).get('id') or 0)
        member = guild.get_member(member_id) if member_id else None
        if kind == 'member.add_role':
            role = guild.get_role(int(p['role_id']))
            if member is None or role is None: raise ValueError('Member or role not found')
            await member.add_roles(role, reason='ShieldNet automation')
            return {'member_id': member.id, 'role_id': role.id}
        if kind == 'member.remove_role':
            role = guild.get_role(int(p['role_id']))
            if member is None or role is None: raise ValueError('Member or role not found')
            await member.remove_roles(role, reason='ShieldNet automation')
            return {'member_id': member.id, 'role_id': role.id}
        if kind == 'member.send_dm':
            if member is None: raise ValueError('Member not found')
            await member.send(str(p.get('message') or ''))
            return {'member_id': member.id}
        if kind == 'member.set_nickname':
            if member is None: raise ValueError('Member not found')
            await member.edit(nick=str(p.get('nickname') or '') or None, reason='ShieldNet automation')
            return {'member_id': member.id, 'nickname': p.get('nickname')}
        if kind == 'channel.send_message':
            channel = guild.get_channel(int(p['channel_id']))
            if channel is None or not hasattr(channel, 'send'): raise ValueError('Text channel not found')
            msg = await channel.send(str(p.get('message') or ''))
            return {'channel_id': channel.id, 'message_id': msg.id}
        if kind == 'webhook.call':
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(str(p['url']), json=p.get('payload') or context)
                r.raise_for_status()
            return {'status_code': r.status_code}
        if kind == 'audit.write':
            logger.info('Automation audit event: guild=%s payload=%s', guild.id, p)
            return {'logged': True}
        raise ValueError(f'Unsupported action type: {kind}')
