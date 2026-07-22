import json
import zipfile
from pathlib import Path

import pytest

from app.plugin_worker.security import (
    PackageValidationError,
    load_and_validate_manifest,
    safe_extract_zip,
)


def test_safe_extract_rejects_parent_path(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.txt", "bad")

    with pytest.raises(PackageValidationError):
        safe_extract_zip(
            archive,
            tmp_path / "out",
            max_uncompressed_bytes=1024 * 1024,
        )


def test_manifest_validation(tmp_path: Path) -> None:
    (tmp_path / "plugin.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "plugin_key": "demo",
                "version": "1.0.0",
                "name": "Demo",
                "entrypoint": "plugin.py",
                "permissions": ["database"],
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )

    manifest = load_and_validate_manifest(
        tmp_path,
        expected_plugin_key="demo",
        expected_version="1.0.0",
        allowed_permissions=frozenset({"database"}),
    )
    assert manifest["plugin_key"] == "demo"
