#!/usr/bin/env python3
"""
Script para aplicar respuestas extraídas por OCR al archivo YAML correspondiente
"""

import json
import yaml
import sys
import os
import argparse
from pathlib import Path
from typing import Dict

# Añadir el directorio del proyecto al path para importaciones
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import settings

def load_extracted_answers(answers_file: str = None) -> Dict[str, str]:
    """Carga las respuestas extraídas del archivo JSON"""
    if answers_file is None:
        # Intentar buscar el archivo con el nuevo patrón de nomenclatura primero
        extracted_dir = settings.get_extracted_path()
        
        # Buscar archivos que sigan el patrón per-test01-*.json
        pattern_files = list(extracted_dir.glob("per-test01-*.json"))
        
        if pattern_files:
            # Usar el primer archivo encontrado con el nuevo patrón
            answers_file = pattern_files[0]
            print(f"📄 Usando archivo con patrón nuevo: {answers_file.name}")
        else:
            # Fallback al archivo de compatibilidad
            answers_file = extracted_dir / "per_test01_answers.json"
            print(f"📄 Usando archivo de compatibilidad: {answers_file.name}")
    else:
        answers_file = Path(answers_file)
    
    if not answers_file.exists():
        raise FileNotFoundError(f"Archivo de respuestas no encontrado: {answers_file}")
    
    with open(answers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['answers']

def apply_answers_to_yaml(yaml_file: Path, extracted_answers: Dict[str, str]) -> int:
    """Aplica las respuestas extraídas al archivo YAML"""
    print(f"📝 Procesando {yaml_file.name}...")
    
    # Crear backup del archivo original en el directorio de backups
    backup_dir = settings.get_backups_path()
    backup_dir.mkdir(parents=True, exist_ok=True)  # Crear directorio si no existe
    backup_file = backup_dir / f"{yaml_file.stem}.yaml.backup"
    
    if not backup_file.exists():
        # Copiar el archivo original al directorio de backups
        import shutil
        shutil.copy2(yaml_file, backup_file)
        print(f"💾 Backup creado: {backup_file.name}")
    else:
        print(f"💾 Backup ya existe: {backup_file.name}")
    
    # Cargar el archivo YAML original
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    updates_count = 0
    questions_found = 0
    
    # Procesar cada categoría y pregunta
    # Intentar ambas estructuras: 'categories' y 'pycategories'
    categories_data = data.get('categories', data.get('pycategories', {}))
    
    for category_id, category_data in categories_data.items():
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
    parser = argparse.ArgumentParser(
        description="Aplicar respuestas extraídas por OCR al archivo YAML correspondiente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EJEMPLOS DE USO:

  # Aplicar respuestas usando auto-detección de archivos
  python madrid_merge_exam.py

  # Especificar archivo de respuestas específico
  python madrid_merge_exam.py --answers-file per-test01-madrid-2025-abril.json

  # Especificar tanto archivo de respuestas como YAML objetivo
  python madrid_merge_exam.py --answers-file per-test01-madrid-2025-abril.json --yaml-file per-test01-madrid-2025-abril.yaml
        """
    )
    
    parser.add_argument(
        '--answers-file',
        type=str,
        help='Archivo JSON con las respuestas extraídas (default: auto-detectar)'
    )
    
    parser.add_argument(
        '--yaml-file',
        type=str,
        help='Archivo YAML del examen a actualizar (default: per-test01-madrid-2025-abril.yaml)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Aplicando respuestas OCR al archivo YAML correspondiente...")
    
    try:
        # Cargar respuestas extraídas
        extracted_answers = load_extracted_answers(args.answers_file)
        print(f"📖 Respuestas cargadas: {len(extracted_answers)}")
        
        # Validar respuestas
        validate_answers(extracted_answers)
        
        # Determinar archivo YAML objetivo
        if args.yaml_file:
            yaml_file = Path(args.yaml_file)
            # Si la ruta no es absoluta y no incluye la carpeta base, añadir la ruta de exámenes
            if not yaml_file.is_absolute() and not str(yaml_file).startswith('data/exams'):
                yaml_file = settings.get_exams_path() / args.yaml_file
        else:
            yaml_file = settings.get_exams_path() / "per-test01-madrid-2025-abril.yaml"
        
        if not yaml_file.exists():
            print(f"❌ Archivo YAML no encontrado: {yaml_file}")
            return
        
        updates = apply_answers_to_yaml(yaml_file, extracted_answers)
        
        print(f"\n🎉 Proceso completado exitosamente!")
        print(f"   📈 Total actualizaciones: {updates}")
        
        if updates > 0:
            print("\n💡 Recomendaciones:")
            print("   - Reinicia el servidor de la aplicación para cargar los cambios")
            print("   - Verifica algunas respuestas manualmente para confirmar la precisión")
            print("   - El archivo original se guardó como .backup")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
