from __future__ import annotations

from thefuck.types import Command, Rule, CorrectedCommand


class TestCommand:
    def test_creation(self) -> None:
        cmd = Command('ls -la', 'total 0')
        assert cmd.script == 'ls -la'
        assert cmd.output == 'total 0'

    def test_equality(self) -> None:
        a = Command('ls', '')
        b = Command('ls', '')
        c = Command('ls', 'error')
        assert a == b
        assert a != c
        assert a != 'not a command'

    def test_update(self) -> None:
        cmd = Command('ls', 'error')
        updated = cmd.update(script='ls -la')
        assert updated.script == 'ls -la'
        assert updated.output == 'error'
        assert cmd.script == 'ls'  # original unchanged

    def test_repr(self) -> None:
        cmd = Command('ls', 'out')
        assert 'Command' in repr(cmd)
        assert 'ls' in repr(cmd)
        assert 'out' in repr(cmd)

    def test_script_parts(self) -> None:
        cmd = Command('git push origin master', '')
        parts = cmd.script_parts
        assert 'git' in parts
        assert 'push' in parts

    def test_update_partial(self) -> None:
        cmd = Command('ls', 'error')
        updated = cmd.update(output='')
        assert updated.script == 'ls'
        assert updated.output == ''


class TestCorrectedCommand:
    def test_creation(self) -> None:
        cc = CorrectedCommand(script='sudo ls', side_effect=None, priority=1000)
        assert cc.script == 'sudo ls'
        assert cc.priority == 1000

    def test_equality_ignores_priority(self) -> None:
        a = CorrectedCommand('ls', None, 100)
        b = CorrectedCommand('ls', None, 200)
        assert a == b

    def test_hash(self) -> None:
        a = CorrectedCommand('ls', None, 100)
        b = CorrectedCommand('ls', None, 200)
        assert hash(a) == hash(b)

    def test_repr(self) -> None:
        cc = CorrectedCommand('ls', None, 100)
        assert 'CorrectedCommand' in repr(cc)


class TestRule:
    def test_creation(self) -> None:
        rule = Rule(
            name='test_rule',
            match=lambda cmd: True,
            get_new_command=lambda cmd: 'fixed',
            enabled_by_default=True,
            side_effect=None,
            priority=1000,
            requires_output=True,
        )
        assert rule.name == 'test_rule'
        assert rule.is_enabled

    def test_is_match(self) -> None:
        cmd = Command('ls', '')
        rule = Rule('test', lambda c: True, lambda c: 'x', True, None, 1000, False)
        assert rule.is_match(cmd)

    def test_no_match_when_output_required_but_none(self) -> None:
        cmd = Command('ls', None)
        rule = Rule('test', lambda c: True, lambda c: 'x', True, None, 1000, True)
        assert rule.is_match(cmd) is False

    def test_get_corrected_commands_string(self) -> None:
        cmd = Command('ls', '')
        rule = Rule('test', lambda c: True, lambda c: 'fixed', True, None, 1000, False)
        results = list(rule.get_corrected_commands(cmd))
        assert len(results) == 1
        assert results[0].script == 'fixed'

    def test_get_corrected_commands_list(self) -> None:
        cmd = Command('ls', '')
        rule = Rule('test', lambda c: True, lambda c: ['a', 'b'], True, None, 1000, False)
        results = list(rule.get_corrected_commands(cmd))
        assert len(results) == 2
        assert results[0].script == 'a'
        assert results[1].script == 'b'
