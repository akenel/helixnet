"""Golden-lock local conftest — keeps the CH tripwire PURE (no server / no Keycloak).

The parent tests/pos/conftest.py has an autouse `_ensure_open_drawer` fixture that mints
a real Keycloak token and opens a cash drawer before every test in tests/pos/ — i.e. it
requires a live server. The golden lock is a pure host-.venv test on the VAT engine, so we
override that fixture here with a same-named no-op. Fixture-override-by-name resolves to the
closest conftest, so tests in this directory get the no-op and never touch the network.

Purely additive: this is a NEW file; it changes nothing in tests/pos/conftest.py or src/.
"""
import pytest


@pytest.fixture(autouse=True)
def _ensure_open_drawer():
    """No-op override of the parent's server-requiring autouse fixture."""
    yield
