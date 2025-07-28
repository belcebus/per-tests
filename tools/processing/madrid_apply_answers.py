#!/usr/bin/env python3
"""
Aplica respuestas oficiales extraídas por OCR a archivos YAML de exámenes.

Este script toma respuestas extraídas en formato JSON y las aplica a los archivos YAML
de preguntas correspondientes, creando backups automáticos y validando la consistencia.
"""

import json
import yaml
import sys
import argparse
from pathlib import Path
from typing import Dict, Union, List, Optional
from config.settings import settings

# Añadir el directorio del proyecto al path para importaciones
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def convert_array_to_comma_format(answer: Union[str, List[str]]) -> str:
    """Convierte arrays a formato de comas para YAML"""
    if isinstance(answer, list):
        return ",".join(answer)
    return answer


def load_extracted_answers(
    answers_file: Optional[str] = None,
) -> Dict[str, Union[str, List[str]]]:
    """Carga las respuestas extraídas del archivo JSON"""
    from typing import cast

    extracted_dir = settings.get_extracted_path()
    answers_path: Path
    if answers_file is None:
        # Buscar archivos que sigan el patrón per-test0X-*.json (donde X puede ser 1-5)
        pattern_files = list(extracted_dir.glob("per-test0[1-5]-*.json"))
        if pattern_files:
            answers_path = pattern_files[0]
            print(f"📄 Usando archivo con patrón nuevo: {answers_path.name}")
        else:
            answers_path = extracted_dir / "per_test01_answers.json"
            print(f"📄 Usando archivo de compatibilidad: {answers_path.name}")
    else:
        answers_path = Path(answers_file)

    if not answers_path.exists():
        raise FileNotFoundError(f"Archivo de respuestas no encontrado: {answers_path}")

    with open(answers_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Aseguramos el tipo de retorno
    answers = data["answers"]
    if not isinstance(answers, dict):
        raise ValueError("El campo 'answers' no es un diccionario")
    return cast(Dict[str, Union[str, List[str]]], answers)


def apply_answers_to_yaml(
    yaml_file: Path, extracted_answers: Dict[str, Union[str, List[str]]]
) -> int:
    """Aplica las respuestas extraídas al archivo YAML"""
    print(f"📝 Procesando {yaml_file.name}...")

    # Crear backup del archivo original en el directorio de backups
    backup_dir = settings.get_backups_path()
    backup_dir.mkdir(parents=True, exist_ok=True)  # Asegura que el directorio exista
    backup_file = backup_dir / f"{yaml_file.stem}.yaml.backup"

    if not backup_file.exists():
        # Copiar el archivo original al directorio de backups
        import shutil

        shutil.copy2(yaml_file, backup_file)
        print(f"💾 Backup creado: {backup_file.name}")

    # Cargar el archivo YAML original
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    updates_count = 0
    questions_found = 0

    # Procesar cada categoría y pregunta
    # Intentar ambas estructuras: 'categories' y 'pycategories'
    categories_data = data.get("categories", data.get("pycategories", {}))

    for category_id, category_data in categories_data.items():
        questions = category_data.get("questions", [])

        for question in questions:
            question_id = question.get("id")
            questions_found += 1
            if question_id and str(question_id) in extracted_answers:
                old_answer = question.get("correct_answer", "N/A")
                new_answer = extracted_answers[str(question_id)]
                # Convertir array a formato de comas para YAML
                yaml_answer = convert_array_to_comma_format(new_answer)
                # Aplicar la nueva respuesta en formato YAML
                question["correct_answer"] = yaml_answer
                # Mostrar el cambio
                if old_answer != yaml_answer:
                    if isinstance(new_answer, list):
                        print(
                            f"   🔄 Pregunta {question_id}: {old_answer} → {yaml_answer} (convertido de array {new_answer})"
                        )
                    else:
                        print(
                            f"   🔄 Pregunta {question_id}: {old_answer} → {yaml_answer}"
                        )
                    updates_count += 1
                else:
                    if isinstance(new_answer, list):
                        print(
                            f"   ✅ Pregunta {question_id}: {yaml_answer} (array {new_answer}, sin cambios)"
                        )
                    else:
                        print(
                            f"   ✅ Pregunta {question_id}: {yaml_answer} (sin cambios)"
                        )

    # Guardar el archivo actualizado
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    print("\\n📊 RESUMEN:")
    print(f"   📄 Preguntas encontradas en YAML: {questions_found}")
    print(f"   🔄 Respuestas actualizadas: {updates_count}")
    print(f"   📁 Archivo actualizado: {yaml_file}")

    return updates_count


def validate_answers(extracted_answers: Dict[str, Union[str, List[str]]]):
    """Valida las respuestas extraídas"""
    print("🔍 Validando respuestas extraídas...")

    valid_answers = {"a", "b", "c", "d", "ANULADA"}
    total_answers = len(extracted_answers)
    valid_count = 0
    multiple_answers_count = 0

    for q_id, answer in extracted_answers.items():
        # Verificar si es un array (múltiples respuestas)
        if isinstance(answer, list):
            multiple_answers_count += 1
            # Validar cada respuesta en el array
            all_valid = all(
                ans.lower() in [v.lower() for v in valid_answers] for ans in answer
            )
            if all_valid:
                valid_count += 1
                comma_format = convert_array_to_comma_format(answer)
                print(
                    f"   ✅ Pregunta {q_id}: {answer} → se convertirá a '{comma_format}'"
                )
            else:
                invalid_answers = [
                    ans
                    for ans in answer
                    if ans.lower() not in [v.lower() for v in valid_answers]
                ]
                print(
                    f"   ⚠️  Pregunta {q_id}: respuestas inválidas en array {invalid_answers}"
                )
        else:
            # Respuesta simple (string)
            if answer.lower() in [v.lower() for v in valid_answers]:
                valid_count += 1
            else:
                print(f"   ⚠️  Pregunta {q_id}: respuesta inválida '{answer}'")

    print(f"   ✅ Respuestas válidas: {valid_count}/{total_answers}")
    if multiple_answers_count > 0:
        print(f"   🔢 Preguntas con múltiples respuestas: {multiple_answers_count}")

    # Mostrar resumen de respuestas (formato que se aplicará al YAML)
    answer_counts: dict[str, int] = {}
    for answer in extracted_answers.values():
        yaml_format = convert_array_to_comma_format(answer)
        answer_counts[yaml_format] = answer_counts.get(yaml_format, 0) + 1

    print("   📊 Distribución de respuestas (formato YAML):")
    for answer, count in sorted(answer_counts.items()):
        if "," in answer:
            print(f"      {answer}: {count} (múltiples respuestas)")
        else:
            print(f"      {answer}: {count}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="🚢 Aplica respuestas oficiales extraídas por OCR a archivos YAML de exámenes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EJEMPLOS DE USO:

  # Aplicar respuestas usando auto-detección de archivos
  python madrid_apply_answers.py

  # Especificar archivos específicos
  python madrid_apply_answers.py --input-file per-test05-madrid-2025-abril.json --target-file per-test05-madrid-2025-abril.yaml

  # Modo detallado
  python madrid_apply_answers.py --input-file respuestas.json --target-file examen.yaml --verbose
        """,
    )

    parser.add_argument(
        "--input-file",
        type=str,
        help="Archivo JSON con las respuestas extraídas (default: auto-detectar)",
    )

    parser.add_argument(
        "--target-file",
        type=str,
        help="Archivo YAML del examen a actualizar (obligatorio si no hay auto-detección)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directorio de salida (default: mismo directorio que target-file)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada del procesamiento",
    )

    args = parser.parse_args()

    if args.verbose:
        print("🚀 Aplicando respuestas OCR al archivo YAML correspondiente...")

    try:
        # Cargar respuestas extraídas
        extracted_answers = load_extracted_answers(args.input_file)
        if args.verbose:
            print(f"📖 Respuestas cargadas: {len(extracted_answers)}")

        # Validar respuestas
        if args.verbose:
            validate_answers(extracted_answers)

        # Determinar archivo YAML objetivo
        if args.target_file:
            yaml_file = settings.get_exams_path() / args.target_file
        else:
            # Intentar auto-detectar basándose en el archivo de respuestas
            if args.input_file:
                # Extraer información del nombre del archivo JSON para encontrar el YAML correspondiente
                input_path = Path(args.input_file)
                # Ejemplo: per-test05-madrid-2025-abril.json -> per-test05-madrid-2025-abril.yaml
                yaml_name = input_path.stem + ".yaml"
                yaml_file = settings.get_exams_path() / yaml_name

                if not yaml_file.exists():
                    print("❌ No se pudo auto-detectar archivo YAML correspondiente.")
                    print(f"   Archivo esperado: {yaml_file}")
                    print("   Por favor, especifica --target-file manualmente.")
                    return
                else:
                    if args.verbose:
                        print(f"🔍 Auto-detectado archivo YAML: {yaml_file}")
            else:
                print(
                    "❌ Debes especificar --target-file o --input-file para auto-detección."
                )
                print(
                    "   Uso: python madrid_apply_answers.py --input-file respuestas.json --target-file examen.yaml"
                )
                return

        if not yaml_file.exists():
            print(f"❌ Archivo YAML no encontrado: {yaml_file}")
            return

        updates = apply_answers_to_yaml(yaml_file, extracted_answers)

        print("\n🎉 Proceso completado exitosamente!")
        if args.verbose:
            print(f"   📈 Total actualizaciones: {updates}")

        if updates > 0:
            print("\n💡 Recomendaciones:")
            print("   - Reinicia el servidor de la aplicación para cargar los cambios")
            print(
                "   - Verifica algunas respuestas manualmente para confirmar la precisión"
            )
            print("   - El archivo original se guardó como .backup")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
