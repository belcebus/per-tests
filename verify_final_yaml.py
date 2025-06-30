#!/usr/bin/env python3
"""
Script de verificación final del YAML generado
"""

import yaml
import sys

def verify_yaml_format():
    """Verifica que el YAML tenga el formato correcto"""
    
    try:
        with open('/workspaces/per-tests/data/per_test_01.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        print("✅ YAML cargado correctamente")
        
        # Verificar estructura principal
        if 'exam_info' not in data:
            print("❌ Falta 'exam_info'")
            return False
        
        if 'categories' not in data:
            print("❌ Falta 'categories'")
            return False
        
        exam_info = data['exam_info']
        print(f"📋 Título: {exam_info.get('title', 'N/A')}")
        print(f"🏷️  Subtítulo: {exam_info.get('subtitle', 'N/A')}")
        print(f"❓ Preguntas: {exam_info.get('total_questions', 0)}")
        print(f"✅ Con respuesta: {exam_info.get('questions_with_answers', 0)}")
        
        # Verificar algunas preguntas específicas
        all_questions = []
        for cat_id, category in data['categories'].items():
            for question in category['questions']:
                all_questions.append(question)
        
        all_questions.sort(key=lambda x: x['id'])
        
        # Verificar formato de opciones
        format_errors = 0
        anuladas = 0
        
        for q in all_questions:
            if not isinstance(q['options'], dict):
                print(f"❌ Pregunta {q['id']}: opciones no es diccionario")
                format_errors += 1
                continue
            
            expected_keys = {'a', 'b', 'c', 'd'}
            actual_keys = set(q['options'].keys())
            
            if actual_keys != expected_keys:
                print(f"❌ Pregunta {q['id']}: opciones incorrectas. Esperadas: {expected_keys}, encontradas: {actual_keys}")
                format_errors += 1
            
            if q['correct_answer'] == 'ANULADA':
                anuladas += 1
            elif q['correct_answer'] not in ['a', 'b', 'c', 'd']:
                print(f"❌ Pregunta {q['id']}: respuesta incorrecta '{q['correct_answer']}'")
                format_errors += 1
        
        print(f"\n📊 RESUMEN DE VERIFICACIÓN:")
        print(f"   Total preguntas: {len(all_questions)}")
        print(f"   Preguntas anuladas: {anuladas}")
        print(f"   Errores de formato: {format_errors}")
        
        # Verificar preguntas específicas
        pregunta_1 = next((q for q in all_questions if q['id'] == 1), None)
        pregunta_45 = next((q for q in all_questions if q['id'] == 45), None)
        
        if pregunta_1:
            print(f"   Pregunta 1: {pregunta_1['correct_answer']} (debería ser ANULADA)")
        
        if pregunta_45:
            print(f"   Pregunta 45: {pregunta_45['correct_answer']} (debería ser ANULADA)")
        
        if format_errors == 0:
            print("\n🎉 ¡YAML VERIFICACIÓN EXITOSA! El formato es correcto.")
            return True
        else:
            print(f"\n❌ Se encontraron {format_errors} errores de formato.")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar YAML: {e}")
        return False

if __name__ == "__main__":
    success = verify_yaml_format()
    sys.exit(0 if success else 1)
