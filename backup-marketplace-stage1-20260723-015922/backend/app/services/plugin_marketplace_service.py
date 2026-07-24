from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugins import PluginMarketplaceItem, PluginMarketplaceVersion
from app.schemas.plugin_marketplace import (
    MarketplaceItemCreate,
    MarketplaceItemResponse,
    MarketplaceItemUpdate,
    MarketplacePageResponse,
    MarketplaceVersionCreate,
    MarketplaceVersionResponse,
)


class MarketplaceConflictError(Exception):
    pass


class PluginMarketplaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_items(
        self,
        *,
        query: str | None,
        category: str | None,
        limit: int,
        offset: int,
        include_unpublished: bool = False,
    ) -> MarketplacePageResponse:
        filters = []
        if not include_unpublished:
            filters.append(PluginMarketplaceItem.published.is_(True))
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(
                PluginMarketplaceItem.name.ilike(pattern)
                | PluginMarketplaceItem.plugin_key.ilike(pattern)
            )
        if category:
            filters.append(PluginMarketplaceItem.category == category)

        total_stmt = select(func.count(PluginMarketplaceItem.id)).where(*filters)
        items_stmt = (
            select(PluginMarketplaceItem)
            .where(*filters)
            .order_by(
                PluginMarketplaceItem.verified.desc(),
                PluginMarketplaceItem.downloads.desc(),
                PluginMarketplaceItem.name.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        total = int((await self.session.execute(total_stmt)).scalar_one())
        items = list((await self.session.execute(items_stmt)).scalars().all())
        responses = [await self._item_response(item) for item in items]

        return MarketplacePageResponse(
            items=responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_item(
        self,
        plugin_key: str,
        *,
        include_unpublished: bool = False,
    ) -> MarketplaceItemResponse:
        filters = [PluginMarketplaceItem.plugin_key == plugin_key]
        if not include_unpublished:
            filters.append(PluginMarketplaceItem.published.is_(True))

        item = (
            await self.session.execute(
                select(PluginMarketplaceItem).where(*filters)
            )
        ).scalar_one_or_none()

        if item is None:
            raise LookupError("Marketplace plugin not found")
        return await self._item_response(item)

    async def create_item(
        self,
        payload: MarketplaceItemCreate,
    ) -> MarketplaceItemResponse:
        item = PluginMarketplaceItem(
            plugin_key=payload.plugin_key,
            name=payload.name,
            summary=payload.summary,
            category=payload.category,
            author=payload.author,
            homepage_url=payload.homepage_url,
            repository_url=payload.repository_url,
            icon_url=payload.icon_url,
            metadata_json=payload.metadata_json,
            verified=False,
            published=False,
        )
        self.session.add(item)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise MarketplaceConflictError("plugin_key already exists") from exc

        await self.session.refresh(item)
        return await self._item_response(item)

    async def update_item(
        self,
        plugin_key: str,
        payload: MarketplaceItemUpdate,
    ) -> MarketplaceItemResponse:
        item = await self._get_model(plugin_key)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(item)
        return await self._item_response(item)

    async def delete_item(self, plugin_key: str) -> None:
        item = await self._get_model(plugin_key)
        await self.session.delete(item)
        await self.session.commit()

    async def add_version(
        self,
        plugin_key: str,
        payload: MarketplaceVersionCreate,
    ) -> MarketplaceVersionResponse:
        item = await self._get_model(plugin_key)
        version = PluginMarketplaceVersion(
            marketplace_item_id=item.id,
            version=payload.version,
            min_core_version=payload.min_core_version,
            package_url=payload.package_url,
            checksum_sha256=payload.checksum_sha256,
            signature=payload.signature,
            changelog=payload.changelog,
            manifest=payload.manifest,
        )
        self.session.add(version)
        item.updated_at = datetime.now(timezone.utc)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise MarketplaceConflictError("plugin version already exists") from exc

        await self.session.refresh(version)
        return self._version_response(version)

    async def delete_version(self, plugin_key: str, version_id: UUID) -> None:
        item = await self._get_model(plugin_key)
        version = (
            await self.session.execute(
                select(PluginMarketplaceVersion).where(
                    PluginMarketplaceVersion.id == version_id,
                    PluginMarketplaceVersion.marketplace_item_id == item.id,
                )
            )
        ).scalar_one_or_none()
        if version is None:
            raise LookupError("Marketplace plugin version not found")
        await self.session.delete(version)
        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()

    async def set_published(
        self,
        plugin_key: str,
        published: bool,
    ) -> MarketplaceItemResponse:
        item = await self._get_model(plugin_key)
        if published:
            version_count = int(
                (
                    await self.session.execute(
                        select(func.count(PluginMarketplaceVersion.id)).where(
                            PluginMarketplaceVersion.marketplace_item_id == item.id
                        )
                    )
                ).scalar_one()
            )
            if version_count == 0:
                raise MarketplaceConflictError(
                    "plugin cannot be published without at least one version"
                )
        item.published = published
        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(item)
        return await self._item_response(item)

    async def set_verified(
        self,
        plugin_key: str,
        verified: bool,
    ) -> MarketplaceItemResponse:
        item = await self._get_model(plugin_key)
        item.verified = verified
        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(item)
        return await self._item_response(item)

    async def _get_model(self, plugin_key: str) -> PluginMarketplaceItem:
        item = (
            await self.session.execute(
                select(PluginMarketplaceItem).where(
                    PluginMarketplaceItem.plugin_key == plugin_key
                )
            )
        ).scalar_one_or_none()
        if item is None:
            raise LookupError("Marketplace plugin not found")
        return item

    async def _item_response(
        self,
        item: PluginMarketplaceItem,
    ) -> MarketplaceItemResponse:
        version = (
            await self.session.execute(
                select(PluginMarketplaceVersion)
                .where(PluginMarketplaceVersion.marketplace_item_id == item.id)
                .order_by(PluginMarketplaceVersion.released_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        latest = self._version_response(version) if version is not None else None

        return MarketplaceItemResponse(
            id=str(item.id),
            plugin_key=item.plugin_key,
            name=item.name,
            summary=item.summary,
            category=item.category,
            author=item.author,
            homepage_url=item.homepage_url,
            repository_url=item.repository_url,
            icon_url=item.icon_url,
            verified=item.verified,
            published=item.published,
            downloads=item.downloads,
            metadata_json=item.metadata_json or {},
            latest_version=latest,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _version_response(
        version: PluginMarketplaceVersion,
    ) -> MarketplaceVersionResponse:
        return MarketplaceVersionResponse(
            id=str(version.id),
            version=version.version,
            min_core_version=version.min_core_version,
            package_url=version.package_url,
            checksum_sha256=version.checksum_sha256,
            changelog=version.changelog,
            manifest=version.manifest or {},
            released_at=version.released_at,
        )
