"""The three editorial rules that the film has to obey.

1. A recording may give up to three excerpts, and those excerpts have
   to be at least 30 seconds apart in it. A photograph, a 3D scene or
   any other single material is used once. The cap is counted on the
   base YouTube id, not on the chunk id, because the chunks of one
   video are one source.
2. A person may not speak to the camera in a shot, unless the
   narration of that shot names that person. An interview of a
   stranger under a narration about a bolt is a talking head, not
   evidence.
3. Burned-in subtitles in the source footage are removed, because
   the film carries its own captions and two sets of text do not
   belong on the same picture.

The rules live here, in one place, so the selector and the delivery
gate ask the same question. A rule that is written twice is a rule
that is checked once.

None of these rules is written for one film. Every one of them reads
the words of the source and the words of the script, so the same code
holds for the next subject.
"""
import re

# The titles that a documentary puts in front of the people it talks
# about. A title is what makes a capitalised phrase a person: "Engineer
# Dan Bunch" is a person, "Engineer Explains The Failure" is a
# headline.
_PERSON_TITLES = {
    "dr", "mr", "mrs", "ms", "prof", "professor", "doctor", "engineer",
    "architect", "detective", "investigator", "reporter", "chief",
    "officer", "surveyor", "consultant", "attorney", "president",
    "senator", "mayor", "scientist", "author", "survivor", "witness",
    "anchor", "journalist", "manager", "worker", "student", "producer",
    "designer", "contractor", "inspector", "foreman", "supervisor",
    "technician", "developer", "supervisor", "coroner", "mayor",
}

# The verbs that a headline puts after a title. "Engineer Explains The
# Failure" names nobody.
_TITLE_VERBS = {
    "explains", "explained", "says", "said", "tells", "told", "reflects",
    "discusses", "discussed", "describes", "described", "recalls",
    "recalled", "shares", "recounts", "recounted", "asks", "answers",
    "speaks", "spoke", "talks", "talked", "adds", "notes", "states",
    "remembers", "studies", "documents", "revisits", "warns", "warned",
    "claims", "claimed", "reveals", "revealed", "explaining", "talking",
    "recounting", "describing", "discussing", "speaking", "reflecting",
}

# The words that end an institution or a place. A capitalised phrase
# that holds one of them is an organisation or a place, never a
# person: "Havens Steel Company", "Kansas City", "National Bureau of
# Standards". The list is English, not the subject of the film, so it
# holds for the next subject as well.
_ORG_WORDS = {
    "company", "corporation", "international", "group", "holdings", "inc",
    "ltd", "llc", "foundation", "association", "council", "committee",
    "society", "agency", "department", "ministry", "bureau", "institute",
    "university", "college", "school", "hospital", "bank", "city",
    "state", "county", "province", "country", "region", "district",
    "island", "mountain", "river", "valley", "avenue", "street", "road",
    "highway", "boulevard", "bridge", "building", "code", "law", "act",
    "standards", "court", "board", "center", "centre", "union", "party",
    "office", "service", "news", "network", "systems", "technologies",
    "industries", "works", "press", "times", "journal", "report",
    "magazine", "channel", "station", "club", "hotel", "mall", "plaza",
    "square", "park", "airport", "terminal", "plant", "factory", "mine",
    "farm", "ranch", "church", "temple", "mosque", "cathedral",
    "museum", "library", "theater", "theatre", "stadium", "arena",
    "project", "program", "unit", "force", "office", "bureau",
}

# A word of the text. A period stays on the word, because a period is
# what tells an initial from the end of a sentence.
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*\.?")
_INITIAL = re.compile(r"^[A-Z]\.$")

# A title in front of a name, and an interview in front of a name.
_TITLE_ANCHOR = re.compile(
    r"\b(" + "|".join(sorted(_PERSON_TITLES)) + r")\.?\s+", re.IGNORECASE)
_INTERVIEW_ANCHOR = re.compile(
    r"\b(?:Interview|Talk|Conversation|Q&A)\s+(?:with|of|to)\s+", re.IGNORECASE)


def _is_initial(word):
    """True for a single capital letter with a period, as in "D."."""
    return bool(_INITIAL.match(word))


def _initials_of(run):
    """The initials of a run of capitalised words.

    An initial stands between a name and a surname: "Jack D. Gillum".
    The letter of an abbreviation does not: "U.S. Accidental" carries
    no person, so the letter is not an initial unless a name stands
    before it and a name stands after it.
    """
    found = set()
    for index, word in enumerate(run):
        if not _is_initial(word) or index == 0 or index + 1 >= len(run):
            continue
        previous = run[index - 1].rstrip(".")
        following = run[index + 1].rstrip(".")
        if len(previous) >= 2 and previous[:1].isupper() \
                and len(following) >= 2 and following[:1].isupper():
            found.add(_clean(word))
    return found


def _clean(word):
    """A word without its period, in lower case."""
    return word.rstrip(".").lower()


def _ends_run(word):
    """True when a word ends the run of capitalised words.

    A word that ends a sentence ends the run, so that the first word
    of the next sentence never joins the name before it. An initial
    and a title do not end the run, so "Jack D. Gillum" and
    "Dr. Waeckerle" stay one name.
    """
    if word[-1] not in ".!?":
        return False
    if _is_initial(word) or _clean(word) in _PERSON_TITLES:
        return False
    return True


def _capitalised_runs(text):
    """The runs of capitalised words in a text.

    A run is a maximal sequence of capitalised words. A word that ends
    a sentence ends the run, so that the first word of the next
    sentence never joins the name before it. An initial does not end
    the run, so "Jack D. Gillum" stays one name.
    """
    runs, run = [], []
    for word in _WORD.findall(text or ""):
        if not word[:1].isupper():
            if run:
                runs.append(run)
                run = []
            continue
        run.append(word)
        if _ends_run(word):
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return runs


def _names_of_run(run):
    """The names that a run of capitalised words carries.

    A run is a person when it holds a title, when it holds an initial,
    or when it is a first name and a surname. A run that holds an
    institution or a place is no person at all, and a run that starts
    with a verb names nobody.
    """
    words = [_clean(w) for w in run]
    if not words or any(w in _ORG_WORDS for w in words):
        return set()
    if words[0] in _TITLE_VERBS:
        return set()
    titled = any(w in _PERSON_TITLES for w in words)
    initials = _initials_of(run)
    names = [w for w in words
             if w not in _PERSON_TITLES and w not in _TITLE_VERBS
             and w not in initials]
    if not names:
        return set()
    # A person is a first name and a surname. One word alone is a
    # person only when a title or an initial stands in front of it.
    if not (titled or initials or len(names) == 2):
        return set()
    return {names[0]} | ({names[1]} if len(names) > 1 else set())


def _names_after(text, start):
    """The names in the capitalised run that follows a position."""
    run = []
    for match in _WORD.finditer(text, start):
        word = match.group(0)
        if not word[:1].isupper():
            break
        run.append(word)
        if len(run) >= 3:
            break
        if _ends_run(word):
            break
    return _names_of_run(run) if run else set()


def narration_names(text):
    """The people the narration names, as lowercase tokens.

    The narration is read in English and names people in the two ways
    a documentary uses: "Dr. Waeckerle" and "Dan Bunch". A capitalised
    word that is only a topic of the film, as in "Kansas City" or
    "Havens Steel Company", names nobody.
    """
    found = set()
    for run in _capitalised_runs(text):
        found |= _names_of_run(run)
    return found


def named_person(text):
    """The name of the person a source names, as lowercase tokens.

    A source names a person when it writes a title in front of a name,
    as in "Engineer Dan Bunch", or when it introduces an interview with
    a name, as in "Interview with Dan Bunch". A source that names
    nobody gives no name, and a person without a name may not speak in
    the film.
    """
    if not text:
        return set()
    text = str(text)
    found = set()
    for match in _TITLE_ANCHOR.finditer(text):
        found |= _names_after(text, match.end())
    for match in _INTERVIEW_ANCHOR.finditer(text):
        found |= _names_after(text, match.end())
    # A run that holds an initial is a person without a title in front
    # of it: "Jack D. Gillum". A run of two capitalised words is not
    # enough on its own, because "Instant Recall" is a programme name.
    for run in _capitalised_runs(text):
        if _initials_of(run):
            found |= _names_of_run(run)
    return found


def narration_allows(narration, source_text):
    """True when the narration names the person the source shows.

    The source has to name a person and the narration has to name the
    same one. A source that names nobody gives no allowance, so a
    stranger who speaks to the camera is refused, and a person the
    narration never mentions is refused as well.
    """
    carried = named_person(source_text)
    if not carried:
        return False
    spoken = narration_names(narration)
    if not spoken:
        return False
    return bool(carried & spoken)
