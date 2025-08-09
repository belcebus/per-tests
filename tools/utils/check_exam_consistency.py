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


def validate_question_options(exam_data):
    """
    Valida que todas las preguntas tengan exactamente 4 opciones (a, b, c, d).
    
    Retorna:
        dict: {
            'valid': bool,
            'invalid_questions': [{'category': int, 'question_id': str, 'options': list, 'issue': str}],
            'total_questions': int,
            'valid_questions': int
        }
    """
    if not exam_data or "categories" not in exam_data:
        return {
            'valid': False,
            'invalid_questions': [],
            'total_questions': 0,
            'valid_questions': 0
        }
    
    invalid_questions = []
    total_questions = 0
    valid_questions = 0
    expected_options = {'a', 'b', 'c', 'd'}
    
    for cat_id, cat_data in exam_data["categories"].items():
        questions = cat_data.get("questions", [])
        
        for question in questions:
            total_questions += 1
            question_id = question.get("id", "unknown")
            options = question.get("options", {})
            
            if not options:
                invalid_questions.append({
                    'category': int(cat_id),
                    'question_id': str(question_id),
                    'options': [],
                    'issue': 'Sin opciones'
                })
                continue
                
            # Convertir las claves de opciones a conjunto para comparar
            actual_options = set(options.keys())
            
            if actual_options != expected_options:
                # Determinar el tipo de problema específico
                if len(actual_options) < 4:
                    missing = expected_options - actual_options
                    issue = f"Faltan opciones: {', '.join(sorted(missing))}"
                elif len(actual_options) > 4:
                    extra = actual_options - expected_options
                    issue = f"Opciones extra: {', '.join(sorted(extra))}"
                else:
                    # Mismo número pero diferentes letras
                    missing = expected_options - actual_options
                    extra = actual_options - expected_options
                    issue = f"Opciones incorrectas. Faltan: {', '.join(sorted(missing))}, Sobran: {', '.join(sorted(extra))}"
                
                invalid_questions.append({
                    'category': int(cat_id),
                    'question_id': str(question_id),
                    'options': sorted(list(actual_options)),
                    'issue': issue
                })
            else:
                valid_questions += 1
    
    return {
        'valid': len(invalid_questions) == 0,
        'invalid_questions': invalid_questions,
        'total_questions': total_questions,
        'valid_questions': valid_questions
    }


def validate_correct_answers(exam_data):
    """
    Valida que las respuestas correctas estén entre las opciones disponibles.
    Maneja respuestas simples (ej: "a") y múltiples (ej: "a,b", "c,d").
    
    Retorna:
        dict: {
            'valid': bool,
            'invalid_questions': [{'category': int, 'question_id': str, 'correct_answer': str, 'available_options': list, 'issue': str}],
            'total_questions': int,
            'valid_questions': int
        }
    """
    if not exam_data or "categories" not in exam_data:
        return {
            'valid': False,
            'invalid_questions': [],
            'total_questions': 0,
            'valid_questions': 0
        }
    
    invalid_questions = []
    total_questions = 0
    valid_questions = 0
    
    for cat_id, cat_data in exam_data["categories"].items():
        questions = cat_data.get("questions", [])
        
        for question in questions:
            total_questions += 1
            question_id = question.get("id", "unknown")
            correct_answer = question.get("correct_answer")
            options = question.get("options", {})
            available_options = list(options.keys()) if options else []
            
            if not correct_answer:
                invalid_questions.append({
                    'category': int(cat_id),
                    'question_id': str(question_id),
                    'correct_answer': 'N/A',
                    'available_options': available_options,
                    'issue': 'Sin respuesta correcta definida'
                })
                continue
            
            # Validar respuestas especiales
            if correct_answer.upper() == "ANULADA":
                valid_questions += 1
                continue
            
            # Procesar respuestas múltiples separadas por comas
            # Eliminar espacios y convertir a minúsculas para comparación
            answer_parts = [part.strip().lower() for part in str(correct_answer).split(',')]
            
            # Verificar que todas las partes de la respuesta estén en las opciones disponibles
            missing_options = []
            for answer_part in answer_parts:
                if answer_part not in available_options:
                    missing_options.append(answer_part)
            
            if missing_options:
                if len(answer_parts) == 1:
                    # Respuesta simple no encontrada
                    issue = f'Respuesta correcta "{correct_answer}" no está en opciones disponibles'
                else:
                    # Respuesta múltiple con partes faltantes
                    missing_str = ', '.join(missing_options)
                    issue = f'Respuesta múltiple "{correct_answer}": opciones faltantes [{missing_str}]'
                
                invalid_questions.append({
                    'category': int(cat_id),
                    'question_id': str(question_id),
                    'correct_answer': str(correct_answer),
                    'available_options': available_options,
                    'issue': issue
                })
            else:
                valid_questions += 1
    
    return {
        'valid': len(invalid_questions) == 0,
        'invalid_questions': invalid_questions,
        'total_questions': total_questions,
        'valid_questions': valid_questions
    }


def validate_question_structure(exam_data):
    """
    Valida que todas las preguntas tengan la estructura completa requerida:
    texto de pregunta, opciones y respuesta correcta.
    
    Retorna:
        dict: {
            'valid': bool,
            'invalid_questions': [{'category': int, 'question_id': str, 'missing_fields': list, 'issue': str}],
            'total_questions': int,
            'valid_questions': int
        }
    """
    if not exam_data or "categories" not in exam_data:
        return {
            'valid': False,
            'invalid_questions': [],
            'total_questions': 0,
            'valid_questions': 0
        }
    
    invalid_questions = []
    total_questions = 0
    valid_questions = 0
    required_fields = ['question', 'options', 'correct_answer']
    
    for cat_id, cat_data in exam_data["categories"].items():
        questions = cat_data.get("questions", [])
        
        for question in questions:
            total_questions += 1
            question_id = question.get("id", "unknown")
            missing_fields = []
            
            # Verificar texto de pregunta
            question_text = question.get("question")
            if not question_text or not str(question_text).strip():
                missing_fields.append("question")
            
            # Verificar opciones
            options = question.get("options")
            if not options or not isinstance(options, dict) or len(options) == 0:
                missing_fields.append("options")
            else:
                # Verificar que las opciones tengan texto
                empty_options = []
                for opt_key, opt_value in options.items():
                    if not opt_value or not str(opt_value).strip():
                        empty_options.append(opt_key)
                if empty_options:
                    missing_fields.append(f"opciones vacías: {', '.join(empty_options)}")
            
            # Verificar respuesta correcta
            correct_answer = question.get("correct_answer")
            if not correct_answer:
                missing_fields.append("correct_answer")
            
            if missing_fields:
                invalid_questions.append({
                    'category': int(cat_id),
                    'question_id': str(question_id),
                    'missing_fields': missing_fields,
                    'issue': f"Campos faltantes o vacíos: {', '.join(missing_fields)}"
                })
            else:
                valid_questions += 1
    
    return {
        'valid': len(invalid_questions) == 0,
        'invalid_questions': invalid_questions,
        'total_questions': total_questions,
        'valid_questions': valid_questions
    }


def validate_unique_question_ids(exam_data):
    """
    Valida que todos los IDs de preguntas sean únicos dentro del examen.
    
    Retorna:
        dict: {
            'valid': bool,
            'duplicate_ids': [{'question_id': str, 'categories': list, 'count': int, 'issue': str}],
            'total_questions': int,
            'unique_ids': int
        }
    """
    if not exam_data or "categories" not in exam_data:
        return {
            'valid': False,
            'duplicate_ids': [],
            'total_questions': 0,
            'unique_ids': 0
        }
    
    id_counts = {}  # id -> {'count': int, 'categories': [int]}
    total_questions = 0
    
    for cat_id, cat_data in exam_data["categories"].items():
        questions = cat_data.get("questions", [])
        
        for question in questions:
            total_questions += 1
            question_id = str(question.get("id", "unknown"))
            
            if question_id not in id_counts:
                id_counts[question_id] = {'count': 0, 'categories': []}
            
            id_counts[question_id]['count'] += 1
            id_counts[question_id]['categories'].append(int(cat_id))
    
    # Encontrar IDs duplicados
    duplicate_ids = []
    for question_id, data in id_counts.items():
        if data['count'] > 1:
            duplicate_ids.append({
                'question_id': question_id,
                'categories': data['categories'],
                'count': data['count'],
                'issue': f'ID "{question_id}" se repite {data["count"]} veces en categorías {data["categories"]}'
            })
    
    unique_ids = len(id_counts)
    
    return {
        'valid': len(duplicate_ids) == 0,
        'duplicate_ids': duplicate_ids,
        'total_questions': total_questions,
        'unique_ids': unique_ids
    }


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
    
    # Estadísticas de validación de opciones
    options_valid_exams = []
    options_invalid_exams = []
    
    # Estadísticas de validación de respuestas correctas
    answers_valid_exams = []
    answers_invalid_exams = []
    
    # Estadísticas de validación de estructura
    structure_valid_exams = []
    structure_invalid_exams = []
    
    # Estadísticas de validación de IDs únicos
    ids_valid_exams = []
    ids_invalid_exams = []
    # Análisis por examen
    for exam_file in exam_files:
        exam_name = exam_file.name
        exam_data = load_exam_yaml(exam_file)
        if not exam_data:
            error_exams.append(exam_name)
            continue
        exam_dist = analyze_exam_distribution(exam_data)
        exam_info = get_exam_info(exam_data)
        
        # Validar opciones de respuesta
        options_validation = validate_question_options(exam_data)
        
        # Validar respuestas correctas
        answers_validation = validate_correct_answers(exam_data)
        
        # Validar estructura de preguntas
        structure_validation = validate_question_structure(exam_data)
        
        # Validar IDs únicos
        ids_validation = validate_unique_question_ids(exam_data)
        
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
        
        # Clasificar exámenes por consistencia de distribución
        if is_consistent and total_questions == expected_questions:
            consistent_exams.append(exam_name)
        else:
            inconsistent_exams.append(
                (exam_name, comparison_lines, total_questions, expected_questions)
            )
        
        # Clasificar exámenes por validez de opciones
        if options_validation['valid']:
            options_valid_exams.append(exam_name)
        else:
            options_invalid_exams.append((exam_name, options_validation))
            
        # Clasificar exámenes por validez de respuestas correctas
        if answers_validation['valid']:
            answers_valid_exams.append(exam_name)
        else:
            answers_invalid_exams.append((exam_name, answers_validation))
            
        # Clasificar exámenes por validez de estructura
        if structure_validation['valid']:
            structure_valid_exams.append(exam_name)
        else:
            structure_invalid_exams.append((exam_name, structure_validation))
            
        # Clasificar exámenes por validez de IDs únicos
        if ids_validation['valid']:
            ids_valid_exams.append(exam_name)
        else:
            ids_invalid_exams.append((exam_name, ids_validation))

    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print("=" * 80)
    print(f"✅ Exámenes consistentes (distribución): {len(consistent_exams)}")
    print(f"❌ Exámenes inconsistentes (distribución): {len(inconsistent_exams)}")
    print(f"✅ Exámenes con opciones válidas (a,b,c,d): {len(options_valid_exams)}")
    print(f"❌ Exámenes con opciones inválidas: {len(options_invalid_exams)}")
    print(f"✅ Exámenes con respuestas correctas válidas: {len(answers_valid_exams)}")
    print(f"❌ Exámenes con respuestas correctas inválidas: {len(answers_invalid_exams)}")
    print(f"✅ Exámenes con estructura completa: {len(structure_valid_exams)}")
    print(f"❌ Exámenes con estructura incompleta: {len(structure_invalid_exams)}")
    print(f"✅ Exámenes con IDs únicos: {len(ids_valid_exams)}")
    print(f"❌ Exámenes con IDs duplicados: {len(ids_invalid_exams)}")
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

    # Mostrar detalles de exámenes con opciones inválidas
    if options_invalid_exams:
        print(f"\n🔤 EXÁMENES CON OPCIONES INVÁLIDAS ({len(options_invalid_exams)}):")
        print("-" * 80)
        for exam_name, validation_data in options_invalid_exams:
            print(f"\n📄 {exam_name}")
            print("=" * 80)
            invalid_questions = validation_data['invalid_questions']
            total_q = validation_data['total_questions']
            valid_q = validation_data['valid_questions']
            invalid_q = len(invalid_questions)
            
            print(f"Total de preguntas: {total_q} | Válidas: {valid_q} | Inválidas: {invalid_q}")
            print("-" * 80)
            print("Cat | ID  | Opciones Encontradas   | Problema")
            print("----|-----|------------------------|----------------------------------")
            
            for q in invalid_questions:
                cat = q['category']
                qid = q['question_id']
                opts = ', '.join(q['options']) if q['options'] else 'ninguna'
                issue = q['issue']
                print(f"{cat:3d} | {qid:3s} | {opts:<22} | {issue}")

    # Mostrar detalles de exámenes con respuestas correctas inválidas
    if answers_invalid_exams:
        print(f"\n✔️ EXÁMENES CON RESPUESTAS INCORRECTAS ({len(answers_invalid_exams)}):")
        print("-" * 80)
        for exam_name, validation_data in answers_invalid_exams:
            print(f"\n📄 {exam_name}")
            print("=" * 80)
            invalid_questions = validation_data['invalid_questions']
            total_q = validation_data['total_questions']
            valid_q = validation_data['valid_questions']
            invalid_q = len(invalid_questions)
            
            print(f"Total de preguntas: {total_q} | Válidas: {valid_q} | Inválidas: {invalid_q}")
            print("-" * 80)
            print("Cat | ID  | Resp. Correcta | Opciones Disponibles    | Problema")
            print("----|-----|----------------|------------------------|----------------------------------")
            
            for q in invalid_questions:
                cat = q['category']
                qid = q['question_id']
                correct = q['correct_answer']
                opts = ', '.join(q['available_options']) if q['available_options'] else 'ninguna'
                issue = q['issue']
                print(f"{cat:3d} | {qid:3s} | {correct:<14} | {opts:<22} | {issue}")

    # Mostrar detalles de exámenes con estructura incompleta
    if structure_invalid_exams:
        print(f"\n🏗️ EXÁMENES CON ESTRUCTURA INCOMPLETA ({len(structure_invalid_exams)}):")
        print("-" * 80)
        for exam_name, validation_data in structure_invalid_exams:
            print(f"\n📄 {exam_name}")
            print("=" * 80)
            invalid_questions = validation_data['invalid_questions']
            total_q = validation_data['total_questions']
            valid_q = validation_data['valid_questions']
            invalid_q = len(invalid_questions)
            
            print(f"Total de preguntas: {total_q} | Válidas: {valid_q} | Inválidas: {invalid_q}")
            print("-" * 80)
            print("Cat | ID  | Problema")
            print("----|-----|--------------------------------------------------")
            
            for q in invalid_questions:
                cat = q['category']
                qid = q['question_id']
                issue = q['issue']
                print(f"{cat:3d} | {qid:3s} | {issue}")

    # Mostrar detalles de exámenes con IDs duplicados
    if ids_invalid_exams:
        print(f"\n🔢 EXÁMENES CON IDS DUPLICADOS ({len(ids_invalid_exams)}):")
        print("-" * 80)
        for exam_name, validation_data in ids_invalid_exams:
            print(f"\n📄 {exam_name}")
            print("=" * 80)
            duplicate_ids = validation_data['duplicate_ids']
            total_q = validation_data['total_questions']
            unique_ids = validation_data['unique_ids']
            
            print(f"Total de preguntas: {total_q} | IDs únicos: {unique_ids} | IDs duplicados: {len(duplicate_ids)}")
            print("-" * 80)
            print("ID  | Repeticiones | Categorías | Problema")
            print("----|--------------|------------|----------------------------------")
            
            for dup in duplicate_ids:
                qid = dup['question_id']
                count = dup['count']
                cats = ', '.join(map(str, dup['categories']))
                issue = dup['issue']
                print(f"{qid:3s} | {count:12d} | {cats:<10} | {issue}")

    # Estadísticas de consistencia
    consistency_rate = (
        (len(consistent_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    options_validity_rate = (
        (len(options_valid_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    answers_validity_rate = (
        (len(answers_valid_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    structure_validity_rate = (
        (len(structure_valid_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    ids_validity_rate = (
        (len(ids_valid_exams) / len(exam_files)) * 100 if exam_files else 0
    )
    
    print(f"\n📈 ESTADÍSTICAS FINALES:")
    print(f"  🎯 Tasa de consistencia (distribución): {consistency_rate:.1f}%")
    print(f"  🔤 Tasa de validez de opciones: {options_validity_rate:.1f}%")
    print(f"  ✔️ Tasa de validez de respuestas: {answers_validity_rate:.1f}%")
    print(f"  🏗️ Tasa de estructura completa: {structure_validity_rate:.1f}%")
    print(f"  🔢 Tasa de IDs únicos: {ids_validity_rate:.1f}%")

    # Verificar si hay algún problema
    has_issues = (
        len(inconsistent_exams) > 0 or 
        len(options_invalid_exams) > 0 or 
        len(answers_invalid_exams) > 0 or 
        len(structure_invalid_exams) > 0 or 
        len(ids_invalid_exams) > 0
    )

    if has_issues:
        print("\n💡 RECOMENDACIONES:")
        if len(inconsistent_exams) > 0:
            print("  📊 DISTRIBUCIÓN:")
            print("     - Revisar la extracción de preguntas en los exámenes inconsistentes")
            print("     - Verificar que las categorías estén correctamente identificadas")
            print("     - Considerar re-extraer los exámenes problemáticos con los scripts actualizados")
        if len(options_invalid_exams) > 0:
            print("  🔤 OPCIONES DE RESPUESTA:")
            print("     - Verificar que todas las preguntas tengan exactamente 4 opciones (a, b, c, d)")
            print("     - Revisar el proceso de extracción de opciones en los scripts")
            print("     - Considerar validación automática durante la extracción")
        if len(answers_invalid_exams) > 0:
            print("  ✔️ RESPUESTAS CORRECTAS:")
            print("     - Verificar que las respuestas correctas estén entre las opciones disponibles")
            print("     - Revisar el proceso de aplicación de respuestas oficiales")
            print("     - Validar que los archivos de respuestas JSON coincidan con los YAML")
        if len(structure_invalid_exams) > 0:
            print("  🏗️ ESTRUCTURA DE PREGUNTAS:")
            print("     - Verificar que todas las preguntas tengan texto, opciones y respuesta correcta")
            print("     - Revisar campos vacíos o faltantes en los archivos YAML")
            print("     - Considerar validación de estructura durante la extracción")
        if len(ids_invalid_exams) > 0:
            print("  🔢 IDS DE PREGUNTAS:")
            print("     - Verificar que no haya IDs de preguntas duplicados")
            print("     - Revisar el proceso de asignación de IDs en los scripts de extracción")
            print("     - Considerar usar IDs secuenciales automáticos")
    else:
        print("\n🎉 ¡EXCELENTE! Todos los exámenes pasaron todas las validaciones.")

    # Aplicar tolerancia cero: cualquier problema resulta en fallo del CI/CD
    total_issues = len(error_exams) + len(inconsistent_exams) + len(options_invalid_exams) + len(answers_invalid_exams) + len(structure_invalid_exams) + len(ids_invalid_exams)
    
    if total_issues > 0:
        print(f"\n❌ VALIDACIÓN FALLIDA: Se encontraron {total_issues} problemas que deben resolverse")
        print("💡 Política de tolerancia cero: todos los problemas deben corregirse antes de continuar.")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDACIÓN EXITOSA: Todos los exámenes pasan las validaciones de calidad")
        sys.exit(0)


if __name__ == "__main__":
    main()
