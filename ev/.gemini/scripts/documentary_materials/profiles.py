"""Production profiles: what a film may show and where its footage is searched.

A profile is chosen once per film (the bridge's /run body field "profile")
and stored in the run's settings.json, so every stage and every restart
reads the same one. The default profile is the engineering/history mix the
pipeline was built for; nothing in it differs from the behaviour before
profiles existed.
"""
from pathlib import Path

from .io import load

DEFAULT = "default"

# The wildlife film's priority channels, searched before the rest of
# YouTube. Each id was resolved and checked with yt-dlp on 2026-10-23
# (channel name, @handle, followers, latest uploads):
#   BBC Earth           @bbcearth            14.6M
#   BBC Studios         @BBCStudios           3.9M
#   BBC Earth Science   @BBCEarthScience      1.8M  (formerly BBC Earth Lab)
#   BBC Earth Relax     @BBCEarthRelax         28K  narration-free 4K nature
#   BBC Wildlife Mag.   @BBCWildlifeMagazine  949
#   BBC                 @BBC                 15.7M  carries the BBC One / BBC
#                                                  Two programme clips
# @BBCOne and @BBCTwo are not the broadcaster (9 and 11 followers,
# unrelated uploads) and BBC Earth Unplugged no longer resolves (404), so
# none of them is listed. BBC Earth Kids (UCO_DaPp4ifhMAmiyybSLx9w) is real
# but its channel has no search tab ("This channel does not have a search
# tab"), so it cannot be searched this way; it is in BBC_ALSO instead.
BBC_CHANNELS = (
    ("BBC Earth", "UCwmZiChSryoWQCZMIQezgTg"),
    ("BBC Studios", "UC2ccm1GajfSujz7T18d7cKA"),
    ("BBC Earth Science", "UCdsOTr6SmDrxuWE7sJFrkhQ"),
    ("BBC Earth Relax", "UC4dMNPt9AGb_o2GwVBf_qNA"),
    ("BBC Wildlife Magazine", "UCTs788MsV-QQeGNGG0xDFSQ"),
    ("BBC", "UCCj956IF62FbT7Gouszaj9w"),
)

# BBC channels that are not searched inside but count as BBC when a
# general search finds them: BBC Earth Kids has no search tab and showed
# 25 times in 14 languages of BBC Earth searches; Sony BBC Earth is BBC
# Earth's Indian channel.
BBC_ALSO = (
    ("BBC Earth Kids", "UCO_DaPp4ifhMAmiyybSLx9w"),
    ("Sony BBC Earth", "UCcIPw0eP8KQPUXh5rK4wp3A"),
)

# Footage is searched in English and in these languages; only the picture
# is used, so the narration language of a video does not matter. Chosen by
# measured yield (new usable videos per query that English did not find).
SEARCH_LANGUAGES = ("es", "pt", "fr", "de", "ru", "ja")

PROFILES = {
    DEFAULT: {
        # History/technology films: CARD is the white explainer card built
        # from a photograph (cards.py). ANIM is the generated vox-style 2D
        # animation (anim.py, G-Labs). MOTION is the code-drawn motion
        # graphic (motion.py, HyperFrames); its 10 points come from CARD
        # (user's mix, 2026-10-24).
        "targets": {"VIDEO": 40, "PHOTO": 10, "3D": 10, "CARD": 15, "MOTION": 10, "ANIM": 15},
    },
    "wildlife": {
        # Real footage only: no photograph and no generated scene, in the
        # plan, in its repairs and in the delivered film. A missing CARD
        # target counts as 0 everywhere.
        "targets": {"VIDEO": 100, "PHOTO": 0, "3D": 0},
        "priority_channels": BBC_CHANNELS,
        # The local BBC episode library (bbc_library) is searched first.
        "library": True,
        "priority_channel_ids": [cid for _, cid in BBC_CHANNELS + BBC_ALSO],
        # Footage from these channels and the local BBC library only:
        # every other YouTube channel, Commons and the Internet Archive
        # are dropped from every search of the run.
        "bbc_only": True,
        # A shot the BBC footage cannot cover may take another channel's
        # video, found by the shot queue's own search, if no frame shows a
        # logo or watermark.
        "logo_free_fallback": True,
        # ...and not only as a fallback: other channels join every search of
        # the run, the BBC is not ranked first (user, 2026-10-25).
        "nonbbc_from_start": True,
        # A line no footage carries and a landscape can show (water, land,
        # sky, season, with no animal in view) may get a generated
        # photoreal landscape clip, up to this share of the film.
        "ai_landscape_fallback": 0.10,
        # A line nothing could carry runs under its neighbour's footage up
        # to 14 s, 15 s in the last merge round (default 9 / 10 s): long
        # slow shots are normal in nature films, and TOPIC_1 stopped on six
        # such lines whose neighbours would have passed 10 s.
        # 17.5 s since 2026-10-26: TOPIC_3/4/7/8 each stopped on one last line
        # whose neighbour needed 15-17.6 s, raised by hand every time.
        "merge_max_sec": 17.5,
        # Shots stay ~4 s; only when the clean VIDEO cuts fall short are the
        # fewest of them lengthened, to at most 7 s (planning.shot_length).
        # The 30 s hook is never lengthened.
        "shot_seconds": "auto",
        "languages": SEARCH_LANGUAGES,
        # Results taken from each priority channel for one short topic.
        # Long footage queries found 10 BBC videos for TOPIC_2 (of 251
        # candidates); 8 two- or three-word topics found 56 on BBC Earth.
        "channel_take": 10,
        # Results taken from a non-English YouTube query.
        "localized_take": 10,
        # Sources fetched per query in the per-sentence search (default 2),
        # and the ceiling of one search batch (default 40).
        "per_query_take": 3,
        "max_sources": 150,
        "search_workers": 12,
        # NASA's archive has no wildlife; Commons and the Internet Archive do.
        "sites": ("youtube", "commons", "archive"),
        "catalog_brief": ("The film is a wildlife documentary and needs real nature footage to cut, not people talking: "
                          "target wildlife documentary footage of the animals, their behaviour (hunting, feeding, mating, "
                          "migration, raising young) and their habitats, aerial and underwater nature footage, slow motion "
                          "and raw or b-roll footage. "),
        "selection_brief": "animals, behaviour, habitats, landscapes and seasons of the story",
        # Appended after a sentence that ends in ". ", so it ends in one too.
        "prompt_note": ("Burned-in subtitles in any language or script (Latin, Cyrillic, Arabic, Devanagari, CJK) are "
                        "burned-in subtitles; a presenter or narrator talking to the camera is a talking head in any language. "),
    },
}


def get(name=None):
    """The profile called name (default when None), with its name."""
    name = DEFAULT if name in (None, "") else str(name).strip().lower()
    if name not in PROFILES:
        raise ValueError("Unknown production profile %r; known: %s" % (name, ", ".join(sorted(PROFILES))))
    return {"name": name, **PROFILES[name]}


def stored(out):
    """The profile name saved in a run's settings.json, or None."""
    path = Path(out) / "settings.json"
    if not path.is_file():
        return None
    return load(path).get("profile")


def for_run(out):
    """The profile a run folder was started with.

    A run's settings.json may carry its own "targets" (the screen-time mix),
    which replace the profile's: the Blackout film had 37 usable photographs
    for a PHOTO+CARD share that needed ~46, and the plan was infeasible.
    """
    production = get(stored(out))
    targets = None
    merge = None
    # The film folder's film_settings.json (copied beside the voice output)
    # holds it for good; settings.json is rewritten at every step-3 start.
    # It may also raise a film's neighbour-merge length (TOPIC_3 206 needed
    # 15.3 s, the user allowed about 15 s for a wildlife film's last gaps).
    for path in (Path(out) / "settings.json", Path(out).parent / "film_settings.json"):
        try:
            data = (load(path) or {}) if path.exists() else {}
            targets = targets or data.get("targets")
            merge = merge or data.get("merge_max_sec")
        except Exception:
            pass
    if merge:
        production = {**production, "merge_max_sec": float(merge)}
    return {**production, "targets": dict(targets)} if targets else production


def video_only(targets):
    """True when the mix gives PHOTO, 3D, CARD, ANIM and MOTION no screen time at all."""
    return bool(targets) and all(float(targets.get(c, 0)) == 0 for c in ("PHOTO", "3D", "CARD", "ANIM", "MOTION"))
