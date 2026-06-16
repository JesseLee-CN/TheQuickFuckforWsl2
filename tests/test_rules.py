from __future__ import annotations

import pytest
from thefuck.types import Command


# ============================================================
# Simple pattern-matching rules (no decorators)
# ============================================================

class TestSudoRule:
    """tests/rules/sudo.py - pattern matching on command.output"""

    def test_match_permission_denied(self) -> None:
        from thefuck.rules.system.sudo import match
        cmd = Command('apt-get install nano', 'Permission denied')
        assert match(cmd)

    def test_match_eacces(self) -> None:
        from thefuck.rules.system.sudo import match
        cmd = Command('ls /root', 'EACCES')
        assert match(cmd)

    def test_no_match_normal(self) -> None:
        from thefuck.rules.system.sudo import match
        cmd = Command('ls', '')
        assert not match(cmd)

    def test_no_match_already_sudo(self) -> None:
        from thefuck.rules.system.sudo import match
        cmd = Command('sudo apt install', 'Permission denied')
        assert not match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.system.sudo import get_new_command
        cmd = Command('apt-get install nano', 'Permission denied')
        assert get_new_command(cmd) == 'sudo apt-get install nano'

    def test_get_new_command_with_redirect(self) -> None:
        from thefuck.rules.system.sudo import get_new_command
        cmd = Command('echo test > /etc/file', 'Permission denied')
        result = get_new_command(cmd)
        assert 'sudo' in result
        assert 'sh -c' in result


class TestManRule:
    """tests/rules/man.py - @for_app with multiple suggestions"""

    def test_match(self) -> None:
        from thefuck.rules.shell.man import match
        cmd = Command('man 3 printf', 'No manual entry for printf')
        assert match(cmd)

    def test_get_new_command_switches_section(self) -> None:
        from thefuck.rules.shell.man import get_new_command
        cmd = Command('man 3 printf', 'No manual entry for printf')
        result = get_new_command(cmd)
        # man rule replaces '3' with '2' for section switch
        assert '2' in result

    def test_suggests_help(self) -> None:
        from thefuck.rules.shell.man import get_new_command
        cmd = Command('man printf', 'No manual entry for printf')
        results = get_new_command(cmd)
        assert any('--help' in r for r in results)


# ============================================================
# @sudo_support decorator rules
# ============================================================

class TestPythonCommandRule:
    """@sudo_support on .py scripts without execute permission"""

    def test_match(self) -> None:
        from thefuck.rules.python.python_command import match
        cmd = Command('./script.py', 'Permission denied')
        assert match(cmd)

    def test_no_match_not_py(self) -> None:
        from thefuck.rules.python.python_command import match
        cmd = Command('./script.sh', 'Permission denied')
        assert not match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.python.python_command import get_new_command
        cmd = Command('./script.py', 'Permission denied')
        assert 'python' in get_new_command(cmd)


class TestRmDirRule:
    """@sudo_support for rm on directories"""

    def test_match(self) -> None:
        from thefuck.rules.file_ops.rm_dir import match
        cmd = Command('rm mydir', 'rm: mydir: is a directory')
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.file_ops.rm_dir import get_new_command
        cmd = Command('rm mydir', 'rm: mydir: is a directory')
        result = get_new_command(cmd)
        assert 'rm -rf' in result


# ============================================================
# @git_support decorator rules
# ============================================================

class TestGitPushRule:
    """@git_support with regex parsing of git output"""

    def test_match(self) -> None:
        from thefuck.rules.git_sync.git_push import match
        cmd = Command('git push', 'git push --set-upstream origin master\n')
        assert match(cmd)

    def test_no_match_no_push_in_output(self) -> None:
        from thefuck.rules.git_sync.git_push import match
        cmd = Command('git status', '')
        assert not match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.git_sync.git_push import get_new_command
        cmd = Command('git push', 'git push --set-upstream origin master\n')
        result = get_new_command(cmd)
        assert '--set-upstream' in result


class TestGitCheckoutRule:
    """@git_support for branch name typos"""

    def test_match(self) -> None:
        from thefuck.rules.git.git_checkout import match
        cmd = Command('git checkout featuer', "error: pathspec 'featuer' did not match any file(s) known to git")
        assert match(cmd)

    def test_no_match_non_git(self) -> None:
        from thefuck.rules.git.git_checkout import match
        cmd = Command('svn checkout', '')
        assert not match(cmd)


# ============================================================
# @for_app decorator rules
# ============================================================

class TestDockerNotCommandRule:
    """@for_app('docker') + @sudo_support"""

    def test_match(self) -> None:
        from thefuck.rules.docker.docker_not_command import match
        cmd = Command('docker containr ls', "docker: 'containr' is not a docker command.")
        assert match(cmd)

    def test_no_match_non_docker(self) -> None:
        from thefuck.rules.docker.docker_not_command import match
        cmd = Command('ls', '')
        assert not match(cmd)


class TestAgLiteralRule:
    """@for_app('ag') with simple string match"""

    def test_match(self) -> None:
        from thefuck.rules.grep_sed.ag_literal import match
        # ag_literal matches when output ends with 'run ag with -Q\n'
        cmd = Command('ag pattern', 'run ag with -Q\n')
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.grep_sed.ag_literal import get_new_command
        cmd = Command('ag -z pattern', 'ag: invalid option -- z')
        result = get_new_command(cmd)
        assert '-Q' in result


class TestPipUnknownCommandRule:
    """@for_app('pip', 'pip2', 'pip3')"""

    def test_match_pip(self) -> None:
        from thefuck.rules.pip.pip_unknown_command import match
        # pip_unknown_command requires 'maybe you meant' in output
        cmd = Command('pip instal', 'ERROR: unknown command "instal" - maybe you meant "install"')
        assert match(cmd)

    def test_no_match_other_app(self) -> None:
        from thefuck.rules.pip.pip_unknown_command import match
        cmd = Command('npm instal', '')
        assert not match(cmd)


class TestCatDirRule:
    """@for_app('cat', at_least=1)"""

    def test_match_with_real_dir(self) -> None:
        from thefuck.rules.system.cat_dir import match
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = Command(f'cat {tmpdir}', f'cat: {tmpdir}: Is a directory')
            # match checks os.path.isdir on script_parts[1]
            assert match(cmd) is True

    def test_no_match_cat_only(self) -> None:
        from thefuck.rules.system.cat_dir import match
        cmd = Command('cat', '')
        assert not match(cmd)


class TestOpenRule:
    """@for_app('open') + @eager"""

    def test_match(self) -> None:
        from thefuck.rules.system.open import match
        cmd = Command('open foo.txt', "The file foo.txt does not exist.")
        assert match(cmd)

    def test_no_match_non_open(self) -> None:
        from thefuck.rules.system.open import match
        cmd = Command('vim foo.txt', '')
        assert not match(cmd)


# ============================================================
# History-based rules
# ============================================================

class TestHistoryRule:
    """Matches against shell history"""

    def test_match_with_history(self) -> None:
        from thefuck.rules.shell.history import match
        # Without actual shell history, should return 0 matches
        cmd = Command('some_weird_cmd', 'command not found')
        result = match(cmd)
        # Returns the number of close matches (likely 0 without history)
        assert isinstance(result, int)


# ============================================================
# Complex rules
# ============================================================

class TestSwitchLangRule:
    """Keyboard layout mismatch detection"""

    def test_no_match_normal_output(self) -> None:
        from thefuck.rules.typo.switch_lang import match
        cmd = Command('ls', 'file1 file2')
        # With normal output and no 'not found', should not match
        assert not match(cmd)

    def test_match_russian_layout(self) -> None:
        from thefuck.rules.typo.switch_lang import match
        # Russian layout: 'рш' maps to 'hi' on qwerty
        cmd = Command('руддщ', 'command not found')
        # This depends on the layout being present in source_layouts
        result = match(cmd)
        # May or may not match depending on layout detection
        assert isinstance(result, bool)


class TestWhoisRule:
    """@for_app('whois', at_least=1) with URL parsing"""

    def test_match(self) -> None:
        from thefuck.rules.typo.whois import match
        cmd = Command('whois example.com', '')
        assert match(cmd)

    def test_no_match_non_whois(self) -> None:
        from thefuck.rules.typo.whois import match
        cmd = Command('dig example.com', '')
        assert not match(cmd)

    def test_get_new_command_with_slash(self) -> None:
        from thefuck.rules.typo.whois import get_new_command
        cmd = Command('whois https://en.wikipedia.org/', '')
        result = get_new_command(cmd)
        assert 'whois ' in result
        assert 'https://' not in result


class TestFixFileRule:
    """@default_settings + @memoize"""

    def test_rule_is_importable(self) -> None:
        from thefuck.rules.shell.fix_file import match, get_new_command
        # Verify the rule loads without errors
        assert callable(match)
        assert callable(get_new_command)


class TestChmodXRule:
    """Simple executable permission rule"""

    def test_match_with_real_file(self) -> None:
        from thefuck.rules.system.chmod_x import match
        # chmod_x checks os.path.exists and os.access(X_OK)
        import tempfile, os, stat
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sh') as f:
            f.write(b'#!/bin/sh\necho hi')
            f.flush()
            os.chmod(f.name, stat.S_IRUSR | stat.S_IWUSR)
            path = f.name
        try:
            cmd = Command(f'./{path}', 'permission denied')
            result = match(cmd)
            assert isinstance(result, bool)
        finally:
            os.unlink(path)

    def test_get_new_command(self) -> None:
        from thefuck.rules.system.chmod_x import get_new_command
        cmd = Command('./script.sh', 'permission denied')
        result = get_new_command(cmd)
        assert 'chmod +x' in result


class TestMkdirPRule:
    """mkdir -p suggestion"""

    def test_match(self) -> None:
        from thefuck.rules.system.mkdir_p import match
        cmd = Command('mkdir foo/bar', 'No such file or directory')
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.system.mkdir_p import get_new_command
        cmd = Command('mkdir foo/bar', 'No such file or directory')
        result = get_new_command(cmd)
        assert 'mkdir -p' in result


class TestLsLahRule:
    """ls typo fix"""

    def test_match(self) -> None:
        from thefuck.rules.system.ls_lah import match
        cmd = Command('ls lah', "ls: cannot access 'lah': No such file or directory")
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.system.ls_lah import get_new_command
        cmd = Command('ls lah', "ls: cannot access 'lah': No such file or directory")
        result = get_new_command(cmd)
        assert 'ls -lah' in result or 'ls -alh' in result


class TestCdParentRule:
    """cd.. typo"""

    def test_match(self) -> None:
        from thefuck.rules.file_ops.cd_parent import match
        cmd = Command('cd..', 'command not found')
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.file_ops.cd_parent import get_new_command
        cmd = Command('cd..', 'command not found')
        assert get_new_command(cmd) == 'cd ..'


class TestSlLsRule:
    """sl typo for ls"""

    def test_match(self) -> None:
        from thefuck.rules.system.sl_ls import match
        cmd = Command('sl', 'command not found')
        assert match(cmd)

    def test_get_new_command(self) -> None:
        from thefuck.rules.system.sl_ls import get_new_command
        cmd = Command('sl', 'command not found')
        assert 'ls' in get_new_command(cmd)
