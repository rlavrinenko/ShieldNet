import pytest

from app.services.settings import InvalidSettingName, SettingsService


def test_detect_type() -> None:
    assert SettingsService.detect_type(True) == "bool"
    assert SettingsService.detect_type(1) == "int"
    assert SettingsService.detect_type("en") == "string"
    assert SettingsService.detect_type(["en", "uk"]) == "list"
    assert SettingsService.detect_type({"enabled": True}) == "object"


def test_validate_name() -> None:
    assert SettingsService.validate_name("Translator.Default", max_length=64) == "translator.default"
    with pytest.raises(InvalidSettingName):
        SettingsService.validate_name("../secret", max_length=64)
