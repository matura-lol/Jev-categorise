"""The cross-subject taxonomies Jev classifies against.

The *dział* (topic) list is per subject and supplied by the caller (on
matura.lol it is extracted from the official CKE informatory — see the
``informator_topics.py`` extractor). Everything else here is subject-agnostic:
how a task is solved, the answer form, capability flags, bloom level and the
time bands.
"""

from __future__ import annotations

import json
from pathlib import Path

#: Difficulty levels, easiest first; the Score index maps onto this legend.
DIFFICULTY_LABELS = ("bardzo łatwe", "łatwe", "średnie", "trudne", "bardzo trudne")

#: How a task is solved, independent of subject — the grouping backbone.
METHODS: dict[str, str] = {
    "rachunek": "obliczenia, przekształcenia algebraiczne, wyznaczanie wartości",
    "dowod": "dowód lub uzasadnienie matematyczne/logiczne",
    "analiza_zrodla": "analiza tekstu, źródła historycznego lub literackiego",
    "interpretacja_danych": "odczyt i interpretacja wykresu, tabeli, danych",
    "doswiadczenie": "opis doświadczenia, obserwacji, eksperymentu",
    "rysunek_techniczny": "projekt, schemat, rysunek techniczny, konstrukcja",
    "algorytm": "algorytm, programowanie, pseudokod, złożoność",
    "wypowiedz": "wypowiedź pisemna, rozprawka, list, esej",
    "gramatyka": "gramatyka, składnia, słownictwo, tłumaczenie",
    "fakty": "odtworzenie wiedzy faktograficznej, nazwy, daty, definicje",
    "inne": "żadna z powyższych metod",
}

#: Expected answer form.
ANSWER_FORMS: dict[str, str] = {
    "liczba": "liczba lub wynik liczbowy",
    "wyrazenie": "wyrażenie, wzór lub równanie",
    "wybor": "wybór jednej z podanych odpowiedzi (A/B/C/D)",
    "prawda_falsz": "prawda/fałsz lub tak/nie",
    "krotka_odpowiedz": "krótka odpowiedź tekstowa (słowo, zdanie)",
    "wypracowanie": "dłuższa wypowiedź pisemna",
    "dowod": "dowód lub pełne uzasadnienie",
    "rysunek": "rysunek, wykres lub schemat",
    "kod": "kod, pseudokod lub algorytm",
    "inne": "żadna z powyższych form",
}

#: Noul capability flags — each is one vector dimension.
CAPABILITIES: dict[str, str] = {
    "wymaga_rachunku": "Czy do rozwiązania potrzebne są obliczenia lub przekształcenia?",
    "wymaga_dowodu": "Czy trzeba przeprowadzić dowód lub pełne uzasadnienie?",
    "wymaga_analizy_tekstu": "Czy trzeba przeanalizować tekst lub źródło?",
    "wymaga_interpretacji_danych": (
        "Czy trzeba odczytać lub zinterpretować wykres, tabelę lub dane?"
    ),
    "wymaga_doswiadczenia": "Czy zadanie dotyczy doświadczenia, obserwacji lub eksperymentu?",
    "wymaga_programowania": "Czy trzeba napisać lub przeanalizować algorytm/kod?",
    "wymaga_wiedzy_faktograficznej": (
        "Czy trzeba przypomnieć sobie konkretne fakty, daty, nazwy lub definicje?"
    ),
    "wymaga_rysunku": "Czy potrzebny jest rysunek, wykres lub schemat?",
    "wymaga_wyjasnienia": "Czy trzeba coś wyjaśnić lub opisać słowami?",
    "wymaga_pojec": "Czy kluczowa jest znajomość i rozumienie pojęć?",
}

#: Jev bloom level (Choice index order).
BLOOM = ("zapamiętanie", "zrozumienie", "zastosowanie", "analiza", "ocena i tworzenie")
#: Jev estimated-time Score index -> band label.
TIME_BANDS = ("do 2 min", "3-5 min", "6-10 min", "11-20 min", "powyżej 20 min")

#: The Choice criteria for the bloom question.
BLOOM_CRITERIA = {
    "zapamiętanie": "przypomnienie faktu, daty, definicji, wzoru",
    "zrozumienie": "wyjaśnienie, opis, interpretacja pojęcia",
    "zastosowanie": "użycie znanej metody lub wzoru do obliczenia",
    "analiza": "rozłożenie problemu, wnioskowanie, dowodzenie",
    "ocena": "ocena, uzasadnienie stanowiska, tworzenie rozwiązania",
}

#: Vector layout: methods, then forms, then capabilities, then difficulty.
VECTOR_DIMS = len(METHODS) + len(ANSWER_FORMS) + len(CAPABILITIES) + 1


def load_topics(path: str | Path) -> dict[str, list[str]]:
    """Load a ``subject -> [dział, …]`` JSON taxonomy (e.g. from informatory)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def topic_criteria(labels: list[str]) -> dict[str, str]:
    """Build the Choice criteria for a dział list (label -> short hint)."""
    return {**{label: label for label in labels},
            "inne": "żadna z powyższych kategorii"}
