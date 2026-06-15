from __future__ import annotations

import os
from thefuck.conf import Settings
from thefuck import const


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings(const.DEFAULT_SETTINGS)
        assert s['require_confirmation'] is True
        assert s['debug'] is False
        assert s['wait_command'] == 3
        assert s['no_colors'] is False

    def test_attribute_access(self) -> None:
        s = Settings(const.DEFAULT_SETTINGS)
        assert s.require_confirmation is True
        assert s.debug is False

    def test_attribute_set(self) -> None:
        s = Settings(const.DEFAULT_SETTINGS)
        s.debug = True
        assert s.debug is True
        assert s['debug'] is True

    def test_missing_key_returns_none(self) -> None:
        s = Settings({})
        assert s.nonexistent is None

    def test_rules_from_env(self, monkeypatch) -> None:
        s = Settings({})
        val = 'git_push:sudo:ls_all'
        result = s._rules_from_env(val)
        assert 'git_push' in result
        assert 'sudo' in result
        assert 'ls_all' in result

    def test_rules_from_env_default(self, monkeypatch) -> None:
        s = Settings({})
        val = 'DEFAULT_RULES:git_push'
        result = s._rules_from_env(val)
        assert const.ALL_ENABLED in result
        assert 'git_push' in result

    def test_priority_from_env(self) -> None:
        s = Settings({})
        result = dict(s._priority_from_env('sudo=100:git_push=200'))
        assert result == {'sudo': 100, 'git_push': 200}

    def test_priority_from_env_skips_invalid(self) -> None:
        s = Settings({})
        result = dict(s._priority_from_env('sudo=100:invalid'))
        assert result == {'sudo': 100}

    def test_val_from_env_bool(self, monkeypatch) -> None:
        s = Settings({})
        monkeypatch.setenv('THEFUCK_DEBUG', 'true')
        result = s._val_from_env('THEFUCK_DEBUG', 'debug')
        assert result is True

    def test_val_from_env_int(self, monkeypatch) -> None:
        s = Settings({})
        monkeypatch.setenv('THEFUCK_WAIT_COMMAND', '10')
        result = s._val_from_env('THEFUCK_WAIT_COMMAND', 'wait_command')
        assert result == 10

    def test_val_from_env_list(self, monkeypatch) -> None:
        s = Settings({})
        monkeypatch.setenv('THEFUCK_SLOW_COMMANDS', 'lein:gradle')
        result = s._val_from_env('THEFUCK_SLOW_COMMANDS', 'slow_commands')
        assert result == ['lein', 'gradle']

    def test_settings_from_env(self, monkeypatch) -> None:
        s = Settings(const.DEFAULT_SETTINGS)
        monkeypatch.setenv('THEFUCK_DEBUG', 'true')
        monkeypatch.setenv('THEFUCK_WAIT_COMMAND', '5')
        result = s._settings_from_env()
        assert result.get('debug') is True
        assert result.get('wait_command') == 5

    def test_settings_from_args(self) -> None:
        s = Settings({})
        args = type('Args', (), {'yes': True, 'debug': True, 'repeat': False})()
        result = s._settings_from_args(args)
        assert result.get('require_confirmation') is False  # --yes
        assert result.get('debug') is True
        assert 'repeat' not in result  # not set when False

    def test_settings_from_args_none(self) -> None:
        s = Settings({})
        result = s._settings_from_args(None)
        assert result == {}
