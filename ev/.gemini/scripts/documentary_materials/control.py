"""Cooperative cancellation for the synchronous worker behind a Langflow node."""
from concurrent.futures import CancelledError
from contextlib import contextmanager
from pathlib import Path
import threading

from . import run_registry as _registry

_local=threading.local()

# The active-run registry has to survive a module reload. The bridge
# reloads the material modules before every stage 3 request so a code
# change takes effect without a restart, and a reload re-executes this
# module: a registry that lives in a module-level dict is emptied by
# that, so the second request finds no active run and starts a second
# production pass on top of the first one.
#
# Measured on the live run: queue_started was written twice, 162
# seconds apart, with 129 shots each, and the second pass ran 15
# workers on top of the 15 the first one still had. The first pass took
# 2885 seconds instead of the 1200 the budget allows.
#
# The registry is therefore kept in a module that is never reloaded.
# The lock file of the same name is the durable half of it: a run that
# belongs to another process is still seen, and the registry that the
# in-process check reads is the one this module imported.


def set_context(out):
    _local.out=Path(out).resolve()
    check_cancelled(out)


def check_cancelled(path=None):
    path=Path(path).resolve() if path is not None else getattr(_local,'out',None)
    if path is None:return
    stop=_registry.stop_for(path)
    if stop is not None and stop.is_set():raise CancelledError('Langflow material job cancelled')


@contextmanager
def production_run(out,stop=None):
    out=Path(out).resolve()
    if not _registry.claim(out,stop):
        raise RuntimeError('This output already has an active production job; wait for cancellation to finish')
    try:
        set_context(out)
        yield
    finally:
        _registry.release(out)
        _local.out=None
