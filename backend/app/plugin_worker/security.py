import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


class PackageValidationError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive_member(name: str) -> PurePosixPath:
    normalized = PurePosixPath(name.replace("\\", "/"))
    if normalized.is_absolute():
        raise PackageValidationError(f"absolute archive path is forbidden: {name}")
    if not normalized.parts or any(part in {"", ".", ".."} for part in normalized.parts):
        raise PackageValidationError(f"unsafe archive path: {name}")
    if normalized.parts[0].endswith(":"):
        raise PackageValidationError(f"drive-prefixed archive path is forbidden: {name}")
    return normalized


def safe_extract_zip(
    archive_path: Path,
    destination: Path,
    *,
    max_uncompressed_bytes: int,
    max_members: int = 5000,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()
    total = 0

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > max_members:
            raise PackageValidationError("archive contains too many entries")

        for info in members:
            relative = validate_archive_member(info.filename)
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(unix_mode):
                raise PackageValidationError(
                    f"symbolic links are forbidden in plugin packages: {info.filename}"
                )

            total += info.file_size
            if total > max_uncompressed_bytes:
                raise PackageValidationError(
                    "archive exceeds maximum uncompressed size"
                )

            target = (destination / Path(*relative.parts)).resolve()
            if os.path.commonpath([destination_resolved, target]) != str(
                destination_resolved
            ):
                raise PackageValidationError(
                    f"archive path escapes destination: {info.filename}"
                )

        archive.extractall(destination)


def load_and_validate_manifest(
    extracted_root: Path,
    *,
    expected_plugin_key: str,
    expected_version: str | None,
    allowed_permissions: frozenset[str],
) -> dict[str, Any]:
    manifest_path = extracted_root / "manifest.json"
    if not manifest_path.is_file():
        raise PackageValidationError("manifest.json is missing")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackageValidationError("manifest.json is not valid UTF-8 JSON") from exc

    if not isinstance(manifest, dict):
        raise PackageValidationError("manifest root must be an object")

    required = {"plugin_key", "version", "name", "entrypoint", "permissions"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise PackageValidationError(
            f"manifest is missing required keys: {', '.join(missing)}"
        )

    if manifest["plugin_key"] != expected_plugin_key:
        raise PackageValidationError("manifest plugin_key does not match the job")
    if expected_version and manifest["version"] != expected_version:
        raise PackageValidationError("manifest version does not match requested version")

    entrypoint = validate_archive_member(str(manifest["entrypoint"]))
    entrypoint_path = (extracted_root / Path(*entrypoint.parts)).resolve()
    if not entrypoint_path.is_file():
        raise PackageValidationError("manifest entrypoint does not exist")
    if entrypoint_path.suffix != ".py":
        raise PackageValidationError("only Python entrypoints are accepted")

    permissions = manifest["permissions"]
    if not isinstance(permissions, list) or any(
        not isinstance(item, str) for item in permissions
    ):
        raise PackageValidationError("manifest permissions must be a string list")

    denied = sorted(set(permissions) - set(allowed_permissions))
    if denied:
        raise PackageValidationError(
            f"manifest requests unsupported permissions: {', '.join(denied)}"
        )

    dependencies = manifest.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise PackageValidationError("manifest dependencies must be a list")

    return manifest
