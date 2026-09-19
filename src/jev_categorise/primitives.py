"""Typed System One primitives.

Jev does not generate text; it evaluates *typed questions* against a *state* and
returns typed answers. These small dataclasses serialise to the wire format of
``POST /v1/systemone``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Choice:
    """Pick one option from a set (returns ``choice`` + ``probabilities``)."""

    instructions: str
    criteria: dict[str, str]
    type: str = field(default="choice", init=False)

    def to_wire(self) -> dict[str, Any]:
        return {"type": self.type, "instructions": self.instructions,
                "criteria": self.criteria}


@dataclass
class Score:
    """Rate the state on ordered, descriptive levels (returns ``score``)."""

    instructions: str
    criteria: list[str]
    type: str = field(default="score", init=False)

    def to_wire(self) -> dict[str, Any]:
        return {"type": self.type, "instructions": self.instructions,
                "criteria": self.criteria}


@dataclass
class Noul:
    """Ask a yes/no question (returns the probability ``noul``)."""

    instructions: str
    type: str = field(default="noul", init=False)

    def to_wire(self) -> dict[str, Any]:
        return {"type": self.type, "instructions": self.instructions}
