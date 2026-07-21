from fastapi import APIRouter

from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.backups import router as backups_router
from app.api.routes.automations import router as automations_router
from app.api.routes.automation_schedules import router as automation_schedules_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.doctor import router as doctor_router
from app.api.routes.enterprise_dashboard import router as enterprise_dashboard_router
from app.api.routes.explorer import router as explorer_router
from app.api.routes.internal_explorer import router as internal_explorer_router
from app.api.routes.internal_automations import router as internal_automations_router
from app.api.routes.discord_guilds import router as discord_guilds_router
from app.api.routes.guild_registry import router as guild_registry_router
from app.api.routes.guild_roles import router as guild_roles_router
from app.api.routes.health import router as health_router
from app.api.routes.internal_discord import router as internal_discord_router
from app.api.routes.internal_guild_roles import router as internal_guild_roles_router
from app.api.routes.internal_member_actions import router as internal_member_actions_router
from app.api.routes.internal_members import router as internal_members_router
from app.api.routes.internal_modules import router as internal_modules_router
from app.api.routes.internal_permissions import router as internal_permissions_router
from app.api.routes.internal_verification import router as internal_verification_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.member_actions import router as member_actions_router
from app.api.routes.member_cases import router as member_cases_router
from app.api.routes.member_evidence import router as member_evidence_router
from app.api.routes.members import router as members_router
from app.api.routes.member_inspector import router as member_inspector_router
from app.api.routes.modules import router as modules_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.operations import router as operations_router
from app.api.routes.moderation_operations import router as moderation_operations_router
from app.api.routes.permissions import router as permissions_router
from app.api.routes.permission_simulator import router as permission_simulator_router
from app.api.routes.platform_access import router as platform_access_router
from app.api.routes.server_control import router as server_control_router
from app.api.routes.server_diff import router as server_diff_router
from app.api.routes.security import router as security_router
from app.api.routes.internal_security import router as internal_security_router
from app.api.routes.internal_runtime import router as internal_runtime_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.verification import router as verification_router
from app.api.routes.leadership import router as leadership_router
from app.api.routes.internal_leadership import router as internal_leadership_router
from app.api.routes.role_channel_management import router as role_channel_management_router
from app.api.routes.internal_role_channel_management import router as internal_role_channel_management_router
from app.api.routes.setup_wizard import router as setup_wizard_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(backups_router)
api_router.include_router(automations_router)
api_router.include_router(automation_schedules_router)
api_router.include_router(dashboard_router)
api_router.include_router(doctor_router)
api_router.include_router(enterprise_dashboard_router)
api_router.include_router(explorer_router)
api_router.include_router(internal_explorer_router)
api_router.include_router(internal_automations_router)
api_router.include_router(server_control_router)
api_router.include_router(server_diff_router)
api_router.include_router(security_router)
api_router.include_router(internal_security_router)
api_router.include_router(internal_runtime_router)
api_router.include_router(runtime_router)
api_router.include_router(discord_guilds_router)
api_router.include_router(guild_registry_router)
api_router.include_router(internal_discord_router)
api_router.include_router(modules_router)
api_router.include_router(notifications_router)
api_router.include_router(operations_router)
api_router.include_router(internal_modules_router)
api_router.include_router(members_router)
api_router.include_router(member_inspector_router)
api_router.include_router(internal_members_router)
api_router.include_router(member_actions_router)
api_router.include_router(member_cases_router)
api_router.include_router(member_evidence_router)
api_router.include_router(moderation_operations_router)
api_router.include_router(internal_member_actions_router)
api_router.include_router(guild_roles_router)
api_router.include_router(internal_guild_roles_router)
api_router.include_router(audit_router)
api_router.include_router(permissions_router)
api_router.include_router(permission_simulator_router)
api_router.include_router(platform_access_router)
api_router.include_router(jobs_router)
api_router.include_router(internal_permissions_router)
api_router.include_router(verification_router)
api_router.include_router(internal_verification_router)
api_router.include_router(leadership_router)
api_router.include_router(internal_leadership_router)
api_router.include_router(role_channel_management_router)
api_router.include_router(internal_role_channel_management_router)
api_router.include_router(setup_wizard_router)
