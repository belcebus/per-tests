#!/usr/bin/env python3
"""
Script para convertir el YAML actual al formato limpio sin redundancias
"""

import yaml

def clean_yaml_format():
    # Leer el archivo actual
    with open('/workspaces/per-tests/data/per_test_01.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Crear estructura limpia
    cleaned_data = {
        'exam_info': data.get('exam_info', {}),
        'categories': {}
    }
    
    # Procesar cada categoría
    for category_id, category_data in data.get('categories', {}).items():
        cleaned_questions = []
        
        # Limpiar cada pregunta eliminando redundancias
        for question in category_data.get('questions', []):
            cleaned_question = {
                'id': question.get('id'),
                'question': question.get('question'),
                'options': question.get('options'),
                'correct_answer': question.get('correct_answer')
            }
            cleaned_questions.append(cleaned_question)
        
        cleaned_data['categories'][category_id] = {
            'name': category_data.get('name'),
            'questions': cleaned_questions
        }
    
    # Guardar el archivo limpio
    with open('/workspaces/per-tests/data/per_test_01_clean.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(cleaned_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print("✅ Archivo limpio generado: per_test_01_clean.yaml")
    
    # Mostrar ejemplo del nuevo formato
    print("\n📝 Ejemplo del nuevo formato:")
    print("categories:")
    print("  1:")
    print("    name: Nomenclatura náutica")
    print("    questions:")
    print("    - id: 1")
    print("      question: '¿Cuál de las siguientes características NO es propia de la bocina?'")
    print("      options:")
    print("        a: Permite el movimiento del eje de la hélice.")
    print("        b: Transforma el movimiento circular de la hélice en empuje.")
    print("        c: Impide que entre el agua en la embarcación.")
    print("        d: Atraviesa el casco de la embarcación.")
    print("      correct_answer: b")
    print("\n✨ ¡Mucho más limpio! Sin redundancias de category/category_name")

if __name__ == "__main__":
    clean_yaml_format()
