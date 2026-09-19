"""The tagging pipeline: state → typed questions → parsed tag → vector/group."""

from __future__ import annotations

from typing import Any

from .client import JevClient
from .primitives import Choice, Noul, Score
from .taxonomy import (
    ANSWER_FORMS,
    BLOOM_CRITERIA,
    CAPABILITIES,
    DIFFICULTY_LABELS,
    METHODS,
)
from .vectors import capability_vector, group_of


def build_state(question: dict[str, Any]) -> dict[str, Any]:
    """The Jev *state*: the task plus just enough context to locate it."""
    return {
        "przedmiot": question.get("subject"),
        "poziom": question.get("level"),
        "kategoria": question.get("category"),
        "punkty": question.get("points"),
        "zadanie": (question.get("text") or "")[:6000],
    }


def build_questions(criteria: dict[str, str]) -> dict[str, Any]:
    """The ~14 typed questions asked for one state.

    *criteria* is the subject's dział taxonomy (label -> hint), typically the
    official list extracted from the CKE informatory.
    """
    questions: dict[str, Any] = {
        "dzial": Choice(
            "Do którego działu należy to zadanie? Wybierz najlepiej pasujący.",
            criteria),
        "trudnosc": Score(
            "Jak trudne jest to zadanie dla przeciętnego ucznia zdającego ten egzamin?",
            list(DIFFICULTY_LABELS)),
        "metoda": Choice("Jak przede wszystkim rozwiązuje się to zadanie?", METHODS),
        "forma": Choice("Jakiej formy odpowiedzi wymaga to zadanie?", ANSWER_FORMS),
        "poziom_bloom": Choice(
            "Który poziom myślenia najlepiej opisuje to zadanie?", BLOOM_CRITERIA),
        "czas": Score("Ile czasu potrzebuje przeciętny uczeń na to zadanie?",
                      ["do 2 minut", "3-5 minut", "6-10 minut", "11-20 minut",
                       "powyżej 20 minut"]),
        "wymaga_tablic": Noul(
            "Czy do rozwiązania potrzebne są tablice/wzory (karta wzorów)?"),
        "wymaga_kalkulatora": Noul(
            "Czy do rozwiązania potrzebny jest kalkulator?"),
        "zgodny_przedmiot": Noul("Czy to zadanie dotyczy właściwego przedmiotu?"),
    }
    for name, instruction in CAPABILITIES.items():
        questions[name] = Noul(instruction)
    return questions


def parse_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """Flatten Jev's typed answers into a compact tag record."""
    tag: dict[str, Any] = {}
    dzial = answers.get("dzial") or {}
    if dzial.get("choice"):
        tag["topic"] = dzial["choice"]
        tag["topic_confidence"] = dzial.get("confidence")
        tag["topic_probs"] = dzial.get("probabilities")
    trudnosc = answers.get("trudnosc") or {}
    if trudnosc.get("score") is not None:
        level = max(0, min(len(DIFFICULTY_LABELS) - 1, round(float(trudnosc["score"]))))
        tag["difficulty"] = level
        tag["difficulty_label"] = DIFFICULTY_LABELS[level]
        tag["difficulty_confidence"] = trudnosc.get("confidence")
    metoda = answers.get("metoda") or {}
    if metoda.get("choice"):
        tag["method"] = metoda["choice"]
        tag["method_probs"] = metoda.get("probabilities")
    forma = answers.get("forma") or {}
    if forma.get("choice"):
        tag["answer_form"] = forma["choice"]
        tag["form_probs"] = forma.get("probabilities")
    caps: dict[str, float] = {}
    for name in CAPABILITIES:
        value = (answers.get(name) or {}).get("noul")
        if value is not None:
            caps[name] = value
    if caps:
        tag["capabilities"] = caps
        if "wymaga_rysunku" in caps:
            tag["visual"] = caps["wymaga_rysunku"]
    bloom = answers.get("poziom_bloom") or {}
    if bloom.get("choice"):
        from .taxonomy import BLOOM
        tag["bloom"] = BLOOM.index(bloom["choice"]) if bloom["choice"] in BLOOM else None
    czas = answers.get("czas") or {}
    if czas.get("score") is not None:
        tag["time_band"] = max(0, min(4, round(float(czas["score"]))))
    tablice = answers.get("wymaga_tablic") or {}
    if tablice.get("noul") is not None:
        tag["needs_formula_sheet"] = tablice["noul"]
    kalkulator = answers.get("wymaga_kalkulatora") or {}
    if kalkulator.get("noul") is not None:
        tag["needs_calculator"] = kalkulator["noul"]
    przedmiot = answers.get("zgodny_przedmiot") or {}
    if przedmiot.get("noul") is not None:
        tag["subject_ok"] = przedmiot["noul"]
    return tag


def tag_question(client: JevClient, question: dict[str, Any],
                 criteria: dict[str, str]) -> dict[str, Any]:
    """Ask Jev about one question and attach the vector + group."""
    response = client.system_one(
        state=build_state(question),
        questions=build_questions(criteria),
    )
    tag = parse_answers(response.get("answers") or {})
    tag["id"] = question.get("id")
    tag["subject"] = question.get("subject")
    tag["model"] = response.get("model", client.model)
    tag["input_tokens"] = (response.get("usage") or {}).get("input_tokens")
    tag["vector"] = capability_vector(tag)
    gid, label = group_of(tag, question.get("subject"))
    tag["group_id"] = gid
    tag["group_label"] = label
    return tag
