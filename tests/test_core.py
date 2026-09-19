"""Offline unit tests — no network, no API key required."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jev_categorise import metatags, parse_answers, tag_question
from jev_categorise.pipeline import build_questions
from jev_categorise.taxonomy import (
    CAPABILITIES,
    VECTOR_DIMS,
    load_topics,
    topic_criteria,
)
from jev_categorise.vectors import capability_vector, group_of

ANSWERS = {
    "dzial": {"type": "choice", "choice": "Funkcje", "confidence": 0.9,
              "probabilities": {"Funkcje": 0.9, "inne": 0.1}},
    "trudnosc": {"type": "score", "score": 3.4, "confidence": 0.7},
    "metoda": {"type": "choice", "choice": "rachunek",
               "probabilities": {"rachunek": 1.0}},
    "forma": {"type": "choice", "choice": "liczba",
              "probabilities": {"liczba": 1.0}},
    "poziom_bloom": {"type": "choice", "choice": "analiza"},
    "czas": {"type": "score", "score": 0.2},
    "wymaga_tablic": {"type": "noul", "noul": 0.9},
    "wymaga_kalkulatora": {"type": "noul", "noul": 0.1},
    "wymaga_rachunku": {"type": "noul", "noul": 0.97},
    "wymaga_rysunku": {"type": "noul", "noul": 0.2},
    "zgodny_przedmiot": {"type": "noul", "noul": 0.99},
}


def test_parse_answers_maps_every_primitive():
    tag = parse_answers(ANSWERS)
    assert tag["topic"] == "Funkcje"
    assert tag["difficulty"] == 3 and tag["difficulty_label"] == "trudne"
    assert tag["method"] == "rachunek"
    assert tag["answer_form"] == "liczba"
    assert tag["bloom"] == 3
    assert tag["time_band"] == 0
    assert tag["needs_formula_sheet"] == 0.9
    assert tag["capabilities"]["wymaga_rachunku"] == 0.97
    assert tag["visual"] == 0.2


def test_capability_vector_shape_and_difficulty():
    tag = parse_answers(ANSWERS)
    vec = capability_vector(tag)
    assert len(vec) == VECTOR_DIMS
    assert vec[-1] == 0.75  # difficulty 3 / 4
    assert max(vec) <= 1.0


def test_group_is_stable_and_capability_sensitive():
    base = parse_answers({**ANSWERS, "wymaga_rachunku": {"type": "noul", "noul": 0.9}})
    same = parse_answers({**ANSWERS, "wymaga_rachunku": {"type": "noul", "noul": 0.8}})
    other = parse_answers({**ANSWERS, "metoda": {"type": "choice", "choice": "dowod"}})
    gid, label = group_of(base, "matematyka")
    assert group_of(same, "matematyka")[0] == gid
    assert group_of(other, "matematyka")[0] != gid
    assert "Funkcje" in label and "rachunek" in label


def test_build_questions_is_typed_and_well_formed():
    questions = build_questions(topic_criteria(["Funkcje", "Planimetria"]))
    assert questions["dzial"].to_wire()["type"] == "choice"
    assert questions["trudnosc"].to_wire()["type"] == "score"
    assert questions["wymaga_rachunku"].to_wire()["type"] == "noul"
    assert "inne" in questions["dzial"].to_wire()["criteria"]
    for name in CAPABILITIES:
        assert name in questions


def test_metatags_command_representation_and_hidden():
    tags = metatags.deterministic("Wykaż, że liczba jest podzielna przez 3. Narysuj wykres.")
    assert "dowod" in tags and "narysuj" in tags and "wykres" in tags
    hidden = metatags.from_tag({"bloom": 3, "time_band": 2,
                                "needs_formula_sheet": 0.9, "needs_calculator": 0.1})
    assert "analiza" in hidden and "tablice" in hidden and "kalkulator" not in hidden
    assert metatags.merge(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_tag_question_uses_injected_client():
    class FakeClient:
        model = "jev-test"

        def system_one(self, state, questions):
            assert state["zadanie"].startswith("Zapisz")
            assert "dzial" in questions
            return {"model": "jev-test", "answers": ANSWERS, "usage": {"input_tokens": 10}}

    tag = tag_question(FakeClient(), {"id": "x", "subject": "matematyka",
                                      "text": "Zapisz przedział."},
                       topic_criteria(["Funkcje"]))
    assert tag["id"] == "x" and tag["group_id"] and len(tag["vector"]) == VECTOR_DIMS


def test_load_topics_reads_subject_map(tmp_path):
    path = tmp_path / "topics.json"
    path.write_text('{"matematyka": ["Funkcje"]}', encoding="utf-8")
    assert load_topics(path) == {"matematyka": ["Funkcje"]}
