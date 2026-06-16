from __future__ import annotations
import os
import re
import threading
from collections.abc import Callable, Iterable
from difflib import get_close_matches as difflib_get_close_matches
from functools import wraps
from typing import Any, TYPE_CHECKING
from .conf import settings
if TYPE_CHECKING:
    from .types import Command

from .cache import memoize, disable_memoize, disable_cache, reset_state, cache, Cache


_executable_cache = None
_executable_cache_lock = threading.Lock()


def _build_executable_cache():
    """Build a {name: path} cache of all executables found in PATH."""
    global _executable_cache
    _executable_cache = {}
    paths = list(dict.fromkeys(os.environ.get('PATH', '').split(os.pathsep)))
    for path in paths:
        if not include_path_in_search(path):
            continue
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if not entry.is_dir() and entry.name not in _executable_cache:
                        _executable_cache[entry.name] = os.path.join(path, entry.name)
        except OSError:
            pass


def which(program: str) -> str | None:
    """Returns the full path to `program` or `None`."""
    global _executable_cache
    if _executable_cache is None:
        with _executable_cache_lock:
            # Double-checked locking: another thread might have built
            # the cache while we were waiting for the lock.
            if _executable_cache is None:
                _build_executable_cache()
    return _executable_cache.get(program)


def default_settings(params: dict) -> Callable:
    """Adds default values to settings if it not presented.

    Usage:

        @default_settings({'apt': '/usr/bin/apt'})
        def match(command):
            print(settings.apt)

    """
    def _default_settings(fn):
        @wraps(fn)
        def wrapper(command, *args, **kwargs):
            for k, w in params.items():
                settings.setdefault(k, w)
            return fn(command, *args, **kwargs)
        return wrapper
    return _default_settings


def get_closest(word: str, possibilities: Iterable[str], cutoff: float = 0.6, fallback_to_first: bool = True) -> str | None:
    """Returns closest match or just first from possibilities."""
    possibilities = list(possibilities)
    try:
        return difflib_get_close_matches(word, possibilities, 1, cutoff)[0]
    except IndexError:
        if fallback_to_first:
            return possibilities[0]


def get_close_matches(word: str, possibilities: Iterable[str], n: int | None = None, cutoff: float = 0.6) -> list[str]:
    """Overrides `difflib.get_close_match` to control argument `n`."""
    if n is None:
        n = settings.num_close_matches
    return difflib_get_close_matches(word, possibilities, n, cutoff)


def include_path_in_search(path: str) -> bool:
    return not any(path.startswith(x) for x in settings.excluded_search_path_prefixes)


@memoize
def get_all_executables() -> list[str]:
    """Returns list of all available executables and aliases."""
    if _executable_cache is None:
        with _executable_cache_lock:
            if _executable_cache is None:
                _build_executable_cache()
    from thefuck.shells import shell
    tf_alias = get_alias()
    tf_entry_points = ['thefuck', 'fuck']
    aliases = [alias for alias in shell.get_aliases() if alias != tf_alias]
    return [name for name in _executable_cache
            if name not in tf_entry_points] + aliases


def replace_argument(script: str, from_: str, to: str) -> str:
    """Replaces command line argument."""
    if script.endswith(' ' + from_):
        return script[:-len(from_)] + to
    else:
        return script.replace(
            u' {} '.format(from_), u' {} '.format(to), 1)


def eager(fn: Callable) -> Callable:
    """Converts a generator-returning function into a list-returning function."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return list(fn(*args, **kwargs))
    return wrapper


@eager
def get_all_matched_commands(stderr: str, separator: str | list[str] = 'Did you mean') -> list[str]:
    if not isinstance(separator, list):
        separator = [separator]
    should_yield = False
    for line in stderr.split('\n'):
        for sep in separator:
            if sep in line:
                should_yield = True
                break
        else:
            if should_yield and line:
                yield line.strip()


def replace_command(command: Command, broken: str, matched: list[str]) -> list[str]:
    """Helper for *_no_command rules."""
    new_cmds = get_close_matches(broken, matched, cutoff=0.1)
    return [replace_argument(command.script, broken, new_cmd.strip())
            for new_cmd in new_cmds]


@memoize
def is_app(command: Command, *app_names: str, **kwargs: Any) -> bool:
    """Returns `True` if command is call to one of passed app names."""

    at_least = kwargs.pop('at_least', 0)
    if kwargs:
        raise TypeError("got an unexpected keyword argument '{}'".format(kwargs.keys()))

    if len(command.script_parts) > at_least:
        return os.path.basename(command.script_parts[0]) in app_names

    return False


def for_app(*app_names: str, **kwargs: Any) -> Callable:
    """Specifies that matching script is for one of app names."""
    def _for_app(fn):
        @wraps(fn)
        def wrapper(command, *args, **kwargs_inner):
            if is_app(command, *app_names, **kwargs):
                return fn(command, *args, **kwargs_inner)
            else:
                return False
        return wrapper
    return _for_app


@memoize
def get_installation_version() -> str:
    try:
        from importlib.metadata import version

        return version('thefuck')
    except ImportError:
        import pkg_resources

        return pkg_resources.require('thefuck')[0].version


def get_alias() -> str:
    return os.environ.get('TF_ALIAS', 'fuck')


@memoize
def get_valid_history_without_current(command: Command) -> list[str]:
    def _not_corrected(history, tf_alias):
        """Returns all lines from history except that comes before `fuck`."""
        previous = None
        for line in history:
            if previous is not None and line != tf_alias:
                yield previous
            previous = line
        if history:
            yield history[-1]

    from thefuck.shells import shell
    history = shell.get_history()
    tf_alias = get_alias()
    executables = set(get_all_executables())\
        .union(shell.get_builtin_commands())

    return [line for line in _not_corrected(history, tf_alias)
            if not line.startswith(tf_alias) and not line == command.script
            and line.split(' ')[0] in executables]


def format_raw_script(raw_script: list[str]) -> str:
    """Creates single script from a list of script parts.

    :type raw_script: [basestring]
    :rtype: basestring

    """
    script = ' '.join(raw_script)
    return script
