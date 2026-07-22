from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class WorkerSettings:
    root: Path
    poll_seconds: float
    max_package_bytes: int
    download_timeout_seconds: int
    allowed_permissions: frozenset[str]

    @classmethod
    def from_env(cls) -> "WorkerSettings":
        root = Path(
            os.getenv("SHIELDNET_PLUGIN_ROOT", "/opt/shieldnet/plugins")
        ).resolve()
        permissions = frozenset(
            item.strip()
            for item in os.getenv(
                "SHIELDNET_PLUGIN_ALLOWED_PERMISSIONS",
                "database,scheduler,http_client,settings",
            ).split(",")
            if item.strip()
        )
        return cls(
            root=root,
            poll_seconds=max(
                1.0, float(os.getenv("SHIELDNET_PLUGIN_POLL_SECONDS", "3"))
            ),
            max_package_bytes=max(
                1024 * 1024,
                int(
                    os.getenv(
                        "SHIELDNET_PLUGIN_MAX_PACKAGE_BYTES",
                        str(100 * 1024 * 1024),
                    )
                ),
            ),
            download_timeout_seconds=max(
                5,
                int(
                    os.getenv(
                        "SHIELDNET_PLUGIN_DOWNLOAD_TIMEOUT_SECONDS",
                        "60",
                    )
                ),
            ),
            allowed_permissions=permissions,
        )
