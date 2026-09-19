"""Capability vectors and stable problem groups.

Jev's answers are turned into a fixed-length numeric vector (method probability
mass + answer-form mass + capability probabilities + normalised difficulty) and
a discrete signature ``topic · method · difficulty · capability bits``. The
signature is the grouping key: questions that share it are solved the same way.
"""

from __future__ import annotations

import re
from typing import Any

from .taxonomy import (
    ANSWER_FORMS,
    CAPABILITIES,
    DIFFICULTY_LABELS,
    METHODS,
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def capability_vector(tag: dict[str, Any]) -> list[float]:
    """The stored capability/solution vector for a parsed Jev tag."""
    method_probs = tag.get("method_probs") or {}
    form_probs = tag.get("form_probs") or {}
    caps = tag.get("capabilities") or {}
    vec = [float(method_probs.get(name, 0.0)) for name in METHODS]
    vec += [float(form_probs.get(name, 0.0)) for name in ANSWER_FORMS]
    vec += [float(caps.get(name, 0.0)) for name in CAPABILITIES]
    vec.append((tag.get("difficulty") or 0) / max(1, len(DIFFICULTY_LABELS) - 1))
    return [round(v, 4) for v in vec]


def _slug(text: str, width: int = 40) -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:width].strip("-")


def capability_bits(caps: dict[str, float], threshold: float = 0.6) -> int:
    """Capability probabilities above *threshold* as a bitmask."""
    bits = 0
    for i, name in enumerate(CAPABILITIES):
        if caps.get(name, 0.0) >= threshold:
            bits |= 1 << i
    return bits


def group_of(tag: dict[str, Any], subject: str | None) -> tuple[str, str]:
    """Stable ``(group_id, label)`` from the discrete Jev signature."""
    topic = tag.get("topic") or "inne"
    method = tag.get("method") or "inne"
    level = int(tag.get("difficulty") or 0)
    bits = capability_bits(tag.get("capabilities") or {})
    gid = (f"{_slug(subject or 'inne', 24)}/{_slug(topic)}/{_slug(method)}/"
           f"{level}/{bits:x}")
    label = f"{topic} · {method} · {DIFFICULTY_LABELS[level]}"
    return gid, label
