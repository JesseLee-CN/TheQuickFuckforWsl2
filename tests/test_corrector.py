from __future__ import annotations

from thefuck.types import Command, Rule, CorrectedCommand
from thefuck.corrector import organize_commands, get_rules_import_paths


class TestOrganizeCommands:
    def test_single_command(self) -> None:
        results = iter([CorrectedCommand('ls', None, 100)])
        organized = list(organize_commands(results))
        assert len(organized) == 1
        assert organized[0].script == 'ls'

    def test_deduplicates(self) -> None:
        a = CorrectedCommand('ls', None, 100)
        b = CorrectedCommand('ls', None, 200)  # same script, different priority
        c = CorrectedCommand('sudo ls', None, 300)
        results = iter([a, b, c])
        organized = list(organize_commands(results))
        # b should be deduplicated since it equals a
        assert len(organized) <= 2

    def test_sorts_by_priority(self) -> None:
        a = CorrectedCommand('a', None, 300)
        b = CorrectedCommand('b', None, 100)
        c = CorrectedCommand('c', None, 200)
        results = iter([a, b, c])
        organized = list(organize_commands(results))
        assert organized[0].script == 'a'  # first yielded kept as-is
        remaining = organized[1:]
        priorities = [cmd.priority for cmd in remaining]
        assert priorities == sorted(priorities)

    def test_empty_commands(self) -> None:
        results = iter([])
        organized = list(organize_commands(results))
        assert organized == []


class TestGetRulesImportPaths:
    def test_yields_bundled_rules(self) -> None:
        from thefuck.conf import settings
        settings.init()
        paths = list(get_rules_import_paths())
        assert len(paths) >= 1  # at least the bundled rules path
