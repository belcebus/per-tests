#!/usr/bin/env python3
"""
Procesador de respuestas del PDF
"""

import fitz
import re
import yaml
from pathlib import Path

def analyze_answers_pdf():
    """Analiza el PDF de respuestas para entender su estructura"""
    print("🔍 Analizando PDF de respuestas...")
    
    doc = fitz.open("pdfs/madrid-2025-resp.pdf")
    print(f"📄 Páginas en PDF de respuestas: {len(doc)}")
    
    # Analizar las primeras páginas
    for page_num in range(min(5, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n=== PÁGINA {page_num + 1} ===")
        
        # Buscar patrones de respuestas
        answer_patterns = [
            r'\d+-[abcd]',  # Formato "1-a"
            r'\d+\)\s*[abcd]',  # Formato "1) a"
            r'\d+\.\s*[abcd]',  # Formato "1. a"
            r'[abcd]\)',  # Solo "a)"
            r'Test\s*\d+',  # "Test 01"
            r'Código\s*de\s*Test\s*\d+',  # "Código de Test 01"
        ]
        
        found_patterns = {}
        for pattern in answer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_patterns[pattern] = matches[:10]  # Primeros 10
        
        if found_patterns:
            print("🎯 Patrones encontrados:")
            for pattern, matches in found_patterns.items():
                print(f"  {pattern}: {matches}")
        
        # Mostrar una muestra del texto
        print("📝 Muestra de texto:")
        lines = text.split('\n')[:15]  # Primeras 15 líneas
        for line in lines:
            if line.strip():
                print(f"  {line.strip()}")
        
        print("-" * 50)
    
    doc.close()

def extract_answers_by_manual_inspection():
    """Extrae respuestas manualmente inspeccionando el PDF completo"""
    print("\n🔧 Extrayendo respuestas por inspección manual...")
    
    doc = fitz.open("pdfs/madrid-2025-resp.pdf")
    all_answers = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Buscar diferentes formatos de respuesta
        # Formato "1-a", "2-b", etc.
        answer_matches = re.finditer(r'(\d+)-([abcd])', text)
        for match in answer_matches:
            question_num = int(match.group(1))
            answer = match.group(2)
            all_answers[question_num] = answer
        
        # Formato "1) a", "2) b", etc. (con espacio)
        answer_matches = re.finditer(r'(\d+)\)\s*([abcd])', text)
        for match in answer_matches:
            question_num = int(match.group(1))
            answer = match.group(2)
            all_answers[question_num] = answer
        
        # Formato "1)a", "2)b", etc. (sin espacio)
        answer_matches = re.finditer(r'(\d+)\)([abcd])', text)
        for match in answer_matches:
            question_num = int(match.group(1))
            answer = match.group(2)
            all_answers[question_num] = answer
    
    doc.close()
    
    print(f"✅ {len(all_answers)} respuestas extraídas")
    
    if all_answers:
        # Mostrar algunas respuestas de ejemplo
        sample_answers = dict(list(all_answers.items())[:10])
        print("📋 Muestra de respuestas:")
        for q_num, answer in sample_answers.items():
            print(f"  Pregunta {q_num}: {answer}")
        
        # Mostrar estadísticas
        answer_counts = {}
        for answer in all_answers.values():
            answer_counts[answer] = answer_counts.get(answer, 0) + 1
        
        print(f"📊 Distribución de respuestas:")
        for answer, count in sorted(answer_counts.items()):
            percentage = (count / len(all_answers)) * 100
            print(f"  {answer}: {count} ({percentage:.1f}%)")
    
    return all_answers

def update_yaml_files_with_answers(all_answers):
    """Actualiza los archivos YAML con las respuestas correctas"""
    print(f"\n🔄 Actualizando archivos YAML con respuestas...")
    
    data_dirs = ["capitan_yate", "patron_yate", "per"]
    updated_files = 0
    updated_questions = 0
    
    for dir_name in data_dirs:
        data_dir = Path("data") / dir_name
        if not data_dir.exists():
            continue
        
        yaml_files = list(data_dir.glob("madrid_2025_test*.yaml"))
        
        for yaml_file in yaml_files:
            print(f"📝 Procesando {yaml_file.name}...")
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                questions_updated = 0
                
                for question in data.get('preguntas', []):
                    q_num = question['metadata']['numero_pregunta']
                    
                    if q_num in all_answers:
                        old_answer = question['respuesta_correcta']
                        new_answer = all_answers[q_num]
                        
                        if old_answer != new_answer:
                            question['respuesta_correcta'] = new_answer
                            questions_updated += 1
                
                if questions_updated > 0:
                    # Guardar archivo actualizado
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    
                    print(f"  ✅ {questions_updated} preguntas actualizadas")
                    updated_files += 1
                    updated_questions += questions_updated
                else:
                    print(f"  ℹ️  Sin cambios necesarios")
                    
            except Exception as e:
                print(f"  ❌ Error procesando {yaml_file}: {e}")
    
    print(f"\n🎉 Actualización completada:")
    print(f"  📄 Archivos actualizados: {updated_files}")
    print(f"  📝 Preguntas actualizadas: {updated_questions}")

if __name__ == "__main__":
    # Analizar estructura del PDF de respuestas
    analyze_answers_pdf()
    
    # Extraer todas las respuestas
    all_answers = extract_answers_by_manual_inspection()
    
    # Actualizar archivos YAML si se encontraron respuestas
    if all_answers:
        update_yaml_files_with_answers(all_answers)
    else:
        print("❌ No se encontraron respuestas para actualizar")
