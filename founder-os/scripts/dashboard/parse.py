"""Pure text-to-value functions. No filesystem, no clock, no I/O.

Every function here refuses to guess. An unreadable amount keeps its raw text and
carries no number; a date that is not ISO is not a date; a section written as
prose is not an empty section. The caller decides what to show; this module never
invents a value it can present confidently.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple


# A thousands separator is written as a space at least as often as a comma, and a
# spreadsheet paste leaves a non-breaking one behind.
_SPACES = " \u00a0\u202f\u2009"

# Between a marker and its amount the founder's whitespace is their own: an extra
# space or a tab still means "this is the currency of this number". Inside a
# number a separator is a single character, which is why the two classes differ.
_GAPS = _SPACES + "\t"

_MARKERS = ("zł", "$", "€", "£", "¥")

# The ISO 4217 codes this product reads as money, and nothing else. Shape is not
# evidence: a bare uppercase triple in a founder's prose is an acronym far more
# often than a currency — "3 NDA rounds", "5 API keys", "4 QBR sessions" — and
# analyze reads an entry's heading as its amount precisely when parse_money found
# a currency, so a guessed code puts both an invented total and an invented unit
# on the page and into the snapshot CSV. A code missing from this list costs a
# label, never a number: the amount still reads and the panel reports that no
# currency was recorded. Extend the list; do not widen the shape.
_CURRENCIES = ("AUD", "CAD", "CHF", "CZK", "DKK", "EUR", "GBP", "HUF", "JPY",
               "NOK", "NZD", "PLN", "RON", "SEK", "USD")

_SIGNS = "-\u2212"
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_H3 = re.compile(r"^###\s+", re.M)
_BULLET = re.compile(r"^\s*[-*]\s+")
_DECLARED_EMPTY = {"none", "none."}


@dataclass(frozen=True)
class Value:
    raw: str
    number: Optional[float]
    currency: Optional[str]


@dataclass(frozen=True)
class Entry:
    title: str
    body: str


def _grouped(digits: str, separator: str) -> bool:
    parts = digits.split(separator)
    if len(parts) == 1:
        return True
    return 1 <= len(parts[0]) <= 3 and all(len(part) == 3 for part in parts[1:])


def _read_number(token: str) -> Optional[float]:
    """Decide what the separators in a number mean, or refuse to decide.

    A comma is a thousands separator to one founder and a decimal point to the
    next, and the same is true of a dot, so the shape of the groups has to settle
    it: three digits after the separator is a group, one or two is a fraction.
    "18.000" satisfies both readings at once — 18000 in Warsaw, 18.0 in Chicago —
    and there is nothing in the text to break the tie, so it is not read at all.
    An amount the page prints as "not recorded" costs the founder a lookup; one
    that is wrong by a factor of a thousand costs them a decision.
    """
    compact = "".join(char for char in token if char not in _SPACES)
    if "," in compact and "." in compact:
        decimal = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        head, _, fraction = compact.rpartition(decimal)
        if decimal in head or not _grouped(head, thousands):
            return None
        if not 1 <= len(fraction) <= 2:
            return None
        return float(head.replace(thousands, "") + "." + fraction)
    for separator in (",", "."):
        if separator not in compact:
            continue
        parts = compact.split(separator)
        if _grouped(compact, separator):
            if len(parts) == 2 and separator == ".":
                return None
            return float("".join(parts))
        if len(parts) == 2 and 1 <= len(parts[1]) <= 2:
            return float(parts[0] + "." + parts[1])
        return None
    return float(compact)


def _digits_at(text: str, index: int) -> int:
    """The index one past the run of digits starting at `index`."""
    end = index
    while end < len(text) and text[end].isdigit():
        end += 1
    return end


def _scan_token(text: str, start: int) -> Tuple[int, bool]:
    """Consume the whole numeric token at `start`; report a dangling digit run.

    This is a scanner rather than a regular expression because the two jobs a
    number pattern has here — find where the token ends, and judge whether what
    it found is readable — pull in opposite directions, and every attempt to make
    one pattern do both has failed the same way. A trailing assertion that
    refuses a token cut short also refuses "$18,000 3 calls", and the engine then
    slides forward and reads the prose: the amount is discarded and "3" is
    reported in its place. Worse, "100 00" has no match the assertion accepts, so
    the search lands on "00" and the page states a confident zero for a number
    the founder did write. A scanner can stop where the token stops and say
    separately that it did not like what came next.

    A space is a thousands separator only in a group of exactly three digits
    whose head is one to three digits — "15 000" is fifteen thousand, "1234 567"
    is two numbers and "100 00" is a typo. `dangling` reports that a digit run
    follows the token across whitespace, which is the shape all three of those
    share and the caller's signal that the text is ambiguous.
    """
    end = _digits_at(text, start)
    groupable = 1 <= end - start <= 3
    while True:
        if (end + 1 < len(text) and text[end] in ".,"
                and text[end + 1].isdigit()):
            end = _digits_at(text, end + 1)
            groupable = False
            continue
        if groupable and end < len(text) and text[end] in _SPACES:
            group_end = _digits_at(text, end + 1)
            if (group_end - (end + 1) == 3
                    and (group_end >= len(text)
                         or not text[group_end].isdigit())):
                end = group_end
                continue
        break
    trailer = end
    while trailer < len(text) and text[trailer] in _SPACES:
        trailer += 1
    dangling = trailer > end and trailer < len(text) and text[trailer].isdigit()
    return end, dangling


def _marker_before(text: str, index: int) -> Tuple[Optional[str], int]:
    """The currency written immediately before `index`, and where it starts."""
    cursor = index
    while cursor > 0 and text[cursor - 1] in _GAPS:
        cursor -= 1
    for marker in _MARKERS:
        if text[:cursor].endswith(marker):
            return marker, cursor - len(marker)
    for code in _CURRENCIES:
        start = cursor - len(code)
        if start >= 0 and text[start:cursor] == code:
            if start == 0 or not text[start - 1].isalpha():
                return code, start
    return None, index


def _marker_after(text: str, index: int) -> Tuple[Optional[str], int]:
    """The currency written immediately after `index`, and where it ends."""
    cursor = index
    while cursor < len(text) and text[cursor] in _GAPS:
        cursor += 1
    for marker in _MARKERS:
        if text.startswith(marker, cursor):
            return marker, cursor + len(marker)
    for code in _CURRENCIES:
        end = cursor + len(code)
        if text[cursor:end] == code:
            # "PLNs" is a plural, not a currency, and neither is "PLN-indexed".
            if end >= len(text) or not (text[end].isalpha() or text[end] == "-"):
                return code, end
    return None, index


def _glued(text: str, index: int, step: int) -> bool:
    """Is the character on this side of a run part of the same word or number?

    A run of digits is an amount only when nothing is welded to it. "2026-08-15"
    is a date, "q-0717b" is a queue id, "3-5" is a range and "18k" is shorthand,
    and each used to parse as money because a search takes the leftmost digits it
    can find. Punctuation is the awkward part: a hyphen is a minus at the head of
    a value and a joiner everywhere else, and a comma holds "1,234" together but
    merely separates "4, 3, 3, 2". Both are judged by what sits on their far
    side, so a separator between digits welds and one before a space does not.
    """
    if not 0 <= index < len(text):
        return False
    char = text[index]
    if char.isalnum():
        return True
    neighbour = index + step
    if not 0 <= neighbour < len(text):
        return False
    if char in ".,":
        return text[neighbour].isdigit()
    if char in _SIGNS:
        return text[neighbour].isalnum()
    return False


def parse_money(raw: Optional[str]) -> Value:
    """Read the first amount in the text, or report that there is none.

    The currency is whichever marker was written against that amount, before it
    ("$18,000") or after it ("15 000 PLN"), and a code counts only when it is one
    the module lists: an uppercase triple is not evidence of money. A currency of
    None means no marker was written, not that the amount is dollars: a caller
    adding amounts up must treat an unmarked number as a currency it does not
    know rather than as its own. A number of None means the text holds no amount
    this module can read — never that the amount is zero.

    The first candidate settles it, and a candidate the module cannot read
    settles it as "no amount". Sliding on to a later run is what turns a stated
    price into whatever number the sentence mentions next, so a run welded into a
    date or an id is skipped before it is ever a candidate, and one that is a
    real candidate is answered rather than abandoned.
    """
    text = (raw or "").strip()
    index = 0
    while index < len(text):
        if not text[index].isdigit():
            index += 1
            continue
        if _glued(text, index - 1, -1):
            index = _digits_at(text, index)
            continue
        end, dangling = _scan_token(text, index)
        prefix, prefix_start = _marker_before(text, index)
        suffix, suffix_end = _marker_after(text, end)
        if _glued(text, suffix_end, 1):
            index = _digits_at(text, index)
            continue

        # A number the founder wrote with a marker against it is an amount even
        # when prose follows; one written bare with a stray digit run after it is
        # a number this module cannot delimit, and guessing which half is the
        # amount is how "100 00" became a confident zero.
        if dangling and prefix is None and suffix is None:
            return Value(raw=text, number=None, currency=None)

        number = _read_number(text[index:end])
        if number is None:
            return Value(raw=text, number=None, currency=None)

        start = prefix_start
        sign = False
        cursor = start
        while cursor > 0 and text[cursor - 1] in _GAPS:
            cursor -= 1
        if cursor > 0 and text[cursor - 1] in _SIGNS:
            sign_at = cursor - 1
            before = sign_at
            while before > 0 and text[before - 1] in _GAPS:
                before -= 1
            # A minus welded to its value is always a sign. A detached one is a
            # sign only where a value begins — after a label's colon, inside
            # brackets, in a table cell — because everywhere else a spaced
            # hyphen is the separator a founder writes between the parts of a
            # heading. "Cash on hand: - 4,200" is an overdrawn account and
            # "Acme - $18,000" is a price, and the character before the dash is
            # the only thing in the text that tells them apart.
            if cursor == start or before == 0 or text[before - 1] in ":(|":
                start = sign_at
                sign = True

        # Accounting writes a negative as "(4,200)". The parentheses have to hold
        # the value and nothing else: "(11 months at current burn)" is a note and
        # "$24,000 (77%)" is an aside, and reading either as a sign reports a
        # figure written in the black as a debt.
        wrapped = (start > 0 and text[start - 1] == "("
                   and suffix_end < len(text) and text[suffix_end] == ")")
        if sign != wrapped:
            number = -number
        return Value(raw=text, number=number, currency=prefix or suffix)
    return Value(raw=text, number=None, currency=None)


def parse_iso_date(raw: Optional[str]) -> Optional[date]:
    match = _ISO.search(raw or "")
    if match is None:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def parse_field(body: Optional[str], label: str) -> Optional[str]:
    pattern = re.compile(r"^%s:[ \t]*(.+)$" % re.escape(label), re.M)
    match = pattern.search(body or "")
    if match is None:
        return None
    found = match.group(1).strip()
    return found or None


def is_declared_empty(body: Optional[str]) -> bool:
    return (body or "").strip().lower() in _DECLARED_EMPTY


def split_entries(body: Optional[str]) -> Optional[Tuple[Entry, ...]]:
    """The entries in a section, or None when the section cannot be read as one.

    Three outcomes, and the difference between the last two is the whole point of
    the return type being optional. A tuple is what the founder listed. An empty
    tuple is a section they left blank or wrote `None.` in, which is a real zero.
    None is a section holding content this module cannot turn into entries —
    prose where a list was expected — and it is not a zero at all.

    Collapsing those two was the most expensive defect in this package. A `##
    Live` section describing two deals in a sentence returned the same empty
    tuple as one saying `None.`, so every caller counted it as zero and the page
    published "live across 0 deals" over a citation to the file that names them,
    and wrote that zero into the append-only snapshot series. The published
    promise — "a value it could not read renders as not recorded, never as zero"
    — was false for as long as this function had one way of saying nothing.

    Optional rather than an exception, and Optional rather than a flag a caller
    can ignore: a caller that forgets None gets a TypeError from iterating it,
    which a test catches, instead of a plausible zero, which nothing catches.
    """
    text = body or ""
    if not text.strip() or is_declared_empty(text):
        return ()
    if _H3.search(text):
        blocks = _H3.split(text)[1:]
        entries = []
        for block in blocks:
            lines = block.splitlines()
            entries.append(
                Entry(title=lines[0].strip(),
                      body="\n".join(lines[1:]).strip()))
        return tuple(entries)

    # The first bullet sets the level of the list. A bullet only nests when it
    # reaches the content column of that first one — two columns in for "- ",
    # which is what CommonMark requires and what the founder sees rendered.
    # Counting a note written under an item as an item is what makes a queue of
    # three read as five; treating a typo'd single-space indent as a note is the
    # opposite error and hides an item over the cap. Tabs are the tab stops
    # CommonMark uses, so a tab indent is a note.
    chunks = []
    current = None
    outer = None
    for line in text.splitlines():
        expanded = line.expandtabs(4)
        indent = len(expanded) - len(expanded.lstrip())
        if _BULLET.match(line) and (outer is None or indent < outer + 2):
            outer = indent if outer is None else min(outer, indent)
            if current is not None:
                chunks.append(current)
            current = [_BULLET.sub("", line).strip()]
        elif current is not None and line.strip():
            current.append(_BULLET.sub("", line).strip())
    if current is not None:
        chunks.append(current)
    if not chunks:
        return None
    return tuple(
        Entry(title=chunk[0], body=" ".join(chunk[1:])) for chunk in chunks)
