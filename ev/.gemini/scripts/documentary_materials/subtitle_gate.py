"""Find the burned-in captions in a source, and cut them out.

The film carries its own captions. A source that carries an old
English caption in the picture has two sets of text on the same
frame, and the old one is wrong: it is a caption for a different
sentence. So the lower band of such a source is cut away.

The cut is only worth it when the caption is really there. The render
used to cut the lower 12 percent of every source, whether it carried
a caption or not, and threw away the picture of every archive shot
for nothing. So the band is measured first.
"""
from pathlib import Path

from . import resources


def _sample_band(path, start, duration, band=0.16, width=960):
    """Read the lower band of a few frames, as grayscale pictures.

    The band is read at 960 pixels wide. At 320 pixels a bright edge
    of concrete breaks into letter-like specks, and the picture of the
    archive and the picture of a caption look the same. At 960 the
    letters stay letters and the edge stays an edge.

    The second that is given is a local second of the file, the same
    one the render reads. It was converted from a source second a
    second time here, and for a fetched window that moved the sampled
    frames off the place the shot actually uses.
    """
    if not path or not Path(path).is_file():
        return []
    local = float(start)
    pictures = []
    for offset in (0.15, 0.5, 0.85):
        at = local + max(0.0, duration * offset)
        try:
            out = resources.media_run(
                ["ffmpeg", "-v", "error", "-ss", "%.2f" % at, "-i", str(path),
                 "-frames:v", "1", "-vf",
                 "crop=iw:floor(ih*%.2f):0:floor(ih*%.2f),scale=%d:-1,format=gray"
                 % (band, 1.0 - band, width),
                 "-f", "rawvideo", "-"],
                capture_output=True, timeout=45)
        except Exception:
            continue
        raw = out.stdout
        if len(raw) < width:
            continue
        pictures.append(raw)
    return pictures


def _white_share(picture, width=960):
    """How much of the band is near-white."""
    if not picture:
        return 0.0
    values = picture[:width * (len(picture) // width)]
    if not values:
        return 0.0
    return sum(1 for v in values if v >= 225) / float(len(values))


def _row_shape(line, width):
    """The shape of the near-white pixels of one row.

    Three numbers: how much of the row is near-white, how many
    separate pieces it is broken into, and how long the longest piece
    is. Letters are many short pieces. A white background is one long
    piece. A graphic stripe is one long piece in every row.
    """
    count = 0
    runs = 0
    longest = 0
    current = 0
    for value in line:
        if value >= 225:
            count += 1
            current += 1
            if current > longest:
                longest = current
        elif current:
            runs += 1
            current = 0
    if current:
        runs += 1
    return count, runs, longest


def _text_rows(picture, width=960):
    """The rows of this band that carry letters.

    A row counts as a text row when a fair part of it is near-white,
    the near-white is broken into many short pieces, and no single
    piece is long enough to be a bar or an edge. Measured on the real
    sources at 960 pixels: a caption row holds 40 to 90 separate
    near-white pieces, the longest of them 4 to 17 pixels. A title bar
    is two pieces of 750 and 861 pixels, and is out for that reason.
    A bright edge of concrete is 35 pieces, but it is only there in
    one of the sampled frames, so it is out for the frame rule.
    """
    if not picture:
        return []
    values = picture[:width * (len(picture) // width)]
    if not values or max(values) < 215:
        return []
    rows = []
    for r in range(len(values) // width):
        line = values[r * width:(r + 1) * width]
        count, runs, longest = _row_shape(line, width)
        if count < width * 0.05 or runs < 20 or longest > width * 0.04:
            continue
        rows.append((r, count / float(width)))
    return rows


def _caption_group(rows):
    """The group of text rows that sit on top of each other.

    A caption is a block of lines: the text of one line sits on the
    line above it. Rubble gives text rows that are scattered all over
    the band, so the longest run of rows that follow each other is
    what tells a caption from a bright background.
    """
    if not rows:
        return []
    best = []
    current = [rows[0]]
    for row in rows[1:]:
        if row[0] - current[-1][0] == 1:
            current.append(row)
            if len(current) > len(best):
                best = list(current)
        else:
            current = [row]
    return best


_SUBTITLE_CACHE = {}


def has_burned_in_subtitle(path, start=0.0, duration=1.0, threshold=0.04):
    """True when the source carries a burned-in caption in its lower band.

    The band is read a few times. A caption is a line of letters that
    holds its place in the frame while the picture behind it changes,
    so the frames that carry a text row have to agree on where that
    row is. Bright rubble and a graphic bar change from frame to
    frame, and a single frame that looks like text is not enough.
    """
    key = (str(path), round(float(start), 2), round(float(duration), 2))
    cached = _SUBTITLE_CACHE.get(key)
    if cached is not None:
        return cached
    pictures = _sample_band(path, start, duration)
    verdict = False
    if pictures:
        hits = []
        for picture in pictures:
            # A caption is a modest amount of white text on a picture
            # that is not itself white. Measured on the real sources: a
            # caption frame carries 4 to 5 percent near-white pixels, a
            # studio shot on a white backdrop carries 18 to 34 percent,
            # and a frame that blows out to white carries 90 percent.
            # A bright scene is not a caption, whatever its texture
            # looks like row by row.
            frac = _white_share(picture)
            if not 0.004 <= frac <= 0.35:
                continue
            group = _caption_group(_text_rows(picture))
            if len(group) < 3:
                continue
            if max(share for _, share in group) < threshold:
                continue
            hits.append(sum(r for r, _ in group) / float(len(group)))
        if len(hits) >= 2:
            verdict = True
    _SUBTITLE_CACHE[key] = verdict
    return verdict


