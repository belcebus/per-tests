#!/usr/bin/env python3
"""One-shot converter: YAML exam questions -> single CSV.

This script generates a CSV compatible with examenes-csv/ejemplo-preguntas.csv,
using only data/exams/questions/**/*.yaml as source.

Design constraints:
- One-shot full regeneration.
- No modification of existing project files.
- Output and docs live under examenes-csv/.
"""

from __future__ import annotations

import argparse
import csv
import html
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml


CSV_COLUMNS = [
    "category",
    "question",
    "question_image",
    "question_hint",
    "type",
    "published",
    "wrong_answer_text",
    "right_answer_text",
    "explanation",
    "user_explanation",
    "not_influence_to_score",
    "weight",
    "answers",
    "options",
    "question_title",
    "tags",
    "id",
]

CSV_OPTIONS_TEMPLATE = (
    "bg_image=::use_html=off::enable_question_text_max_length=off::"
    "question_text_max_length=::question_limit_text_type=characters::"
    "question_enable_text_message=off::enable_question_number_max_length=off::"
    "question_number_max_length=::quiz_hide_question_text=off::"
    "enable_max_selection_number=off::max_selection_number=::"
    "quiz_question_note_message=::enable_case_sensitive_text=off::"
    "enable_min_selection_number=off::min_selection_number=::"
    "enable_question_number_min_length=off::question_number_min_length=::"
    "enable_question_number_error_message=off::question_number_error_message=::"
    "quiz_enable_question_stripslashes=off::quiz_disable_answer_stripslashes=off::"
    "answer_slug_max_id=1::answer_incorrect_matches=::"
    "enable_question_upload_types=off::question_upload_types=::"
    "question_upload_file_max_size=1"
)

ANNULLED_VALUES = {"anulada", "anulado", "annulled"}


@dataclass
class BuildStats:
    yaml_files: int = 0
    rows: int = 0
    annulled_rows: int = 0
    warnings: int = 0


class IdFactory:
    def __init__(self) -> None:
        self.row_id = 1
        self.option_id = 1

    def next_row_id(self) -> str:
        value = str(self.row_id)
        self.row_id += 1
        return value

    def next_option_id(self) -> str:
        value = str(self.option_id)
        self.option_id += 1
        return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one-shot CSV from YAML exams/questions tree"
    )
    parser.add_argument(
        "--input-root",
        default="data/exams/questions",
        help="Root directory containing YAML files",
    )
    parser.add_argument(
        "--output",
        default="examenes-csv/preguntas_todas_convocatorias.csv",
        help="Target CSV path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on first data consistency warning",
    )
    return parser.parse_args()


def natural_key_for_category(raw_key: object) -> Tuple[int, str]:
    text = str(raw_key)
    if text.isdigit():
        return (0, f"{int(text):04d}")
    return (1, text)


def ordered_option_keys(options: Dict[str, str]) -> List[str]:
    preferred = ["a", "b", "c", "d", "e", "f"]
    lowered = {k.lower(): k for k in options.keys()}

    result: List[str] = []
    for key in preferred:
        if key in lowered:
            result.append(lowered[key])

    for key in sorted(options.keys()):
        if key not in result:
            result.append(key)

    return result


def normalize_correct_keys(correct_answer: str, options: Dict[str, str]) -> Tuple[bool, set[str]]:
    lowered_keys = {k.lower() for k in options.keys()}
    normalized = correct_answer.strip().lower()

    if normalized in ANNULLED_VALUES:
        return True, set()

    if normalized in lowered_keys:
        return False, {normalized}

    # Accept compact multiple answers like "bc" or "abd"
    compact = normalized.replace(",", "").replace(" ", "")
    if compact and all(ch in lowered_keys for ch in compact):
        return False, set(compact)

    return False, set()


def encode_question_html(question_text: str) -> str:
    wrapped = f"<p>{question_text.strip()}</p>"
    return html.escape(wrapped, quote=False)


def build_answers_field(
    options: Dict[str, str],
    correct_keys: set[str],
    is_annulled: bool,
    ids: IdFactory,
) -> str:
    segments: List[str] = []
    for original_key in ordered_option_keys(options):
        key = original_key.lower()
        option_text = str(options[original_key]).strip()
        is_correct = "1" if (not is_annulled and key in correct_keys) else "0"
        segment = f"{option_text}::{is_correct}::0::::::A::{ids.next_option_id()}::::"
        segments.append(segment)
    if not segments:
        return ""
    return ";;".join(segments) + ";;"


def warn(msg: str, stats: BuildStats, strict: bool) -> None:
    stats.warnings += 1
    print(f"[WARN] {msg}")
    if strict:
        raise ValueError(msg)


def convert_yaml_file(
    yaml_path: Path,
    ids: IdFactory,
    stats: BuildStats,
    strict: bool,
) -> List[Dict[str, str]]:
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    categories = data.get("categories", {})
    if not isinstance(categories, dict):
        warn(f"Formato inesperado (sin categories dict): {yaml_path}", stats, strict)
        return []

    rows: List[Dict[str, str]] = []

    for category_key in sorted(categories.keys(), key=natural_key_for_category):
        category_block = categories.get(category_key) or {}
        category_name = str(category_block.get("name", "")).strip()
        questions = category_block.get("questions", [])

        if not isinstance(questions, list):
            warn(
                f"questions no es lista en {yaml_path} categoría {category_key}",
                stats,
                strict,
            )
            continue

        for question in questions:
            if not isinstance(question, dict):
                warn(f"Pregunta no dict en {yaml_path}", stats, strict)
                continue

            question_text = str(question.get("question", "")).strip()
            if not question_text:
                warn(f"Pregunta vacía en {yaml_path}", stats, strict)

            options = question.get("options", {})
            if not isinstance(options, dict):
                warn(f"Opciones no dict en {yaml_path}", stats, strict)
                options = {}

            if len(options) < 2:
                warn(
                    f"Menos de 2 opciones en {yaml_path} pregunta id={question.get('id')}",
                    stats,
                    strict,
                )

            correct_answer = str(question.get("correct_answer", "")).strip()
            is_annulled, correct_keys = normalize_correct_keys(correct_answer, options)

            if is_annulled:
                stats.annulled_rows += 1
            elif not correct_keys:
                warn(
                    (
                        "Sin respuesta correcta reconocida en "
                        f"{yaml_path} pregunta id={question.get('id')} "
                        f"(correct_answer={correct_answer})"
                    ),
                    stats,
                    strict,
                )

            answers = build_answers_field(options, correct_keys, is_annulled, ids)
            category_value = str(question.get("category_name", "")).strip() or category_name

            row = {
                "category": category_value,
                "question": encode_question_html(question_text),
                "question_image": "",
                "question_hint": "",
                "type": "radio",
                "published": "1",
                "wrong_answer_text": "",
                "right_answer_text": "",
                "explanation": "",
                "user_explanation": "off",
                "not_influence_to_score": "on" if is_annulled else "off",
                "weight": "1",
                "answers": answers,
                "options": CSV_OPTIONS_TEMPLATE,
                "question_title": "",
                "tags": "",
                "id": ids.next_row_id(),
            }

            rows.append(row)

    return rows


def collect_yaml_paths(root: Path) -> List[Path]:
    return sorted(root.rglob("*.yaml"), key=lambda p: p.as_posix())


def write_csv(rows: Iterable[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    input_root = Path(args.input_root)
    output_path = Path(args.output)

    if not input_root.exists():
        print(f"[ERROR] Input root not found: {input_root}")
        return 2

    yaml_paths = collect_yaml_paths(input_root)
    if not yaml_paths:
        print(f"[ERROR] No YAML files found under: {input_root}")
        return 2

    stats = BuildStats(yaml_files=len(yaml_paths))
    ids = IdFactory()
    all_rows: List[Dict[str, str]] = []

    for yaml_path in yaml_paths:
        file_rows = convert_yaml_file(yaml_path, ids, stats, args.strict)
        all_rows.extend(file_rows)

    stats.rows = len(all_rows)

    if not all_rows:
        print("[ERROR] No rows generated.")
        return 2

    write_csv(all_rows, output_path)

    print("[OK] CSV generado")
    print(f" - YAML procesados: {stats.yaml_files}")
    print(f" - Filas generadas: {stats.rows}")
    print(f" - Preguntas anuladas: {stats.annulled_rows}")
    print(f" - Warnings: {stats.warnings}")
    print(f" - Salida: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
