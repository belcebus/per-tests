#!/usr/bin/env python3
"""
Script para verificar la consistencia de la distribución de preguntas por categorías
en todos los exámenes YAML contra la distribución oficial definida en settings.py
"""

import yaml
import sys
from pathlib import Path
from config.settings import settings

# Agregar el directorio raíz del proyecto al path de Python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_exam_yaml(filepath):
    """Carga un archivo YAML de examen y retorna su contenido."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error al cargar {filepath}: {e}")
        return None


def analyze_exam_distribution(exam_data):
    """Analiza la distribución de preguntas por categoría en un examen."""
    if not exam_data or "categories" not in exam_data:
        return {}
    distribution = {}
    for cat_id, cat_data in exam_data["categories"].items():
        distribution[int(cat_id)] = len(cat_data.get("questions", []))
    return distribution


def get_exam_info(exam_data):
    """Extrae información básica del examen."""
    if not exam_data or "exam_info" not in exam_data:
        return {}
    return exam_data["exam_info"]


def find_all_exam_files():
    """Encuentra todos los archivos YAML de exámenes."""
    exam_files = []
    data_dir = Path("data/exams")
    if data_dir.exists():
        for yaml_file in data_dir.rglob("*.yaml"):
            exam_files.append(yaml_file)
    return sorted(exam_files)


def format_distribution_comparison(official_dist, exam_dist, exam_name):
    """Formatea la comparación de distribuciones para un examen."""
    lines = []
    lines.append(f"\n📊 {exam_name}")
    lines.append("=" * 80)
    lines.append("Cat | Nombre Categoría           | Oficial | Extraído | Dif | Estado")
    lines.append(
        "----|----------------------------|---------|----------|-----|--------"
    )
    total_official = 0
    total_extracted = 0
    all_match = True
    # Nombres de categorías
    category_names = {
        1: "Nomenclatura náutica",
        2: "Elementos de amarre y fondeo",
        3: "Seguridad",
        4: "Legislación",
        5: "Balizamiento",
        6: "Reglamento (RIPA)",
        7: "Maniobra y navegación",
        8: "Emergencias en la mar",
        9: "Meteorología",
        10: "Teoría de la navegación",
        11: "Carta de navegación",
    }
    for cat_id in sorted(official_dist.keys()):
        official_count = official_dist[cat_id]
        extracted_count = exam_dist.get(cat_id, 0)
        diff = extracted_count - official_count
        status = "✅ OK" if diff == 0 else f"❌ {diff:+d}"
        cat_name = category_names.get(cat_id, f"Categoría {cat_id}")
        if diff != 0:
            all_match = False
        total_official += official_count
        total_extracted += extracted_count
        lines.append(
            f"{cat_id:3d} | {cat_name:<26} | {official_count:7d} | {extracted_count:8d} | {diff:+3d} | {status}"
        )
    lines.append(
        "----|----------------------------|---------|----------|-----|--------"
    )
    total_diff = total_extracted - total_official
    total_status = "✅ PERFECTO" if all_match else f"❌ DIFERENCIAS ({total_diff:+d})"
    lines.append(
        f"TOT | {'TOTAL':<26} | {total_official:7d} | {total_extracted:8d} | {total_diff:+3d} | {total_status}"
    )
    return lines, all_match


def main():
    """Función principal."""
    print("🔍 Verificando consistencia de exámenes PER...")
    print("=" * 80)
    # Cargar distribución oficial
    official_dist = settings.simulacro_distribution
    print("📋 Distribución oficial (settings.py):")
    print("-" * 40)
    category_names = {
        1: "Nomenclatura náutica",
        2: "Elementos de amarre y fondeo",
        3: "Seguridad",
        4: "Legislación",
        5: "Balizamiento",
        6: "Reglamento (RIPA)",
        7: "Maniobra y navegación",
        8: "Emergencias en la mar",
        9: "Meteorología",
        10: "Teoría de la navegación",
        11: "Carta de navegación",
    }
    for cat_id, count in sorted(official_dist.items()):
        cat_name = category_names.get(cat_id, f"Categoría {cat_id}")
        print(f"{cat_id:2d}: {count:2d} preguntas - {cat_name}")
    total_official = sum(official_dist.values())
    print(f"Total: {total_official} preguntas")
    # Encontrar todos los archivos de exámenes
    exam_files = find_all_exam_files()
    print(f"\n🔍 Encontrados {len(exam_files)} archivos de exámenes")
    # Estadísticas globales
    consistent_exams = []
    inconsistent_exams = []
    error_exams = []
    # Análisis por examen
    for exam_file in exam_files:
        exam_name = exam_file.name
        exam_data = load_exam_yaml(exam_file)
        if not exam_data:
            error_exams.append(exam_name)
            continue
        exam_dist = analyze_exam_distribution(exam_data)
        exam_info = get_exam_info(exam_data)
        # Verificar si el examen tiene el número correcto total de preguntas
        total_questions = sum(exam_dist.values())
        expected_questions = exam_info.get("expected_questions", 45)
        if total_questions == 0:
            error_exams.append(exam_name)
            continue
        # Comparar distribuciones
        comparison_lines, is_consistent = format_distribution_comparison(
            official_dist, exam_dist, exam_name
        )
        if is_consistent and total_questions == expected_questions:
            consistent_exams.append(exam_name)
        else:
            inconsistent_exams.append(
                (exam_name, comparison_lines, total_questions, expected_questions)
            )

    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print("=" * 80)
    print(f"✅ Exámenes consistentes: {len(consistent_exams)}")
    print(f"❌ Exámenes inconsistentes: {len(inconsistent_exams)}")
    print(f"💥 Exámenes con errores: {len(error_exams)}")
    print(f"📁 Total de exámenes: {len(exam_files)}")

    # Mostrar exámenes consistentes
    if consistent_exams:
        print(f"\n✅ EXÁMENES CONSISTENTES ({len(consistent_exams)}):")
        print("-" * 40)
        for exam in sorted(consistent_exams):
            print(f"  ✓ {exam}")

    # Mostrar detalles de exámenes inconsistentes
    if inconsistent_exams:
        print(f"\n❌ EXÁMENES INCONSISTENTES ({len(inconsistent_exams)}):")
        print("-" * 40)
        for exam_name, comparison_lines, total_q, expected_q in inconsistent_exams:
            for line in comparison_lines:
                print(line)
            if total_q != expected_q:
                print(f"⚠️  Total de preguntas: {total_q} (esperado: {expected_q})")

    # Mostrar exámenes con errores
    if error_exams:
        print(f"\n💥 EXÁMENES CON ERRORES ({len(error_exams)}):")
        print("-" * 40)
        for exam in sorted(error_exams):
            print(f"  💥 {exam}")

    # Estadísticas de consistencia
    consistency_rate = (
        (len(consistent_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    print(f"\n📈 TASA DE CONSISTENCIA: {consistency_rate:.1f}%")

    if len(inconsistent_exams) > 0:
        print("\n💡 RECOMENDACIONES:")
        print("  - Revisar la extracción de preguntas en los exámenes inconsistentes")
        print("  - Verificar que las categorías estén correctamente identificadas")
        print(
            "  - Considerar re-extraer los exámenes problemáticos con los scripts actualizados"
        )


if __name__ == "__main__":
    main()
