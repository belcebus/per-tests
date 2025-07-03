#!/usr/bin/env python3
"""
Herramienta para analizar problemas de extracción de preguntas
Ayuda a identificar preguntas duplicadas, faltantes o mal formateadas
"""

import yaml
import sys
from pathlib import Path

def analyze_exam_questions(yaml_file):
    """Analiza las preguntas del examen y muestra problemas"""
    
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    print("🔍 ANÁLISIS DE PREGUNTAS DEL EXAMEN")
    print("=" * 60)
    
    categories = data.get('categories', {})
    all_questions = []
    
    # Recopilar todas las preguntas
    for cat_id, cat_data in categories.items():
        cat_name = cat_data.get('name', 'Sin nombre')
        questions = cat_data.get('questions', [])
        
        for q in questions:
            q_info = {
                'id': q.get('id'),
                'category': cat_id,
                'category_name': cat_name,
                'question': q.get('question', ''),
                'options': q.get('options', {}),
                'correct_answer': q.get('correct_answer')
            }
            all_questions.append(q_info)
    
    # Ordenar por ID
    all_questions.sort(key=lambda x: x['id'] if x['id'] else 0)
    
    # Análisis de problemas
    print(f"📊 TOTAL PREGUNTAS: {len(all_questions)}")
    print(f"📊 ESPERADAS: 45")
    print()
    
    # Buscar IDs duplicados
    ids = [q['id'] for q in all_questions if q['id']]
    from collections import Counter
    id_counts = Counter(ids)
    duplicates = [(id_, count) for id_, count in id_counts.items() if count > 1]
    
    if duplicates:
        print("❌ PREGUNTAS DUPLICADAS:")
        for dup_id, count in duplicates:
            print(f"   ID {dup_id}: {count} veces")
            
            # Mostrar detalles de las preguntas duplicadas
            dup_questions = [q for q in all_questions if q['id'] == dup_id]
            for i, q in enumerate(dup_questions, 1):
                question_preview = q['question'][:100] + "..." if len(q['question']) > 100 else q['question']
                print(f"      {i}. Cat {q['category']} ({q['category_name']}): {question_preview}")
        print()
    
    # Buscar IDs faltantes
    expected_ids = set(range(1, 46))
    found_ids = set(ids)
    missing_ids = expected_ids - found_ids
    
    if missing_ids:
        print(f"❌ PREGUNTAS FALTANTES: {sorted(missing_ids)}")
        print()
    
    # Buscar preguntas mal formateadas
    print("🔍 PREGUNTAS CON POSIBLES PROBLEMAS:")
    for q in all_questions:
        problems = []
        
        # Pregunta muy corta
        if len(q['question']) < 10:
            problems.append("Pregunta muy corta")
        
        # Pregunta incompleta (termina con ':' o '...')
        if q['question'].endswith(':') or q['question'].endswith('...'):
            problems.append("Pregunta posiblemente incompleta")
        
        # Faltan opciones
        if len(q['options']) < 4:
            problems.append(f"Solo {len(q['options'])} opciones")
        
        # Opciones muy cortas
        short_options = [k for k, v in q['options'].items() if len(v) < 5]
        if short_options:
            problems.append(f"Opciones cortas: {short_options}")
        
        if problems:
            print(f"   ID {q['id']}: {', '.join(problems)}")
            print(f"      Pregunta: {q['question']}")
            print(f"      Opciones: {list(q['options'].keys())}")
            print()
    
    # Mostrar secuencia de IDs por categoría
    print("📋 SECUENCIA DE IDs POR CATEGORÍA:")
    for cat_id, cat_data in categories.items():
        cat_name = cat_data.get('name', 'Sin nombre')
        questions = cat_data.get('questions', [])
        q_ids = [q.get('id') for q in questions if q.get('id')]
        print(f"   Cat {cat_id} ({cat_name}): {q_ids}")
    
    print()
    return all_questions

def show_specific_question(yaml_file, question_id):
    """Muestra detalles de una pregunta específica"""
    
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    categories = data.get('categories', {})
    
    print(f"🔍 DETALLES DE LA PREGUNTA {question_id}:")
    print("=" * 50)
    
    found_questions = []
    
    for cat_id, cat_data in categories.items():
        questions = cat_data.get('questions', [])
        for q in questions:
            if q.get('id') == question_id:
                found_questions.append({
                    'category': cat_id,
                    'category_name': cat_data.get('name', 'Sin nombre'),
                    'question': q
                })
    
    if not found_questions:
        print(f"❌ No se encontró la pregunta {question_id}")
        return
    
    for i, q_info in enumerate(found_questions, 1):
        print(f"\\n📝 OCURRENCIA {i}:")
        print(f"   Categoría: {q_info['category']} - {q_info['category_name']}")
        print(f"   Pregunta: {q_info['question']['question']}")
        print(f"   Opciones:")
        for letter, text in q_info['question'].get('options', {}).items():
            print(f"     {letter}) {text}")
        print(f"   Respuesta correcta: {q_info['question'].get('correct_answer', 'No asignada')}")

if __name__ == "__main__":
    yaml_file = "data/exams/per-test01-madrid-2024-noviembre.yaml"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--question" and len(sys.argv) > 2:
            question_id = int(sys.argv[2])
            show_specific_question(yaml_file, question_id)
        else:
            yaml_file = sys.argv[1]
            analyze_exam_questions(yaml_file)
    else:
        analyze_exam_questions(yaml_file)
