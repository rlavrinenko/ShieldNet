from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import ModuleSetting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_module(self, guild_id: int, module: str) -> Sequence[ModuleSetting]:
        result = await self.session.execute(
            select(ModuleSetting)
            .where(
                ModuleSetting.guild_id == guild_id,
                ModuleSetting.module == module,
            )
            .order_by(ModuleSetting.key.asc())
        )
        return result.scalars().all()

    async def get(self, guild_id: int, module: str, key: str) -> ModuleSetting | None:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.guild_id == guild_id,
                ModuleSetting.module == module,
                ModuleSetting.key == key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        guild_id: int,
        module: str,
        key: str,
        value: object,
        value_type: str,
        updated_by: object | None,
    ) -> ModuleSetting:
        stmt = (
            insert(ModuleSetting)
            .values(
                guild_id=guild_id,
                module=module,
                key=key,
                value=value,
                value_type=value_type,
                updated_by=updated_by,
            )
            .on_conflict_do_update(
                constraint="uq_core_module_settings_scope",
                set_={
                    "value": value,
                    "value_type": value_type,
                    "updated_by": updated_by,
                },
            )
            .returning(ModuleSetting)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def remove(self, guild_id: int, module: str, key: str) -> bool:
        result = await self.session.execute(
            delete(ModuleSetting)
            .where(
                ModuleSetting.guild_id == guild_id,
                ModuleSetting.module == module,
                ModuleSetting.key == key,
            )
            .returning(ModuleSetting.id)
        )
        return result.scalar_one_or_none() is not None
