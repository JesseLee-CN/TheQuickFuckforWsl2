from __future__ import annotations

from thefuck.types import Command
from thefuck.specific.sudo import sudo_support
from thefuck.specific.git import git_support


class TestSudoSupport:
    def test_adds_sudo_to_string_result(self) -> None:
        @sudo_support
        def get_new_command(command: Command) -> str:
            return 'apt-get install'

        cmd = Command('sudo apt-get install', 'Permission denied')
        result = get_new_command(cmd)
        assert result == 'sudo apt-get install'

    def test_adds_sudo_to_list_result(self) -> None:
        @sudo_support
        def get_new_command(command: Command) -> list[str]:
            return ['cmd1', 'cmd2']

        cmd = Command('sudo something', 'Permission denied')
        result = get_new_command(cmd)
        assert result == ['sudo cmd1', 'sudo cmd2']

    def test_no_sudo_prefix(self) -> None:
        """When command doesn't start with sudo, function passes through."""
        @sudo_support
        def match(command: Command) -> bool:
            return True

        cmd = Command('apt-get install', '')
        result = match(cmd)
        assert result is True

    def test_passes_extra_args(self) -> None:
        """verify extra args are forwarded when present."""
        calls = []
        @sudo_support
        def fn(command: Command, extra: str) -> str:
            calls.append(extra)
            return 'result'

        cmd = Command('ls', '')
        result = fn(cmd, 'hello')
        assert result == 'result'
        assert calls == ['hello']


class TestGitSupport:
    def test_git_command(self) -> None:
        @git_support
        def match(command: Command) -> bool:
            return 'push' in command.script

        cmd = Command('git push', '')
        result = match(cmd)
        assert result is True

    def test_hub_command(self) -> None:
        @git_support
        def match(command: Command) -> bool:
            return True

        cmd = Command('hub push', '')
        result = match(cmd)
        assert result is True

    def test_non_git_command(self) -> None:
        @git_support
        def match(command: Command) -> bool:
            return True

        cmd = Command('ls -la', '')
        result = match(cmd)
        assert result is False

    def test_git_alias_expansion(self) -> None:
        """When output contains git trace, aliases are expanded."""
        @git_support
        def match(command: Command) -> bool:
            return 'commit' in command.script

        cmd = Command('git ci', "trace: alias expansion: ci => 'commit'")
        result = match(cmd)
        assert result is True
