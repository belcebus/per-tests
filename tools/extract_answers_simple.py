#!/usr/bin/env python3
"""
Extractor directo de respuestas del PDF procesado
"""

import yaml
from pathlib import Path

def extract_answers_from_text_file():
    """Extrae respuestas del archivo de texto procesado"""
    
    with open('pdf_answers_full_text.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Dividir por páginas
    sections = content.split('=== PÁGINA')
    
    all_answers = {}
    
    for section in sections:
        if not section.strip():
            continue
        
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        # Identificar tipo de examen y test
        exam_type = None
        test_code = None
        
        for line in lines:
            if 'CAPITÁN DE YATE' in line:
                exam_type = 'capitan_yate'
            elif 'PATRÓN DE YATE' in line and 'EMBARCACIONES' not in line:
                exam_type = 'patron_yate'
            elif 'PATRÓN DE EMBARCACIONES DE RECREO' in line:
                exam_type = 'per'
            
            if 'Código de Test' in line and exam_type:
                import re
                match = re.search(r'(\d+)', line)
                if match:
                    test_code = match.group(1)
                    break
        
        if not exam_type or not test_code:
            continue
        
        # Extraer respuestas (formato: letra en una línea, número en la siguiente)
        answers = {}
        i = 0
        while i < len(lines) - 1:
            if lines[i] in ['A', 'B', 'C', 'D'] and lines[i+1].isdigit():
                question_num = int(lines[i+1])
                answer_letter = lines[i].lower()
                answers[question_num] = answer_letter
                i += 2
            else:
                i += 1
        
        if answers:
            exam_key = f"{exam_type}_test{test_code}"
            all_answers[exam_key] = answers
            print(f"✅ {exam_key}: {len(answers)} respuestas extraídas")
    
    return all_answers

def update_yaml_with_answers(all_answers):
    """Actualiza archivos YAML con respuestas extraídas"""
    
    print(f"\n🔄 Actualizando archivos YAML...")
    
    exam_dirs = {
        'capitan_yate': 'capitan_yate',
        'patron_yate': 'patron_yate',
        'per': 'per'
    }
    
    for exam_key, answers in all_answers.items():
        # Parsear exam_key
        parts = exam_key.split('_test')
        if len(parts) != 2:
            continue
        
        exam_type = parts[0]
        test_code = parts[1]
        
        if exam_type not in exam_dirs:
            continue
        
        # Buscar archivo YAML
        yaml_file = Path("data") / exam_dirs[exam_type] / f"madrid_2025_test{test_code}.yaml"
        
        if not yaml_file.exists():
            print(f"⚠️  No encontrado: {yaml_file}")
            continue
        
        # Actualizar archivo
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        updated = 0
        for question in data.get('preguntas', []):
            q_num = question['metadata']['numero_pregunta']
            if q_num in answers:
                old = question['respuesta_correcta']
                new = answers[q_num]
                if old != new:
                    question['respuesta_correcta'] = new
                    updated += 1
        
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"📝 {yaml_file.name}: {updated} respuestas actualizadas")

if __name__ == "__main__":
    print("🚢 EXTRACTOR DE RESPUESTAS OFICIALES")
    print("=" * 40)
    
    # Extraer respuestas
    all_answers = extract_answers_from_text_file()
    
    # Actualizar YAMLs
    if all_answers:
        update_yaml_with_answers(all_answers)
        print(f"\n✅ Proceso completado!")
    else:
        print("❌ No se pudieron extraer respuestas")
