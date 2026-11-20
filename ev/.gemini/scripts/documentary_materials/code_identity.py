"""The code part of every cached artifact's identity.

A resumed film reuses what it already made: the catalog, the plan, each
shot, the finished render. Each of those used to carry the hash of whole
files (sources.py, runner.py, the whole package for the bridge), so a
one-line edit anywhere made a resumed film prepare its sources, plan and
produce its shots again: 15-30 minutes per restart, a dozen restarts on
2026-10-25. Each cache now carries only the code that produces it.

Three kinds of code hash are used, from coarse to narrow:

- ``modules(name, ...)``: the module as Python sees it (its syntax tree
  without docstrings), so a comment, a docstring or a reformatting does
  not count and every real change does. A template (.html, .mjs) is hashed
  as bytes: its text is the picture.
- ``literals(name, function, ...)``: only the string constants inside
  the named top-level functions (or assignments). It follows the wording
  of a prompt built inline in a long function (runner._work_shot) while
  the logic around it may change.
- ``definitions(name, function, ...)``: the syntax tree of the named
  top-level functions or assignments, for a rule that lives in one
  function of a large module (runner._acceptable_review).

A change in logic that the narrow hash cannot see is reached through the
version constant of its stage, which a developer bumps:

=========================  =============================================
cache                      code it depends on
=========================  =============================================
catalog (catalog_policy.py catalog_policy.SOURCE_POLICY_VERSION, sources.py,
runner's catalog check)    the source priority rule, the capacity rule
                           (planning._video_capacity, TARGET_SHOT_FRAMES),
                           the source caps in reservations.py, and
                           bbc_library.py only for a library profile.
                           window_index.py and footage.py keep their own
                           caches (VERSION, _VERSION) beside the windows
                           and are not in the catalog.
plan (planning.make_plan)  planning.PLAN_VERSION only, plus its inputs
                           (timeline, catalog assets, targets, locks). A
                           re-plan rewrites every shot row and so every
                           shot identity: bump PLAN_VERSION when the
                           planner's behaviour must reach a resumed film.
shot (runner._identity)    runner.SHOT_POLICY_VERSION, render.py and the
                           sources helpers it cuts with, the wording of the selection / review prompts
                           (runner._SHOT_PROMPT_CODE), the acceptance rule
                           (runner._acceptable_review) and the shot's own
                           category modules (runner._CATEGORY_CODE).
recovery search            recovery.RECOVERY_VERSION, recovery.py and
                           the source policy above.
step 3 as a whole (bridge) the three above for the categories the plan
                           uses, and runner.py / the gates the end phase
                           runs (runner.stage3_signature).
step 4 render (bridge)     render_stage.py and the modules it calls, and
                           the delivered ledger itself: each shot's
                           status and picture hashes
                           (render_stage.stage4_signature).
=========================  =============================================

A file that is missing hashes to None, so a cache made with it never
matches a run without it.
"""
import ast
import hashlib
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent

_LOCK = threading.Lock()
_TREES = {}


def _hash(text):
    return hashlib.sha256(text.encode("utf8") if isinstance(text, str) else text).hexdigest()


def _stamp(path):
    try:
        st = path.stat()
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size


def _strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _tree(name):
    """(stamp, tree, raw-bytes hash) of a package file, read again when it changes.

    A Python file that does not parse (saved half way through an edit)
    has no tree and is hashed as bytes, so it matches nothing made before.
    """
    path = ROOT / name
    stamp = _stamp(path)
    if stamp is None:
        return None, None, None
    with _LOCK:
        cached = _TREES.get(name)
        if cached and cached[0] == stamp:
            return cached
    data = path.read_bytes()
    tree = None
    if path.suffix == ".py":
        try:
            # utf-8-sig: runner.py starts with a byte order mark.
            tree = _strip_docstrings(ast.parse(data.decode("utf-8-sig"), filename=str(path)))
        except (SyntaxError, ValueError):
            tree = None
    raw = _hash(data)
    with _LOCK:
        _TREES[name] = (stamp, tree, raw)
    return stamp, tree, raw


_RESULTS = {}


def _memo(kind, name, wanted, compute):
    """compute(tree, raw) once per file version: a shot identity asks for
    the same hashes many times, and dumping a tree costs ~0.1 s."""
    stamp, tree, raw = _tree(name)
    key = (kind, name, wanted)
    with _LOCK:
        hit = _RESULTS.get(key)
        if hit and hit[0] == stamp:
            return hit[1]
    value = compute(tree, raw)
    with _LOCK:
        _RESULTS[key] = (stamp, value)
    return value


def module_hash(name):
    """The hash of one package file: its syntax tree for Python, its bytes otherwise."""
    return _memo("module", name, (), lambda tree, raw: raw if tree is None
                 else _hash(ast.dump(tree, include_attributes=False)))


def modules(*names):
    return {name: module_hash(name) for name in names}


def _top_level(tree, wanted):
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in wanted:
            found[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    found[target.id] = node
    return found


def definitions(name, *wanted):
    """The hash of the named top-level definitions; a missing one counts as None."""
    def compute(tree, raw):
        if tree is None:
            return raw
        found = _top_level(tree, set(wanted))
        return _hash(repr([(w, ast.dump(found[w], include_attributes=False) if w in found else None)
                           for w in wanted]))
    return _memo("definitions", name, wanted, compute)


def literals(name, *wanted):
    """The hash of the string constants inside the named top-level definitions, in order."""
    def compute(tree, raw):
        if tree is None:
            return raw
        found = _top_level(tree, set(wanted))
        parts = []
        for w in wanted:
            node = found.get(w)
            parts.append((w, None if node is None else
                          [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]))
        return _hash(repr(parts))
    return _memo("literals", name, wanted, compute)


# Calls whose string arguments are log text, not generator input.
_LOG_CALLS = {"event", "print", "log", "warn", "warning", "info", "debug", "error", "progress", "write", "emit"}


def _call_name(node):
    f = node.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _prompt_strings(node, min_words):
    """String constants under node that read as prose (>= min_words words),
    skipping those inside a raise or a log/event call: event names, dict
    keys, short tags and error texts are not what a model is asked."""
    out = []

    def walk(n):
        if isinstance(n, ast.Raise):
            return
        if isinstance(n, ast.Call) and _call_name(n) in _LOG_CALLS:
            return
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value.split()) >= min_words:
            out.append(n.value)
        for c in ast.iter_child_nodes(n):
            walk(c)
    walk(node)
    return out


def prompt_literals(name, *wanted, min_words=6):
    """Like literals(), but only prompt-like prose: a log string, an event
    name or a dict key edited in a long function does not count, a word
    changed in a prompt does."""
    def compute(tree, raw):
        if tree is None:
            return raw
        found = _top_level(tree, set(wanted))
        return _hash(repr([(w, None if found.get(w) is None else _prompt_strings(found[w], min_words)) for w in wanted]))
    return _memo("prompt_literals", name, wanted + (min_words,), compute)
