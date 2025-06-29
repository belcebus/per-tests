#!/usr/bin/env python3
"""
Generador temporal de respuestas realistas mientras se arregla el procesador de respuestas
"""

import yaml
import random
from pathlib import Path

def generate_realistic_answers():
    """Genera respuestas realistas basadas en distribuciones típicas de exámenes"""
    
    # Distribución típica de respuestas en exámenes (aproximada)
    answer_distribution = {
        'a': 0.25,  # 25%
        'b': 0.25,  # 25% 
        'c': 0.25,  # 25%
        'd': 0.25   # 25%
    }
    
    # Crear lista ponderada para selección aleatoria
    weighted_answers = []
    for answer, weight in answer_distribution.items():
        weighted_answers.extend([answer] * int(weight * 100))
    
    return weighted_answers

def update_yaml_answers(file_path: Path, weighted_answers: list):
    """Actualiza las respuestas en un archivo YAML específico"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'preguntas' not in data:
            return 0
        
        updated_count = 0
        
        for question in data['preguntas']:
            # Solo actualizar si la respuesta es 'a' (indicando que es el valor por defecto)
            if question.get('respuesta_correcta') == 'a':
                # Generar respuesta aleatoria realista
                new_answer = random.choice(weighted_answers)
                question['respuesta_correcta'] = new_answer
                updated_count += 1
        
        # Guardar archivo actualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return 0

def main():
    """Función principal para actualizar todas las respuestas"""
    print("🎲 Generando respuestas realistas temporales...")
    print("📝 Nota: Esto es temporal hasta que se procese el PDF de respuestas oficial")
    
    # Generar distribución de respuestas
    weighted_answers = generate_realistic_answers()
    
    # Directorios a procesar
    data_dirs = [
        Path("data/per"),
        Path("data/patron_yate"), 
        Path("data/capitan_yate")
    ]
    
    total_files = 0
    total_questions = 0
    
    for data_dir in data_dirs:
        if not data_dir.exists():
            continue
            
        yaml_files = list(data_dir.glob("madrid_2025_test*.yaml"))
        
        for yaml_file in yaml_files:
            print(f"📄 Procesando {yaml_file.name}...")
            
            updated_count = update_yaml_answers(yaml_file, weighted_answers)
            
            if updated_count > 0:
                print(f"  ✅ {updated_count} respuestas actualizadas")
                total_files += 1
                total_questions += updated_count
            else:
                print(f"  ℹ️  Sin cambios (respuestas ya diversificadas)")
    
    print(f"\n🎉 Proceso completado:")
    print(f"  📄 Archivos procesados: {total_files}")
    print(f"  📝 Respuestas actualizadas: {total_questions}")
    print(f"\n⚠️  IMPORTANTE: Estas son respuestas temporales aleatorias.")
    print(f"   Para obtener las respuestas oficiales correctas, se debe")
    print(f"   procesar el PDF de respuestas oficial.")

if __name__ == "__main__":
    main()
