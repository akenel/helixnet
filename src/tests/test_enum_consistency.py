# File: src/tests/test_enum_consistency.py
"""
Enum Consistency Tests -- the seal inspection for enums.

"If one seal fails, check all the seals."

This test dynamically discovers EVERY enum class in src/db/models/
and src/schemas/, then verifies:
1. All inherit from HelixEnum (not bare str+Enum)
2. All values are lowercase (DB/API standard)
3. Case-insensitive lookup works on every member
4. No duplicate values within any single enum
5. All enum classes can be instantiated from their own values

If this test breaks, something slipped through the migration.
"""
import importlib
import inspect
import pkgutil
from enum import Enum

import pytest

from src.core.constants import HelixEnum


# -------------------------------------------------------------------
# Discovery: find all enum classes in models and schemas
# -------------------------------------------------------------------
def _discover_enum_classes(*package_paths):
    """Walk packages, import every module, collect enum subclasses."""
    found = []
    for pkg_path in package_paths:
        package = importlib.import_module(pkg_path)
        prefix = package.__name__ + "."
        for importer, modname, ispkg in pkgutil.walk_packages(
            package.__path__, prefix=prefix
        ):
            try:
                module = importlib.import_module(modname)
            except Exception:
                continue
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Must be an Enum, defined in THIS module (not imported)
                if (
                    issubclass(obj, Enum)
                    and obj is not Enum
                    and obj is not HelixEnum
                    and obj.__module__ == module.__name__
                ):
                    found.append(obj)
    return found


# Discover at import time so parametrize works
MODEL_ENUMS = _discover_enum_classes("src.db.models")
SCHEMA_ENUMS = _discover_enum_classes("src.schemas")
ALL_ENUMS = MODEL_ENUMS + SCHEMA_ENUMS

# Also grab enums from constants.py itself (UserRoles, UserScopes, etc.)
import src.core.constants as _constants_mod
CONSTANTS_ENUMS = [
    obj for name, obj in inspect.getmembers(_constants_mod, inspect.isclass)
    if issubclass(obj, Enum) and obj is not Enum and obj is not HelixEnum
    and obj.__module__ == _constants_mod.__name__
]
ALL_ENUMS = ALL_ENUMS + CONSTANTS_ENUMS

# Remove duplicates (same class imported in multiple places)
ALL_ENUMS = list({id(e): e for e in ALL_ENUMS}.values())


def _enum_id(enum_cls):
    """Readable test ID: 'ModuleName.ClassName'."""
    short_mod = enum_cls.__module__.rsplit(".", 1)[-1]
    return f"{short_mod}.{enum_cls.__name__}"


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------
class TestEnumDiscovery:
    """Sanity check: make sure discovery actually finds enums."""

    def test_found_model_enums(self):
        assert len(MODEL_ENUMS) > 50, (
            f"Expected 50+ model enums, found {len(MODEL_ENUMS)}. "
            "Did a model file fail to import?"
        )

    def test_found_schema_enums(self):
        assert len(SCHEMA_ENUMS) > 50, (
            f"Expected 50+ schema enums, found {len(SCHEMA_ENUMS)}. "
            "Did a schema file fail to import?"
        )

    def test_found_total(self):
        assert len(ALL_ENUMS) > 100, (
            f"Expected 100+ total enums, found {len(ALL_ENUMS)}."
        )


@pytest.mark.parametrize("enum_cls", ALL_ENUMS, ids=_enum_id)
class TestHelixEnumInheritance:
    """Every enum MUST inherit from HelixEnum."""

    def test_inherits_helix_enum(self, enum_cls):
        assert issubclass(enum_cls, HelixEnum), (
            f"{enum_cls.__module__}.{enum_cls.__name__} inherits from "
            f"{[b.__name__ for b in enum_cls.__mro__]} -- "
            f"should inherit from HelixEnum"
        )


@pytest.mark.parametrize("enum_cls", ALL_ENUMS, ids=_enum_id)
class TestEnumValues:
    """Enum values must follow HelixNet conventions."""

    def test_values_are_lowercase(self, enum_cls):
        """All enum .value strings must be lowercase."""
        for member in enum_cls:
            if isinstance(member.value, str):
                assert member.value == member.value.lower(), (
                    f"{enum_cls.__name__}.{member.name}.value = "
                    f"'{member.value}' is not lowercase"
                )

    def test_no_duplicate_values(self, enum_cls):
        """No two members should share the same value."""
        values = [m.value for m in enum_cls]
        seen = {}
        for member in enum_cls:
            if member.value in seen:
                pytest.fail(
                    f"{enum_cls.__name__}: duplicate value '{member.value}' "
                    f"in {seen[member.value]} and {member.name}"
                )
            seen[member.value] = member.name

    def test_roundtrip_from_value(self, enum_cls):
        """Every member must be instantiable from its own .value."""
        for member in enum_cls:
            reconstructed = enum_cls(member.value)
            assert reconstructed is member, (
                f"{enum_cls.__name__}('{member.value}') returned "
                f"{reconstructed}, expected {member}"
            )


@pytest.mark.parametrize("enum_cls", ALL_ENUMS, ids=_enum_id)
class TestCaseInsensitivity:
    """HelixEnum._missing_ must handle any case variant."""

    def test_uppercase_lookup(self, enum_cls):
        for member in enum_cls:
            if isinstance(member.value, str):
                result = enum_cls(member.value.upper())
                assert result is member

    def test_title_case_lookup(self, enum_cls):
        for member in enum_cls:
            if isinstance(member.value, str):
                result = enum_cls(member.value.title())
                assert result is member

    def test_mixed_case_lookup(self, enum_cls):
        """Alternating case: 'oPeN' etc."""
        for member in enum_cls:
            if isinstance(member.value, str):
                mixed = "".join(
                    c.upper() if i % 2 else c.lower()
                    for i, c in enumerate(member.value)
                )
                result = enum_cls(mixed)
                assert result is member
