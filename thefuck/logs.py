from __future__ import annotations
# -*- encoding: utf-8 -*-

from contextlib import contextmanager
from datetime import datetime
import sys
from traceback import format_exception
import colorama
from .conf import settings
from .display import color
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .types import Rule


def warn(title: str) -> None:
    sys.stderr.write(u'{warn}[WARN] {title}{reset}\n'.format(
        warn=color(colorama.Back.RED + colorama.Fore.WHITE
                   + colorama.Style.BRIGHT),
        reset=color(colorama.Style.RESET_ALL),
        title=title))


def exception(title: str, exc_info: Any) -> None:
    sys.stderr.write(
        u'{warn}[WARN] {title}:{reset}\n{trace}'
        u'{warn}----------------------------{reset}\n\n'.format(
            warn=color(colorama.Back.RED + colorama.Fore.WHITE
                       + colorama.Style.BRIGHT),
            reset=color(colorama.Style.RESET_ALL),
            title=title,
            trace=''.join(format_exception(*exc_info))))


def rule_failed(rule: Rule, exc_info: Any) -> None:
    exception(u'Rule {}'.format(rule.name), exc_info)


def debug(msg: str, *args, **kwargs) -> None:
    if settings.debug:
        if args or kwargs:
            msg = msg.format(*args, **kwargs)
        sys.stderr.write(u'{blue}{bold}DEBUG:{reset} {msg}\n'.format(
            msg=msg,
            reset=color(colorama.Style.RESET_ALL),
            blue=color(colorama.Fore.BLUE),
            bold=color(colorama.Style.BRIGHT)))


@contextmanager
def debug_time(msg: str) -> Iterator[None]:
    started = datetime.now()
    try:
        yield
    finally:
        debug(u'{} took: {}'.format(msg, datetime.now() - started))


def version(thefuck_version: str, python_version: str, shell_info: str) -> None:
    sys.stderr.write(
        u'The Fuck {} using Python {} and {}\n'.format(thefuck_version,
                                                       python_version,
                                                       shell_info))
