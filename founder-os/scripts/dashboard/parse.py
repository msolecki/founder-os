"""Pure text-to-value functions. No filesystem, no clock, no I/O.

Every function here refuses to guess. An unreadable amount keeps its raw text and
carries no number; a date that is not ISO is not a date. The caller decides what
to show; this module never invents a value it can present confidently.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple


_MONEY = re.compile(
    r"(?P<symbol>[$€£¥]|(?<![A-Za-z])[A-Z]{3}(?=\s|\d))?\s*"
    r"(?P<number>\d[\d,  ]*(?:\.\d+)?)")
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


def parse_money(raw: Optional[str]) -> Value:
    text = (raw or "").strip()
    if not text:
        return Value(raw=text, number=None, currency=None)
    match = _MONEY.search(text)
    if match is None:
        return Value(raw=text, number=None, currency=None)
    digits = re.sub(r"[,  ]", "", match.group("number"))
    try:
        number = float(digits)
    except ValueError:
        return Value(raw=text, number=None, currency=None)
    symbol = (match.group("symbol") or "").strip() or None
    return Value(raw=text, number=number, currency=symbol)


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


def split_entries(body: Optional[str]) -> Tuple[Entry, ...]:
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

    chunks = []
    current = None
    for line in text.splitlines():
        if _BULLET.match(line):
            if current is not None:
                chunks.append(current)
            current = [_BULLET.sub("", line).strip()]
        elif current is not None and line.strip():
            current.append(line.strip())
    if current is not None:
        chunks.append(current)
    return tuple(
        Entry(title=chunk[0], body=" ".join(chunk[1:])) for chunk in chunks)
