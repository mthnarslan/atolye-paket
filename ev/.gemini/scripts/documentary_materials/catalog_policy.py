"""The code a film's catalog (sources.prepare) depends on.

The catalog used to be keyed on the hash of the whole sources.py file, so
a comment or an unrelated fix in it prepared, downloaded and classified
the catalog again; every shot identity digests the catalog, so the film
was then re-planned and produced again (15-30 minutes a restart).

A catalog is now current while these are what they were (code_identity.py):

- SOURCE_POLICY_VERSION below. Bump it when a change the hashes do not
  see (a profile field, a helper in another module) has to reach the
  catalog of a resumed film;
- sources.py as a syntax tree, so comments and docstrings do not count;
- the source priority rule (io.SOURCE_PRIORITY_RULE), the capacity rule
  that stops the inventory rounds (planning.TARGET_SHOT_FRAMES and
  _video_capacity) and the source caps (reservations.py);
- bbc_library.py, only for a profile that searches the library.

window_index.py and footage.py are not part of it: they keep their own
caches beside the windows (VERSION, _VERSION) and write nothing into the
catalog.

This lives outside sources.py on purpose: a catalog of the older rule
holds the raw hash of sources.py, and it is recognised (and recorded
under this policy) only while that file is byte for byte unchanged.
"""
from pathlib import Path

from .io import SOURCE_PRIORITY_RULE, digest, sha

SOURCE_POLICY_VERSION = 1


def policy(production=None):
    """The source policy a catalog made under production is recorded with."""
    from . import code_identity
    parts = {"version": SOURCE_POLICY_VERSION, "code": code_identity.modules("sources.py"),
             "priority_rule": digest(SOURCE_PRIORITY_RULE),
             "capacity_rule": code_identity.definitions("planning.py", "TARGET_SHOT_FRAMES", "_video_capacity"),
             "source_caps": code_identity.definitions("reservations.py", "MAX_USES_PER_ORIGIN",
                                                      "MAX_USES_PER_MATERIAL", "MIN_SAME_ORIGIN_GAP_SECONDS")}
    if production and production.get("library"):
        parts["library"] = code_identity.modules("bbc_library.py")
    return digest(parts)


def current(catalog, production=None):
    """True when catalog was made by the source code that runs now.

    A catalog of the older rule (no "source_policy") holds the hash of the
    whole sources.py file; it is current while that file is unchanged,
    which is the rule it was made under.
    """
    if not catalog:
        return False
    if "source_policy" in catalog:
        return catalog["source_policy"] == policy(production)
    return catalog.get("source_policy_sha") == sha(Path(__file__).with_name("sources.py"))
