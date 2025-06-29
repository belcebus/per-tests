#!/usr/bin/env python3
"""
Script para verificar las preguntas cargadas
"""

import yaml
from pathlib import Path

def count_questions():
    data_dir = Path("data")
    total_questions = 0
    categories = {}
    
    print("🔍 Contando preguntas en archivos YAML...")
    
    # Buscar archivos YAML recursivamente
    yaml_files = list(data_dir.glob("**/*.yaml"))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if 'preguntas' in data:
                questions_count = len(data['preguntas'])
                category = data.get('metadata', {}).get('category', 'unknown')
                
                print(f"📄 {yaml_file.name}: {questions_count} preguntas ({category})")
                
                total_questions += questions_count
                
                if category in categories:
                    categories[category] += questions_count
                else:
                    categories[category] = questions_count
                    
        except Exception as e:
            print(f"❌ Error leyendo {yaml_file}: {e}")
    
    print(f"\n📊 RESUMEN:")
    print(f"Total de preguntas: {total_questions}")
    print(f"Categorías:")
    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count} preguntas")

if __name__ == "__main__":
    count_questions()
