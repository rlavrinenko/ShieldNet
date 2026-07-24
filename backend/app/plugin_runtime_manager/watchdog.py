from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionFactory, close_database
from app.models.plugins import (
    GuildPluginInstallation,
    PluginRuntimeInstance,
)

logger = logging.getLogger("shieldnet.plugin_runtime.watchdog")


class RuntimeWatchdog:
    def __init__(self) -> None:
        self.poll_seconds = float(
            os.getenv("PLUGIN_WATCHDOG_POLL_SECONDS", "15")
        )
        self.stale_seconds = float(
            os.getenv("PLUGIN_WATCHDOG_STALE_SECONDS", "60")
        )

    async def check(self) -> None:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.stale_seconds)

        async with AsyncSessionFactory() as session:
            runtimes = list(
                (
                    await session.execute(
                        select(PluginRuntimeInstance).where(
                            PluginRuntimeInstance.state == "running",
                            PluginRuntimeInstance.last_heartbeat_at < cutoff,
                        )
                    )
                ).scalars().all()
            )

            for runtime in runtimes:
                installation = (
                    await session.execute(
                        select(GuildPluginInstallation).where(
                            GuildPluginInstallation.guild_id
                            == runtime.guild_id,
                            GuildPluginInstallation.plugin_key
                            == runtime.plugin_key,
                        )
                    )
                ).scalar_one_or_none()

                message = (
                    "Runtime heartbeat is stale: "
                    f"last heartbeat at {runtime.last_heartbeat_at}"
                )

                runtime.last_error = message
                runtime.updated_at = now

                if installation is not None:
                    installation.status = "stale"
                    installation.last_error = message
                    installation.last_health_check_at = now
                    installation.updated_at = now

                logger.warning(
                    "Stale runtime detected plugin_key=%s guild_id=%s",
                    runtime.plugin_key,
                    runtime.guild_id,
                )

            if runtimes:
                await session.commit()

    async def run(self) -> None:
        logger.info(
            "Runtime watchdog started poll=%ss stale=%ss",
            self.poll_seconds,
            self.stale_seconds,
        )

        while True:
            try:
                await self.check()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Runtime watchdog check failed")

            await asyncio.sleep(self.poll_seconds)


async def async_main() -> None:
    watchdog = RuntimeWatchdog()

    try:
        await watchdog.run()
    finally:
        await close_database()


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s %(message)s"
        ),
    )

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
