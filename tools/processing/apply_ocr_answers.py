#!/usr/bin/env python3
"""
Script para aplicar respuestas extraídas por OCR al archivo YAML de Madrid PER Test 01
"""

import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict

# Añadir el directorio del proyecto al path para importaciones
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import settings

def load_extracted_answers() -> Dict[str, str]:
    """Carga las respuestas extraídas del archivo JSON"""
    answers_file = settings.get_extracted_path() / "per_test01_answers.json"
    
    if not answers_file.exists():
        raise FileNotFoundError(f"Archivo de respuestas no encontrado: {answers_file}")
    
    with open(answers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['answers']

def apply_answers_to_yaml(yaml_file: Path, extracted_answers: Dict[str, str]) -> int:
    """Aplica las respuestas extraídas al archivo YAML"""
    print(f"📝 Procesando {yaml_file.name}...")
    
    # Crear backup del archivo original
    backup_file = yaml_file.with_suffix('.yaml.backup')
    if not backup_file.exists():
        yaml_file.rename(backup_file)
        yaml_file = backup_file.with_suffix('.yaml')
        print(f"💾 Backup creado: {backup_file.name}")
    
    # Cargar el archivo YAML
    with open(backup_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    updates_count = 0
    questions_found = 0
    
    # Procesar cada categoría y pregunta
    for category_id, category_data in data.get('categories', {}).items():
        questions = category_data.get('questions', [])
        
        for question in questions:
            question_id = question.get('id')
            questions_found += 1
            
            if question_id and str(question_id) in extracted_answers:
                old_answer = question.get('correct_answer', 'N/A')
                new_answer = extracted_answers[str(question_id)]
                
                # Aplicar la nueva respuesta
                question['correct_answer'] = new_answer
                
                # Mostrar el cambio
                if old_answer != new_answer:
                    print(f"   🔄 Pregunta {question_id}: {old_answer} → {new_answer}")
                    updates_count += 1
                else:
                    print(f"   ✅ Pregunta {question_id}: {new_answer} (sin cambios)")
    
    # Guardar el archivo actualizado
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\\n📊 RESUMEN:")
    print(f"   📄 Preguntas encontradas en YAML: {questions_found}")
    print(f"   🔄 Respuestas actualizadas: {updates_count}")
    print(f"   📁 Archivo actualizado: {yaml_file}")
    
    return updates_count

def validate_answers(extracted_answers: Dict[str, str]):
    """Valida las respuestas extraídas"""
    print("🔍 Validando respuestas extraídas...")
    
    valid_answers = {'a', 'b', 'c', 'd', 'ANULADA'}
    total_answers = len(extracted_answers)
    valid_count = 0
    
    for q_id, answer in extracted_answers.items():
        if answer.lower() in [v.lower() for v in valid_answers]:
            valid_count += 1
        else:
            print(f"   ⚠️  Pregunta {q_id}: respuesta inválida '{answer}'")
    
    print(f"   ✅ Respuestas válidas: {valid_count}/{total_answers}")
    
    # Mostrar resumen de respuestas
    answer_counts = {}
    for answer in extracted_answers.values():
        answer_counts[answer] = answer_counts.get(answer, 0) + 1
    
    print("   📊 Distribución de respuestas:")
    for answer, count in sorted(answer_counts.items()):
        print(f"      {answer}: {count}")

def main():
    """Función principal"""
    print("🚀 Aplicando respuestas OCR al archivo YAML de Madrid PER Test 01...")
    
    try:
        # Cargar respuestas extraídas
        extracted_answers = load_extracted_answers()
        print(f"📖 Respuestas cargadas: {len(extracted_answers)}")
        
        # Validar respuestas
        validate_answers(extracted_answers)
        
        # Aplicar al archivo YAML
        yaml_file = settings.get_exams_path() / "per_madrid_2025_ordinaria_test01.yaml"
        
        if not yaml_file.exists():
            print(f"❌ Archivo YAML no encontrado: {yaml_file}")
            return
        
        updates = apply_answers_to_yaml(yaml_file, extracted_answers)
        
        print(f"\\n🎉 Proceso completado exitosamente!")
        print(f"   📈 Total actualizaciones: {updates}")
        
        if updates > 0:
            print("\\n💡 Recomendaciones:")
            print("   - Reinicia el servidor de la aplicación para cargar los cambios")
            print("   - Verifica algunas respuestas manualmente para confirmar la precisión")
            print("   - El archivo original se guardó como .backup")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
