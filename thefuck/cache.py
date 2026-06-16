from __future__ import annotations
import atexit
import contextlib
import dbm
import os
import pickle
import shelve
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator
from functools import wraps
from typing import Any

from .system import Path


DEVNULL = subprocess.DEVNULL

shelve_open_error = dbm.error


def memoize(fn: Callable) -> Callable:
    """Caches previous calls to the function."""
    memo = {}

    @wraps(fn)
    def wrapper(*args, **kwargs) -> Any:
        if not memoize.disabled:
            key = pickle.dumps((args, kwargs))
            if key not in memo:
                memo[key] = fn(*args, **kwargs)
            value = memo[key]
        else:
            # Memoize is disabled, call the function
            value = fn(*args, **kwargs)

        return value

    return wrapper


memoize.disabled = False


class Cache(object):
    """Lazy read cache and save changes at exit."""

    def __init__(self) -> None:
        self._db: Any = None
        self._lock = threading.Lock()

    def _init_db(self) -> None:
        with self._lock:
            if self._db is not None:
                return
            try:
                self._setup_db()
            except Exception:
                from .logs import exception
                exception("Unable to init cache", sys.exc_info())
                self._db = {}

    def _setup_db(self) -> None:
        cache_dir = self._get_cache_dir()
        cache_path = Path(cache_dir).joinpath('thefuck').as_posix()

        try:
            self._db = shelve.open(cache_path)
        except shelve_open_error + (ImportError,):
            from .logs import warn
            warn("Removing possibly out-dated cache")
            os.remove(cache_path)
            self._db = shelve.open(cache_path)

        atexit.register(self._db.close)

    def _get_cache_dir(self) -> str:
        default_xdg_cache_dir = os.path.expanduser("~/.cache")
        cache_dir = os.getenv("XDG_CACHE_HOME", default_xdg_cache_dir)

        # Ensure the cache_path exists, Python 2 does not have the exist_ok
        # parameter
        try:
            os.makedirs(cache_dir)
        except OSError:
            if not os.path.isdir(cache_dir):
                raise

        return cache_dir

    def _get_mtime(self, path: str) -> str:
        try:
            return str(os.path.getmtime(path))
        except OSError:
            return '0'

    def _get_key(self, fn: Callable, depends_on: list[str], args: tuple, kwargs: dict) -> str:
        parts = (fn.__module__, repr(fn).split('at')[0],
                 depends_on, args, kwargs)
        return str(pickle.dumps(parts))

    def get_value(self, fn: Callable, depends_on: list[str], args: tuple, kwargs: dict) -> Any:
        if self._db is None:
            self._init_db()

        depends_on = [Path(name).expanduser().absolute().as_posix()
                      for name in depends_on]
        key = self._get_key(fn, depends_on, args, kwargs)
        etag = '.'.join(self._get_mtime(path) for path in depends_on)

        if self._db.get(key, {}).get('etag') == etag:
            return self._db[key]['value']
        else:
            value = fn(*args, **kwargs)
            self._db[key] = {'etag': etag, 'value': value}
            return value


_cache = Cache()


def cache(*depends_on: str) -> Callable:
    """Caches function result in temporary file.

    Cache will be expired when modification date of files from `depends_on`
    will be changed.

    Only functions should be wrapped in `cache`, not methods.

    """
    def cache_decorator(fn):
        @memoize
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if cache.disabled:
                return fn(*args, **kwargs)
            else:
                return _cache.get_value(fn, depends_on, args, kwargs)

        return wrapper

    return cache_decorator


cache.disabled = False


@contextlib.contextmanager
def disable_memoize() -> Iterator[None]:
    """Context manager to temporarily disable memoization (for testing)."""
    previous = memoize.disabled
    memoize.disabled = True
    try:
        yield
    finally:
        memoize.disabled = previous


@contextlib.contextmanager
def disable_cache() -> Iterator[None]:
    """Context manager to temporarily disable persistent cache (for testing)."""
    previous = cache.disabled
    cache.disabled = True
    try:
        yield
    finally:
        cache.disabled = previous


def reset_state() -> None:
    """Reset all module-level state. Intended for testing."""
    from thefuck import utils
    utils._executable_cache = None
    memoize.disabled = False
    cache.disabled = False
