from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_globals() -> None:
    """Reset module-level state before each test."""
    from thefuck.cache import reset_state
    reset_state()
    yield


@pytest.fixture
def no_memoize():
    """Disable memoization for test isolation."""
    from thefuck.cache import disable_memoize
    with disable_memoize():
        yield


@pytest.fixture
def command() -> Command:
    """Create a minimal Command object."""
    from thefuck.types import Command
    return Command(script='ls', output='')


@pytest.fixture
def command_with_output() -> Command:
    """Create a Command with error output for match testing."""
    from thefuck.types import Command
    return Command(script='ls foo', output="ls: foo: No such file or directory")


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide a controllable settings object."""
    from thefuck.conf import settings
    settings.init()
    yield settings
