from __future__ import annotations

import pytest
from thefuck.utils import (
    get_closest, get_close_matches, replace_argument,
    is_app, format_raw_script, get_alias,
    get_all_matched_commands, replace_command,
    memoize, disable_memoize, disable_cache, reset_state,
    eager, which,
)
from thefuck.types import Command
from thefuck.conf import settings


class TestGetClosest:
    def test_exact_match(self) -> None:
        assert get_closest('ls', ['ls', 'lss']) == 'ls'

    def test_fuzzy_match(self) -> None:
        result = get_closest('got', ['git', 'get', 'hot'], cutoff=0.1)
        assert result is not None

    def test_fallback(self) -> None:
        result = get_closest('xyz', ['abc', 'def'], cutoff=0.6, fallback_to_first=True)
        assert result == 'abc'

    def test_no_fallback(self) -> None:
        result = get_closest('xyz', ['abc', 'def'], cutoff=0.6, fallback_to_first=False)
        assert result is None


class TestGetCloseMatches:
    def test_returns_list(self) -> None:
        settings.init()
        result = get_close_matches('gti', ['git', 'got', 'get'])
        assert isinstance(result, list)
        assert 'git' in result


class TestReplaceArgument:
    def test_replaces_in_middle(self) -> None:
        result = replace_argument('git brnch foo', 'brnch', 'branch')
        assert result == 'git branch foo'

    def test_replaces_at_end(self) -> None:
        result = replace_argument('git checkout brnch', 'brnch', 'branch')
        assert result == 'git checkout branch'


class TestIsApp:
    def test_matches(self) -> None:
        cmd = Command('git push', '')
        assert is_app(cmd, 'git')
        assert is_app(cmd, 'git', 'hub')

    def test_no_match(self) -> None:
        cmd = Command('ls', '')
        assert not is_app(cmd, 'git')

    def test_at_least(self) -> None:
        cmd = Command('man ls', '')
        assert is_app(cmd, 'man', at_least=1)
        cmd2 = Command('man', '')
        assert not is_app(cmd2, 'man', at_least=1)


class TestFormatRawScript:
    def test_joins_parts(self) -> None:
        result = format_raw_script(['git', 'push'])
        assert result == 'git push'

    def test_single_part(self) -> None:
        assert format_raw_script(['ls']) == 'ls'

    def test_empty_list(self) -> None:
        assert format_raw_script([]) == ''


class TestGetAlias:
    def test_default(self) -> None:
        assert get_alias() == 'fuck'


class TestGetAllMatchedCommands:
    def test_separator(self) -> None:
        stderr = 'Error\nDid you mean this?\n  command1\n  command2'
        result = get_all_matched_commands(stderr, 'Did you mean')
        assert 'command1' in result
        assert 'command2' in result

    def test_multiple_separators(self) -> None:
        stderr = 'Error\nTry: this\n  cmd1\n  cmd2'
        result = get_all_matched_commands(stderr, ['Did you mean', 'Try'])
        assert 'cmd1' in result
        assert 'cmd2' in result


class TestMemoize:
    def test_caches_result(self) -> None:
        calls = []
        @memoize
        def fn(x):
            calls.append(x)
            return x * 2
        assert fn(5) == 10
        assert fn(5) == 10
        assert len(calls) == 1  # only called once

    def test_disable_context(self) -> None:
        calls = []
        @memoize
        def fn(x):
            calls.append(x)
            return x * 2
        fn(3)
        assert len(calls) == 1
        with disable_memoize():
            fn(3)
            assert len(calls) == 2  # called again

    def test_reset_state(self) -> None:
        # reset_state resets memoize.disabled and _executable_cache
        from thefuck.utils import memoize, reset_state
        # Just verify it doesn't crash and sets disabled=False
        memoize.disabled = True
        reset_state()
        assert memoize.disabled is False


class TestEager:
    def test_converts_generator_to_list(self) -> None:
        @eager
        def gen():
            yield 1
            yield 2
            yield 3
        result = gen()
        assert result == [1, 2, 3]


class TestReplaceCommand:
    def test_returns_replacements(self) -> None:
        cmd = Command('dcker ps', '')
        result = replace_command(cmd, 'dcker', ['docker', 'docker-compose'])
        assert len(result) > 0
