from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modules import GuildModule, ModuleCatalog
from app.schemas.modules import ModuleResponse


class ModuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_guild(self, guild_id: int) -> list[ModuleResponse]:
        result = await self.session.execute(
            select(ModuleCatalog, GuildModule)
            .outerjoin(
                GuildModule,
                (GuildModule.module_id == ModuleCatalog.id)
                & (GuildModule.guild_id == guild_id),
            )
            .where(ModuleCatalog.is_available.is_(True))
            .order_by(ModuleCatalog.sort_order, ModuleCatalog.name)
        )

        modules: list[ModuleResponse] = []

        for catalog, guild_module in result.all():
            modules.append(
                ModuleResponse(
                    module_key=catalog.module_key,
                    name=catalog.name,
                    description=catalog.description,
                    icon=catalog.icon,
                    version=catalog.version,
                    is_core=catalog.is_core,
                    enabled=(
                        True
                        if catalog.is_core
                        else bool(guild_module and guild_module.enabled)
                    ),
                    configuration=(
                        guild_module.configuration
                        if guild_module
                        else {}
                    ),
                    revision=(
                        guild_module.revision
                        if guild_module
                        else 0
                    ),
                )
            )

        return modules

    async def update(
        self,
        guild_id: int,
        module_key: str,
        enabled: bool,
        configuration: dict | None,
        changed_by,
    ) -> ModuleResponse:
        catalog_result = await self.session.execute(
            select(ModuleCatalog).where(
                ModuleCatalog.module_key == module_key,
                ModuleCatalog.is_available.is_(True),
            )
        )
        catalog = catalog_result.scalar_one_or_none()

        if catalog is None:
            raise LookupError("Module not found")

        effective_enabled = True if catalog.is_core else enabled

        state_result = await self.session.execute(
            select(GuildModule).where(
                GuildModule.guild_id == guild_id,
                GuildModule.module_id == catalog.id,
            )
        )
        state = state_result.scalar_one_or_none()

        if state is None:
            state = GuildModule(
                guild_id=guild_id,
                module_id=catalog.id,
                enabled=effective_enabled,
                configuration=configuration or {},
                changed_by=changed_by,
                revision=1,
            )
            self.session.add(state)
        else:
            state.enabled = effective_enabled
            if configuration is not None:
                state.configuration = configuration
            state.changed_by = changed_by
            state.revision += 1

        await self.session.commit()
        await self.session.refresh(state)

        return ModuleResponse(
            module_key=catalog.module_key,
            name=catalog.name,
            description=catalog.description,
            icon=catalog.icon,
            version=catalog.version,
            is_core=catalog.is_core,
            enabled=effective_enabled,
            configuration=state.configuration,
            revision=state.revision,
        )

    async def configuration_revision(self, guild_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(GuildModule.revision), 0)).where(
                GuildModule.guild_id == guild_id
            )
        )
        return int(result.scalar_one())
