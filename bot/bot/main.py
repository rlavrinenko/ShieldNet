import asyncio
import logging
from bot.client import ShieldNetBot
from bot.config import settings

async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    bot = ShieldNetBot()
    async with bot:
        await bot.start(settings.discord_bot_token)

if __name__ == "__main__":
    asyncio.run(main())
