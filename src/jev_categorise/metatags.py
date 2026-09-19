"""Hidden meta-tags: machine-only labels that sharpen search and grouping.

These never appear in a UI. They enrich a searchable metadata field so a query
like "zadania na dowodzenie" or "wymaga tablic" reaches the right tasks even
when those words are absent from the task text, and they give the group
signature more signal. Two sources:

* deterministic regexes over the task text (command verb, data representation);
* the Jev tag record (bloom, time band, whether the formula sheet / a calculator
  is needed).
"""

from __future__ import annotations

import re
from typing import Any

from .taxonomy import BLOOM, TIME_BANDS

_COMMANDS: tuple[tuple[str, str], ...] = (
    ("dowod", r"\b(?:wykaż|udowodni|dowiedź|dowodz)"),
    ("uzasadnij", r"\buzasadni"),
    ("oblicz", r"\boblicz"),
    ("wyznacz", r"\bwyznacz"),
    ("rozwiaz", r"\brozwiąż|\brozwiaz"),
    ("uzupelnij", r"\buzupełni"),
    ("zapisz", r"\bzapisz"),
    ("podaj", r"\bpodaj"),
    ("okresl", r"\bokreśl"),
    ("wybierz", r"\bwybierz|\bzaznacz"),
    ("ocen", r"\boceń|\bocen"),
    ("porownaj", r"\bporówna"),
    ("opis", r"\bopisz|\bopisa"),
    ("wyjasnij", r"\bwyjaśni"),
    ("scharakteryzuj", r"\bscharakteryzuj"),
    ("narysuj", r"\bnarysuj|\bsporządź|\bnaszkicuj"),
    ("przeksztalc", r"\bprzekształ"),
)
_REPRESENTATIONS: tuple[tuple[str, str], ...] = (
    ("wykres", r"\bwykres"),
    ("tabela", r"\btabel|\btab\.|dane w tabeli"),
    ("rysunek", r"\brysun|\brzynsun|\brvsunek|\brys\."),
    ("schemat", r"\bschemat"),
    ("wzor", r"\bwzór|\bwzory|\bwzoru"),
    ("uklad wspolrzednych", r"układ(?:zie)? współrzędnych|współrzędn"),
    ("mapa", r"\bmapa\b|\bmapie\b|\bmapka\b"),
    ("diagram", r"\bdiagram"),
    ("zdjecie", r"\bzdjęc|\bfotograf"),
)
_COMMAND_RE = tuple((tag, re.compile(pat)) for tag, pat in _COMMANDS)
_REPR_RE = tuple((tag, re.compile(pat)) for tag, pat in _REPRESENTATIONS)


def deterministic(text: str | None) -> list[str]:
    """Command-verb and representation tags derived from the task text."""
    if not text or len(text) < 4:
        return []
    low = text.lower()
    tags = [tag for tag, pattern in _COMMAND_RE if pattern.search(low)]
    tags += [tag for tag, pattern in _REPR_RE if pattern.search(low)]
    return tags


def from_tag(tag: dict[str, Any]) -> list[str]:
    """Hidden tags carried by a Jev tag record (bloom/time/tools)."""
    tags: list[str] = []
    bloom = tag.get("bloom")
    if isinstance(bloom, int) and 0 <= bloom < len(BLOOM):
        tags.append(BLOOM[bloom].replace(" i ", " "))
    band = tag.get("time_band")
    if isinstance(band, int) and 0 <= band < len(TIME_BANDS):
        tags.append("czas " + TIME_BANDS[band].replace("-", " "))
    if (tag.get("needs_formula_sheet") or 0) >= 0.5:
        tags.append("tablice")
    if (tag.get("needs_calculator") or 0) >= 0.5:
        tags.append("kalkulator")
    return tags


def merge(*groups: list[str]) -> list[str]:
    """Union several tag lists, preserving order and dropping duplicates."""
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for tag in group:
            if tag and tag not in seen:
                seen.add(tag)
                out.append(tag)
    return out
