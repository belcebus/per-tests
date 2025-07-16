#!/usr/bin/env python3
"""
Script para detectar automáticamente las opciones que tienen títulos de categorías concatenados incorrectamente
en TODOS los archivos de examen del proyecto.
Busca casos como "...por popa. Seguridad." y reporta un análisis completo.
"""

import yaml
import re
import os
import glob
from pathlib import Path
from collections import defaultdict

def detect_concatenated_categories(file_path):
    """
    Detecta pero NO corrige un archivo YAML, buscando títulos de categorías concatenados incorrectamente.
    Retorna una lista de problemas encontrados.
    """
    # Lista de títulos de categorías que pueden estar concatenados
    category_titles = [
        "Nomenclatura náutica",
        "Elementos de amarre y fondeo", 
        "Seguridad",
        "Legislación",
        "Balizamiento",
        "Reglamento (RIPA)",
        "Maniobra y navegación",
        "Emergencias en la mar",
        "Meteorología",
        "Teoría de la navegación",
        "Carta de navegación"
    ]
    
    problems = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [f"❌ Error leyendo archivo: {e}"]
    
    # Recorrer todas las categorías y preguntas
    for category_id, category_data in data.get('categories', {}).items():
        if not isinstance(category_data, dict):
            continue
        for question in category_data.get('questions', []):
            if not isinstance(question, dict):
                continue
            question_id = question.get('id')
            options = question.get('options', {})
            
            # Validar que options sea un diccionario
            if not isinstance(options, dict):
                continue
            
            # Revisar cada opción
            for option_letter, option_text in options.items():
                if not isinstance(option_text, str):
                    continue
                    
                # Buscar títulos de categorías concatenados al final
                for title in category_titles:
                    # Palabras que pueden preceder legítimamente a los títulos de categorías
                    legitimate_preceding_words = [
                        "de", "del", "la", "el", "una", "un", "para", "por", "con", "en",
                        "sobre", "hacia", "desde", "velocidad", "temperatura", "presión",
                        "nivel", "grado", "sistema", "equipo", "elemento", "zona", "área"
                    ]
                    
                    # Patrón 1: ". Título." al final (caso típico de concatenación)
                    pattern1 = rf'(.+)\.\s+{re.escape(title)}\.\s*$'
                    match1 = re.search(pattern1, option_text, re.IGNORECASE)
                    if match1:
                        # Verificar que no sea un caso legítimo
                        text_before = match1.group(1).strip()
                        words_before = text_before.split()
                        if len(words_before) > 0:
                            last_word = words_before[-1].lower()
                            # Si la última palabra es legítima con el título, no reportar
                            if last_word in legitimate_preceding_words and title.lower() in ["seguridad", "legislación", "balizamiento"]:
                                continue
                        
                        problems.append({
                            'type': 'concatenated_title',
                            'question_id': question_id,
                            'option': option_letter,
                            'title': title,
                            'pattern': f'". {title}."',
                            'text': option_text,
                            'suggested_fix': match1.group(1) + '.'
                        })
                        continue
                    
                    # Patrón 2: " Título." al final (solo si no hay preposición legítima antes)
                    pattern2 = rf'(.+)\s+{re.escape(title)}\.\s*$'
                    match2 = re.search(pattern2, option_text, re.IGNORECASE)
                    if match2:
                        text_before = match2.group(1).strip()
                        words_before = text_before.split()
                        if len(words_before) > 0:
                            last_word = words_before[-1].lower()
                            # Si la última palabra es legítima con el título, no reportar
                            if last_word in legitimate_preceding_words:
                                continue
                        
                        problems.append({
                            'type': 'concatenated_title',
                            'question_id': question_id,
                            'option': option_letter,
                            'title': title,
                            'pattern': f' {title}.',
                            'text': option_text,
                            'suggested_fix': match2.group(1) + '.'
                        })
                        continue
    
    return problems

def scan_all_exam_files():
    """
    Escanea todos los archivos de examen en busca de problemas de concatenación.
    """
    # Buscar todos los archivos YAML de examen
    exam_files = glob.glob("/Users/davidh/projects/per/per-tests/data/exams/questions/**/*.yaml", recursive=True)
    
    print(f"🔍 Escaneando {len(exam_files)} archivos de examen...")
    print("="*80)
    
    all_problems = {}
    total_problems = 0
    files_with_problems = 0
    
    # Estadísticas por categoría
    problems_by_category = defaultdict(int)
    problems_by_pattern = defaultdict(int)
    
    for file_path in sorted(exam_files):
        relative_path = file_path.replace("/Users/davidh/projects/per/per-tests/", "")
        print(f"📄 Escaneando: {relative_path}")
        
        problems = detect_concatenated_categories(file_path)
        
        if problems:
            all_problems[file_path] = problems
            files_with_problems += 1
            total_problems += len(problems)
            
            print(f"  ⚠️  {len(problems)} problemas encontrados:")
            for problem in problems:
                if problem.get('type') == 'concatenated_title':
                    print(f"    • Pregunta {problem['question_id']}, opción {problem['option']}: '{problem['title']}' concatenado")
                    print(f"      Texto: '{problem['text'][:100]}{'...' if len(problem['text']) > 100 else ''}'")
                    print(f"      Sugerencia: '{problem['suggested_fix'][:100]}{'...' if len(problem['suggested_fix']) > 100 else ''}'")
                    
                    # Estadísticas
                    problems_by_category[problem['title']] += 1
                    problems_by_pattern[problem['pattern']] += 1
                else:
                    print(f"    • {problem}")
            print()
        else:
            print(f"  ✅ No se encontraron problemas")
    
    print("="*80)
    print("📊 RESUMEN GLOBAL")
    print("="*80)
    
    print(f"📁 Archivos escaneados: {len(exam_files)}")
    print(f"⚠️  Archivos con problemas: {files_with_problems}")
    print(f"🚨 Total de problemas detectados: {total_problems}")
    
    if total_problems > 0:
        print(f"\n📈 ESTADÍSTICAS POR CATEGORÍA:")
        for category, count in sorted(problems_by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {category}: {count} problemas")
        
        print(f"\n🔍 ESTADÍSTICAS POR PATRÓN:")
        for pattern, count in sorted(problems_by_pattern.items(), key=lambda x: x[1], reverse=True):
            print(f"   • '{pattern}': {count} casos")
        
        print(f"\n📋 ARCHIVOS PROBLEMÁTICOS:")
        for file_path, problems in all_problems.items():
            relative_path = file_path.replace("/Users/davidh/projects/per/per-tests/", "")
            print(f"   • {relative_path}: {len(problems)} problemas")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   1. Usar el script fix_concatenated_categories.py para corregir automáticamente")
        print(f"   2. Revisar las correcciones manualmente antes de hacer commit")
        print(f"   3. Aplicar las mejoras del script de extracción a futuros PDFs")
        
        # Generar lista de archivos para el script de corrección
        print(f"\n🔧 ARCHIVOS PARA CORRECCIÓN (copiar al script fix_concatenated_categories.py):")
        print("problematic_files = [")
        for file_path in sorted(all_problems.keys()):
            print(f'    "{file_path}",')
        print("]")
    
    else:
        print(f"\n🎉 ¡Excelente! No se encontraron problemas de concatenación en ningún archivo.")
    
    return all_problems

def main():
    """
    Función principal que escanea todos los archivos de examen.
    """
    print("🚀 Iniciando escaneo global de categorías concatenadas...")
    print("🔍 Buscando títulos de categorías incorrectamente concatenados a opciones...")
    print()
    
    all_problems = scan_all_exam_files()
    
    print("\n✅ Escaneo completado.")
    
    if all_problems:
        print(f"⚠️  Se encontraron problemas en {len(all_problems)} archivos.")
        print("🔧 Usa el script fix_concatenated_categories.py para aplicar correcciones automáticas.")
    else:
        print("🎉 No se encontraron problemas de concatenación.")

if __name__ == "__main__":
    main()
