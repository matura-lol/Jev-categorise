"""Tag one exam question with Jev and print the result.

    JEV_API_KEY=... python examples/tag_one.py
"""

from __future__ import annotations

import json
import os

from jev_categorise import JevClient, tag_question, topic_criteria

QUESTION = {
    "id": "matematyka-2023-maj-pp/zad/19.2",
    "subject": "matematyka",
    "level": "podstawowa",
    "category": "matura",
    "points": 1,
    "text": (
        "Zapisz w miejscu wykropkowanym maksymalny przedział lub maksymalne "
        "przedziały, w których funkcja f jest malejąca."
    ),
}

# The official, closed set of działy for the subject. On matura.lol this is
# extracted from the CKE informatory; here we pass a short list for the example.
CRITERIA = topic_criteria([
    "Liczby rzeczywiste", "Wyrażenia algebraiczne", "Równania i nierówności",
    "Funkcje", "Ciągi", "Trygonometria", "Planimetria",
    "Geometria analityczna", "Stereometria", "Kombinatoryka",
    "Rachunek prawdopodobieństwa i statystyka",
])


def main() -> int:
    client = JevClient(api_key=os.environ.get("JEV_API_KEY"))
    tag = tag_question(client, QUESTION, CRITERIA)
    print(json.dumps(tag, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
