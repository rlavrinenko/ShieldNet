from __future__ import annotations

import ctypes
import os
import resource
from dataclasses import dataclass


PR_SET_NO_NEW_PRIVS = 38


@dataclass(frozen=True)
class SandboxLimits:
    memory_mb: int
    cpu_seconds: int
    open_files: int
    processes: int
    file_size_mb: int

    @classmethod
    def from_env(cls) -> "SandboxLimits":
        return cls(
            memory_mb=int(
                os.getenv("PLUGIN_SANDBOX_MEMORY_MB", "256")
            ),
            cpu_seconds=int(
                os.getenv("PLUGIN_SANDBOX_CPU_SECONDS", "3600")
            ),
            open_files=int(
                os.getenv("PLUGIN_SANDBOX_OPEN_FILES", "128")
            ),
            processes=int(
                os.getenv("PLUGIN_SANDBOX_PROCESSES", "16")
            ),
            file_size_mb=int(
                os.getenv("PLUGIN_SANDBOX_FILE_SIZE_MB", "32")
            ),
        )


def _set_limit(
    limit_name: int,
    soft: int,
    hard: int | None = None,
) -> None:
    if hard is None:
        hard = soft

    resource.setrlimit(
        limit_name,
        (soft, hard),
    )


def apply_sandbox(limits: SandboxLimits) -> None:
    """
    Runs in the child process immediately before exec().
    Do not perform logging or database work here.
    """

    os.umask(0o077)

    memory_bytes = limits.memory_mb * 1024 * 1024
    file_size_bytes = limits.file_size_mb * 1024 * 1024

    _set_limit(
        resource.RLIMIT_AS,
        memory_bytes,
    )

    _set_limit(
        resource.RLIMIT_CPU,
        limits.cpu_seconds,
    )

    _set_limit(
        resource.RLIMIT_NOFILE,
        limits.open_files,
    )

    _set_limit(
        resource.RLIMIT_NPROC,
        limits.processes,
    )

    _set_limit(
        resource.RLIMIT_FSIZE,
        file_size_bytes,
    )

    _set_limit(
        resource.RLIMIT_CORE,
        0,
    )

    libc = ctypes.CDLL(None, use_errno=True)

    result = libc.prctl(
        PR_SET_NO_NEW_PRIVS,
        1,
        0,
        0,
        0,
    )

    if result != 0:
        errno_value = ctypes.get_errno()
        raise OSError(
            errno_value,
            "Unable to enable no_new_privileges",
        )
