"""Jev categoriser — classify and group exam questions with TypeSafe Jev.

The package turns a question into a rich, typed record: the official subject
dział (Choice), difficulty (Score), how it is solved (Choice), the answer form
(Choice), bloom level (Choice), estimated time (Score) and a set of capability /
tool flags (Noul). Those answers become a capability vector and a stable
``group_id`` so questions can be searched and grouped by *how* they are solved,
not only by their text.
"""

from __future__ import annotations

from .client import JevClient, JevError
from .metatags import deterministic as meta_tags_from_text
from .pipeline import build_questions, build_state, parse_answers, tag_question
from .primitives import Choice, Noul, Score
from .taxonomy import (
    ANSWER_FORMS,
    BLOOM,
    CAPABILITIES,
    DIFFICULTY_LABELS,
    METHODS,
    TIME_BANDS,
)
from .vectors import capability_vector, group_of

__all__ = [
    "ANSWER_FORMS",
    "BLOOM",
    "CAPABILITIES",
    "DIFFICULTY_LABELS",
    "METHODS",
    "TIME_BANDS",
    "Choice",
    "JevClient",
    "JevError",
    "Noul",
    "Score",
    "build_questions",
    "build_state",
    "capability_vector",
    "group_of",
    "meta_tags_from_text",
    "parse_answers",
    "tag_question",
]
