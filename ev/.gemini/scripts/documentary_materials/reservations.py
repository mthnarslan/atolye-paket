"""Source-level excerpt rules shared by selection and final delivery."""
from urllib.parse import parse_qs, urlparse


def origin_id(asset):
    # Distinct photographs from one report are distinct materials; the no-repeat
    # rule applies to the image itself, not to every figure in that document.
    # A CARD is built from one photograph and carries its origin, so the
    # photograph is used once across PHOTO and CARD shots.
    if asset.get("category") in ("PHOTO","CARD") or asset.get("kind")=="PHOTO":
        if str(asset.get("origin_id","")).startswith("photo:"):return asset["origin_id"]
        return "photo:"+str(asset.get("sha256") or asset.get("id") or asset.get("source_id") or "")
    raw = asset.get("origin_id") or asset.get("source_url") or asset.get("url")
    if raw:
        parsed = urlparse(str(raw))
        host = parsed.netloc.lower().removeprefix("www.")
        if host in ("youtube.com", "m.youtube.com", "youtu.be"):
            video = (parse_qs(parsed.query).get("v") or [None])[0]
            if host == "youtu.be":
                video = parsed.path.strip("/").split("/")[0]
            if not video and parsed.path.startswith(("/shorts/", "/embed/")):
                video = parsed.path.split("/")[2]
            if video:
                return "youtube:" + video
        return str(raw)
    return str(asset.get("sha256") or asset.get("source_id") or asset.get("id") or "")


# One YouTube video may give the film up to four excerpts. Two was
# too few: with a limited pool the film ran out of usable material and
# shots died on the cap instead of on their own merit. Four (user's rule,
# 2026-10-24) lets a BBC-led film live on BBC: TOPIC_2's 16 usable BBC
# sources give 64 cuts at four, 48 at three, for ~59 needed.
MAX_USES_PER_ORIGIN = 4

# The three excerpts of one recording have to be far apart in it.
# Three cuts from one video read as three different places; three cuts
# from the same half minute read as a loop, which is what the film
# looked like when the rule only counted.
MIN_SAME_ORIGIN_GAP_SECONDS = 30.0

# A photograph, a generated 3D scene or any other single material is
# used once. Repeating a picture is repeating a picture, whatever its
# origin is.
MAX_USES_PER_MATERIAL = 1


def _origin_limit(origin_uses):
    """How many times one origin may appear in the film."""
    if any(u.get("category") == "VIDEO" for u in origin_uses):
        return MAX_USES_PER_ORIGIN
    return MAX_USES_PER_MATERIAL


# The uploads that carry the same footage, as {origin: group}. One
# recording is uploaded again under other YouTube ids, and those uploads
# are one source to the viewer. footage.py measures the groups; they
# are kept here because every rule below reads them. The bridge reloads
# this module before each stage request, and a reload must not drop
# the groups of a run that is still producing, so the map is carried
# over from the previous module body.
_FOOTAGE = globals().get("_FOOTAGE", {})


def use_footage_groups(groups):
    """Add measured groups; a group that shares an upload with a known one joins it."""
    for members in _members(groups).values():
        joined = set(members)
        for origin in members:
            joined |= _members(_FOOTAGE).get(_FOOTAGE.get(origin), set())
        name = "footage:" + min(joined)
        _FOOTAGE.update({origin: name for origin in joined})


def _members(groups):
    by_group = {}
    for origin, group in groups.items():
        by_group.setdefault(group, set()).add(origin)
    return by_group


def footage(origin):
    """The source an origin counts as: its footage group, or itself."""
    return _FOOTAGE.get(origin, origin)


def footage_uses(uses, origin):
    """The uses that count against the same source as origin."""
    key = footage(origin)
    return [u for u in uses if footage(u.get("origin")) == key]


def same_footage_origins(origins):
    """Every origin that shows the same footage as one of origins."""
    keys = {footage(o) for o in origins}
    return set(origins) | {o for o, g in list(_FOOTAGE.items()) if g in keys}


def allowed(existing, proposed):
    """Video excerpts of one source are few and far apart; other material is used once."""
    uses = list(existing) + list(proposed)
    if not uses:
        return True
    # Count by origin, not by category. A video counted once per excerpt
    # would trip the cap at three excerpts; a photograph has no excerpt
    # range, so it has to be counted per use of the same origin. Uploads
    # of the same footage are one origin here.
    by_origin = {}
    for u in uses:
        by_origin.setdefault(footage(u.get("origin")), []).append(u)
    for origin, origin_uses in by_origin.items():
        if len(origin_uses) > _origin_limit(origin_uses):
            return False
    # The gap rule is about excerpts inside one source, so it is
    # checked per origin. Two different videos may both be cut from
    # second zero without overlapping anything, and a photograph
    # carries no range at all - it is stamped at 0-0 - so two
    # different photographs would otherwise look like two overlapping
    # excerpts of the same thing.
    for origin, origin_uses in by_origin.items():

        ranged = sorted((u for u in origin_uses if u.get("category") == "VIDEO"),
                        key=lambda u: u["start"])

        # Two uploads of one footage have their own timelines, and a
        # second of one is not the same second of the other: a re-upload
        # trimmed by a minute shows the collapse a minute earlier. The
        # gap between them cannot be measured, so the cuts of one
        # footage come from one upload, where it can.
        if len({u.get("origin") for u in ranged}) > 1:

            return False

        for a, b in zip(ranged, ranged[1:]):

            if b["start"] - a["end"] < MIN_SAME_ORIGIN_GAP_SECONDS:

                return False

    return True


def available_ranges(start, end, existing, origin=None):
    """The parts of a source that are still free, apart from the used cuts.

    A used cut takes its own seconds and the gap around it: the next
    cut from the same recording has to be a different part of it. With
    origin given, existing may hold every use of the film: the uses of
    the same footage are taken from it, and a use from another upload
    of that footage leaves this upload nothing (see allowed).
    """
    if origin is not None:
        existing = footage_uses(existing, origin)
        if any(u.get("origin") != origin for u in existing if u.get("category") == "VIDEO"):
            return []
    if len(existing) >= MAX_USES_PER_ORIGIN or any(u.get("category") != "VIDEO" for u in existing):
        return []
    ranges = [(float(start), float(end))]
    for use in existing:
        blocked_start = float(use["start"]) - MIN_SAME_ORIGIN_GAP_SECONDS
        blocked_end = float(use["end"]) + MIN_SAME_ORIGIN_GAP_SECONDS
        ranges = [(a, min(b, blocked_start)) for a, b in ranges if a < blocked_start] + [
            (max(a, blocked_end), b) for a, b in ranges if b > blocked_end]
    return [(a, b) for a, b in ranges if b-a >= 1]
