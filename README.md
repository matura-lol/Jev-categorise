# Jev-categorise

Classify and group exam questions with **[TypeSafe Jev](https://docs.typesafe.ai/introduction)** —
the first *System One* model. This repository extracts the Jev-only components of
the pipeline that powers **[matura.lol](https://matura.lol)**, a full-text search
engine over the Polish exam corpus (CKE matura, egzamin ósmoklasisty and
vocational arkusze).

Given one question, Jev returns a fully typed record — the official **dział**
(topic), **difficulty**, **solution method**, **answer form**, **bloom** level,
**estimated time**, capability flags and tool needs — with no text generation and
no parsing. Those answers are turned into a **capability vector** and a stable
**problem group**, so questions can be searched and grouped by *how they are
solved*, not only by their text.

```text
question ──▶ Jev (typed questions + state) ──▶ tag record ──▶ capability vector
                                                    │
                                                    └──▶ group_id  (topic · method ·
                                                                    difficulty · capability bits)
```

---

## Why Jev beats the previous approaches

matura.lol previously categorised tasks with three hand-rolled methods. Jev
replaces all of them at once, and adds things none of them could do:

| Approach | What it did | Why it fell short |
| --- | --- | --- |
| **Source labels** | Copy the publisher's tag | Covers ~13% of the corpus, and the labels are inconsistent: `analityczna` vs `geometria analityczna`, `rownania_i_nierownosci`, random casing, duplicated taxonomies across sources. |
| **Keyword rules** | Curated regex per subject, longest-match wins | Brittle: a `trójkąt` task in a physics context gets a maths dział; inflections must be enumerated; new subjects mean new rules; no confidence signal. |
| **TF-IDF centroid** | Mine a bag-of-words centroid from labelled rows | Needs a labelled seed set, produces a single guess with no probability, and struggles with short or OCR-damaged text. |
| **Generic LLM prompting** | Prompt a chat model for a label and parse the text | Non-deterministic output, needs fragile parsing, one broad question per call (context rot), and a text-generation model is the wrong tool for a decision your code must branch on. |

Jev is a better fit because it is **built for exactly this decision**:

1. **Typed, structured output — no parsing.** A `Choice` returns the chosen
   option *and* a full probability distribution; a `Score` returns a calibrated
   level; a `Noul` returns the probability that a statement is true. The code
   branches on values, never on scraped text.

2. **Calibrated probabilities and confidence.** Each answer carries
   `probabilities` and `confidence`, so low-confidence rows can be routed to
   review, gated, or re-asked — impossible with a keyword score or a single LLM
   label.

3. **Many atomic questions per call, evaluated in parallel.** One HTTP request
   carries ~14 questions (dział, difficulty, method, form, bloom, time, ten
   capability flags, subject check). Adding questions barely changes latency and,
   because each is evaluated in isolation, there is **no context rot** — the
   difficulty judgment cannot contaminate the topic judgment.

4. **A taxonomy we control, not one the model imagines.** The `Choice` criteria
   are the official list of działy extracted from the **CKE informatory**
   (`Wymaganie szczegółowe` headings). Jev picks from the real, closed set, so
   labels are consistent across every source and every year.

5. **Deterministic taxonomy, probabilistic edge.** The *criteria* are fixed, so
   results are reproducible and groupable; the *confidence* still tells you when
   a task is genuinely ambiguous.

6. **An answer-verification primitive.** The same model can be asked a `Noul`
   "does this stored answer/solution actually fit this task?", turning a
   classification model into a **data-quality signal** that flags mismatched
   keys and solutions.

7. **Cheap and fast enough to run over an entire corpus.** Jev is priced per
   **input token** (output tokens are free) and evaluates questions in parallel;
   tagging tens of thousands of questions costs a few dollars and runs
   unattended and resumable.

## What it produces

One JSON record per question (`tags.jsonl`):

```json
{
  "id": "informator-maturalny-matematyka-2023-poziom-podstawowy/zad/19.2",
  "subject": "matematyka",
  "topic": "Funkcje",
  "topic_confidence": 1.0,
  "topic_probs": {"Funkcje": 1.0, "Planimetria": 0.0, "...": 0.0},
  "difficulty": 2,
  "difficulty_label": "średnie",
  "method": "rachunek",
  "method_probs": {"rachunek": 1.0, "...": 0.0},
  "answer_form": "liczba",
  "capabilities": {"wymaga_rachunku": 0.98, "wymaga_rysunku": 0.08, "...": 0.0},
  "bloom": 3,
  "time_band": 0,
  "needs_formula_sheet": 0.2,
  "needs_calculator": 0.1,
  "visual": 0.08,
  "subject_ok": 0.99,
  "vector": [0.0, 1.0, "..."],           /* 32 dims */
  "group_id": "matematyka/funkcje/rachunek/2/1e",
  "group_label": "Funkcje · rachunek · średnie",
  "model": "jev-1.13",
  "input_tokens": 2612
}
```

* **`vector`** — method probability mass + answer-form mass + capability
  probabilities + normalised difficulty (`VECTOR_DIMS` = 32).
* **`group_id`** — the discrete signature `subject/topic/method/difficulty/capability-bits`.
  All questions with the same signature are solved the same way and become one
  *problem group*.
* **hidden meta-tags** — command verbs (`oblicz`, `wykaz`, `narysuj`) and data
  representations (`wykres`, `tabela`, `schemat`), plus Jev's bloom, time band,
  and `tablice`/`kalkulator` tool needs. Never shown in a UI; indexed so a
  query like *"zadania na dowodzenie"* or *"wymaga tablic"* reaches the right
  tasks even when the words are absent from the task text.

## Used on matura.lol

This code runs in the production pipeline behind **https://matura.lol**:

* `informator-import` extracts the official per-subject dział list from the CKE
  informatory into a JSON taxonomy.
* `jev-tag` tags every matura and egzamin ósmoklasisty question (~47k across
  16 subjects) into `tags.jsonl`, resumable and rate-limit aware.
* `load` folds the tags onto the corpus: Jev's dział wins over weak source
  labels, difficulty/method/answer-form become **facets and filters** (the
  search UI gets a "Trudność" and "Sposób" select), the capability vector and
  `group_id` power **"related problems"**, and hidden meta-tags widen the
  metadata search vector.
* `jev-check` asks Jev whether each stored answer/solution fits its task and
  writes low-confidence rows to a **mismatch ledger** for review.

The net effect on matura.lol: topic coverage goes from ~13% of questions to
essentially all of them, labels become consistent with the official taxonomy,
and search gains difficulty/method filters plus genuine "solve-it-the-same-way"
problem groups.

## Install

```bash
pip install -e .            # or: uv run --project . python ...
```

No runtime dependencies — the client uses the standard library.

## Quick start

```python
import os
from jev_categorise import JevClient, tag_question, topic_criteria

client = JevClient(api_key=os.environ["JEV_API_KEY"])   # model defaults to jev-1.13

question = {
    "id": "matematyka-2023-maj-pp/zad/19.2",
    "subject": "matematyka",
    "level": "podstawowa",
    "category": "matura",
    "points": 1,
    "text": "Zapisz maksymalny przedział, w którym funkcja f jest malejąca.",
}

# The official działy per subject (extract them from the CKE informatory).
criteria = topic_criteria(["Liczby rzeczywiste", "Funkcje", "Planimetria", "..."])

tag = tag_question(client, question, criteria)
print(tag["topic"], tag["difficulty_label"], tag["method"])
print(tag["group_label"], tag["vector"])
```

Run the example: `JEV_API_KEY=... python examples/tag_one.py`.

### Endpoints

`JevClient` defaults to OpenCode Zen (`https://opencode.ai/zen/v1/systemone`,
model `jev-1.13`). Point it at TypeSafe directly with:

```python
JevClient(api_key=..., url="https://api.typesafe.ai/v1/systemone", model="jev-latest")
```

## Layout

```
src/jev_categorise/
  client.py       # System One HTTP client: retries, backoff, Retry-After
  primitives.py   # Choice / Score / Noul dataclasses
  taxonomy.py     # method, answer-form, capability, bloom, time taxonomies + vector dims
  pipeline.py     # state → typed questions → parsed tag → vector/group
  vectors.py      # capability vector, capability bits, stable group_id
  metatags.py     # deterministic + hidden machine-only meta-tags
examples/tag_one.py
tests/test_core.py   # offline; no network
```

## Credits

Built for [matura.lol](https://matura.lol). Jev is by
[TypeSafe AI](https://docs.typesafe.ai/introduction). If you reuse this, please
credit matura.lol with a link.
