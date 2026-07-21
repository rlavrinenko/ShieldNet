from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugins import PluginMarketplaceItem, PluginMarketplaceVersion
from app.schemas.plugin_marketplace import (
    MarketplaceItemResponse,
    MarketplacePageResponse,
    MarketplaceVersionResponse,
)


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
    ) -> MarketplacePageResponse:
        filters = [PluginMarketplaceItem.published.is_(True)]
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

    async def get_item(self, plugin_key: str) -> MarketplaceItemResponse:
        stmt = select(PluginMarketplaceItem).where(
            PluginMarketplaceItem.plugin_key == plugin_key,
            PluginMarketplaceItem.published.is_(True),
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if item is None:
            raise LookupError("Marketplace plugin not found")
        return await self._item_response(item)

    async def _item_response(
        self,
        item: PluginMarketplaceItem,
    ) -> MarketplaceItemResponse:
        version_stmt = (
            select(PluginMarketplaceVersion)
            .where(PluginMarketplaceVersion.marketplace_item_id == item.id)
            .order_by(PluginMarketplaceVersion.released_at.desc())
            .limit(1)
        )
        version = (await self.session.execute(version_stmt)).scalar_one_or_none()

        latest = None
        if version is not None:
            latest = MarketplaceVersionResponse(
                id=str(version.id),
                version=version.version,
                min_core_version=version.min_core_version,
                package_url=version.package_url,
                checksum_sha256=version.checksum_sha256,
                changelog=version.changelog,
                manifest=version.manifest or {},
                released_at=version.released_at,
            )

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
