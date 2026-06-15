"""Package with shell specific actions, each shell class should
implement `from_shell`, `to_shell`, `app_alias`, `put_to_history` and
`get_aliases` methods.

.. note::

    ``shell`` is a module-level global (module singleton pattern).
    It is lazily initialized at import time by auto-detecting the
    current shell from the process tree (via ``psutil``) or the
    ``TF_SHELL`` environment variable. This is an intentional design
    choice to avoid passing a shell instance through every function
    signature. Tests can override it by setting ``TF_SHELL`` in the
    environment or by monkey-patching the ``shell`` global.
"""
import os
from psutil import Process
from .bash import Bash
from .fish import Fish
from .generic import Generic
from .tcsh import Tcsh
from .zsh import Zsh
from .powershell import Powershell

shells = {'bash': Bash,
          'fish': Fish,
          'zsh': Zsh,
          'csh': Tcsh,
          'tcsh': Tcsh,
          'powershell': Powershell,
          'pwsh': Powershell}


def _get_shell_from_env():
    name = os.environ.get('TF_SHELL')

    if name in shells:
        return shells[name]()


def _get_shell_from_proc():
    proc = Process(os.getpid())

    while proc is not None and proc.pid > 0:
        try:
            name = proc.name()
        except TypeError:
            name = proc.name

        name = os.path.splitext(name)[0]

        if name in shells:
            return shells[name]()

        try:
            proc = proc.parent()
        except TypeError:
            proc = proc.parent

    return Generic()


shell = _get_shell_from_env() or _get_shell_from_proc()
