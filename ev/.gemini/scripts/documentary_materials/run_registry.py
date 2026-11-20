"""The registry of active production runs, kept out of the reload path.

The bridge reloads the material modules before every stage request so a
code change takes effect without a restart, and a reload re-executes
the module it reloads. A registry that lives in a module-level dict is
emptied by that, so the guard that stops a second run on the same
output stops working exactly when the pipeline is asked to run twice.

Measured on the live run: queue_started was written twice, 162 seconds
apart, with 129 shots each, and the second pass put 15 workers on top
of the 15 the first one still had. The first pass took 2885 seconds
against a 1200 second budget, and every shot was produced twice.

This module is the one place the registry lives, and the bridge does
not reload it: the registry is imported by name and kept as a module
object, so a reload of the material package leaves it in place. The
entry is a plain path, so a second process that imports the same
module sees the same table.
"""
from pathlib import Path
import threading

_lock = threading.Lock()
_runs = {}


def claim(out, stop=None):
    """Take the output for a run. Returns False when it is already taken."""
    key = str(out)
    with _lock:
        if key in _runs:
            return False
        _runs[key] = stop if stop is not None else threading.Event()
        return True


def release(out):
    """Give the output back."""
    with _lock:
        _runs.pop(str(out), None)


def stop_for(path):
    """The stop event of the run whose output holds this path, or None."""
    path = Path(path)
    with _lock:
        for root, stop in _runs.items():
            root = Path(root)
            if path == root or root in path.parents:
                return stop
    return None
