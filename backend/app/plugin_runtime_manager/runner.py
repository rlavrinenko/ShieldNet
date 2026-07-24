from __future__ import annotations

import argparse
import asyncio
import importlib.util
import inspect
import logging
import signal
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

logger = logging.getLogger("shieldnet.plugin_runtime.runner")


async def call_lifecycle(
    module: ModuleType,
    names: tuple[str, ...],
    context: dict[str, Any],
) -> Any:
    for name in names:
        callback = getattr(module, name, None)

        if callback is None:
            continue

        logger.info("Calling plugin lifecycle callback: %s", name)
        result = callback(context)

        if inspect.isawaitable(result):
            result = await result

        return result

    return None


def load_plugin(
    package_path: Path,
    entrypoint: str,
    plugin_key: str,
    guild_id: int,
) -> ModuleType:
    package_root = package_path.resolve()
    entrypoint_path = (package_root / entrypoint).resolve()

    if package_root not in entrypoint_path.parents:
        raise RuntimeError("Plugin entrypoint escapes package directory")

    if not entrypoint_path.is_file():
        raise RuntimeError(
            f"Plugin entrypoint does not exist: {entrypoint_path}"
        )

    if entrypoint_path.suffix != ".py":
        raise RuntimeError("Only Python plugin entrypoints are supported")

    module_name = (
        f"shieldnet_runtime_"
        f"{plugin_key.replace('-', '_')}_{guild_id}"
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        entrypoint_path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to create plugin module specification")

    module = importlib.util.module_from_spec(spec)

    sys.path.insert(0, str(package_root))

    try:
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(package_root))
        except ValueError:
            pass

    return module


async def run_plugin(args: argparse.Namespace) -> None:
    package_path = Path(args.package_path).resolve()

    context: dict[str, Any] = {
        "guild_id": args.guild_id,
        "plugin_key": args.plugin_key,
        "package_path": str(package_path),
        "entrypoint": args.entrypoint,
    }

    logger.info(
        "Loading plugin plugin_key=%s guild_id=%s package=%s",
        args.plugin_key,
        args.guild_id,
        package_path,
    )

    module = load_plugin(
        package_path,
        args.entrypoint,
        args.plugin_key,
        args.guild_id,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_stop() -> None:
        logger.info(
            "Plugin stop requested plugin_key=%s guild_id=%s",
            args.plugin_key,
            args.guild_id,
        )
        stop_event.set()

    for signal_name in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(signal_name, request_stop)
        except NotImplementedError:
            pass

    await call_lifecycle(
        module,
        ("setup", "on_load"),
        context,
    )

    await call_lifecycle(
        module,
        ("start", "on_start"),
        context,
    )

    logger.info(
        "Plugin is running plugin_key=%s guild_id=%s",
        args.plugin_key,
        args.guild_id,
    )

    await stop_event.wait()

    try:
        await call_lifecycle(
            module,
            ("stop", "on_stop", "shutdown"),
            context,
        )
    finally:
        logger.info(
            "Plugin stopped plugin_key=%s guild_id=%s",
            args.plugin_key,
            args.guild_id,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ShieldNet plugin process runner",
    )

    parser.add_argument("--guild-id", type=int, required=True)
    parser.add_argument("--plugin-key", required=True)
    parser.add_argument("--package-path", required=True)
    parser.add_argument("--entrypoint", required=True)

    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s %(message)s"
        ),
    )

    args = parse_args()

    try:
        asyncio.run(run_plugin(args))
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception(
            "Plugin runner failed plugin_key=%s guild_id=%s",
            args.plugin_key,
            args.guild_id,
        )
        raise


if __name__ == "__main__":
    main()
