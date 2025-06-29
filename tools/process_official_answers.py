#!/usr/bin/env python3
"""
Procesador de respuestas oficiales del PDF
"""

import re
import yaml
from pathlib import Path
from collections import defaultdict

def parse_answers_from_text():
    """Extrae las respuestas del texto ya extraído del PDF"""
    print("🔍 Procesando respuestas del PDF oficial...")
    
    with open('/workspaces/per-tests/pdf_answers_full_text.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Dividir en secciones por páginas
    pages = content.split('=== PÁGINA')
    
    answers_by_exam = {}
    
    for page in pages:
        if not page.strip():
            continue
            
        lines = page.strip().split('\n')
        
        # Buscar el encabezado del examen
        exam_header = None
        test_code = None
        
        for line in lines:
            if 'Respuestas al EXAMEN DE' in line:
                exam_header = line.strip()
                continue
            if 'Código de Test' in line:
                test_match = re.search(r'Código de Test (\d+)', line)
                if test_match:
                    test_code = test_match.group(1)
                break
        
        if not exam_header or not test_code:
            continue
        
        # Determinar tipo de examen
        if 'CAPITÁN DE YATE' in exam_header:
            exam_type = 'capitan_yate'
        elif 'PATRÓN DE YATE' in exam_header:
            exam_type = 'patron_yate'
        elif 'PATRÓN DE EMBARCACIONES DE RECREO' in exam_header:
            exam_type = 'per'
        elif 'PATRÓN PARA NAVEGACIÓN BÁSICA' in exam_header:
            exam_type = 'pnb'  # No lo usamos actualmente
        else:
            continue
        
        exam_key = f"{exam_type}_test{test_code}"
        
        # Extraer respuestas
        answers = {}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Si la línea es una letra (A, B, C, D), la siguiente debería ser un número
            if line in ['A', 'B', 'C', 'D'] and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.isdigit():
                    question_num = int(next_line)
                    answers[question_num] = line.lower()
                    i += 2  # Saltar ambas líneas
                else:
                    i += 1
            else:
                i += 1
        
        if answers:
            answers_by_exam[exam_key] = answers
            print(f"✅ {exam_key}: {len(answers)} respuestas extraídas")
    
    return answers_by_exam

def update_yaml_files_with_official_answers(answers_by_exam):
    """Actualiza los archivos YAML con las respuestas oficiales"""
    print(f"\n🔄 Actualizando archivos YAML con respuestas oficiales...")
    
    # Mapeo de tipos de examen a directorios
    exam_to_dir = {
        'capitan_yate': 'capitan_yate',
        'patron_yate': 'patron_yate', 
        'per': 'per'
    }
    
    updated_files = 0
    updated_questions = 0
    
    for exam_key, answers in answers_by_exam.items():
        # Parsear el exam_key para obtener tipo y test
        if '_test' not in exam_key:
            continue
            
        exam_type, test_part = exam_key.split('_test')
        test_code = test_part
        
        if exam_type not in exam_to_dir:
            print(f"⚠️  Tipo de examen no reconocido: {exam_type}")
            continue
        
        # Buscar archivo YAML correspondiente
        data_dir = Path("data") / exam_to_dir[exam_type]
        yaml_file = data_dir / f"madrid_2025_test{test_code}.yaml"
        
        if not yaml_file.exists():
            print(f"⚠️  Archivo no encontrado: {yaml_file}")
            continue
        
        print(f"📝 Procesando {yaml_file.name}...")
        
        try:
            # Cargar archivo YAML
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            questions_updated = 0
            
            # Actualizar respuestas
            for question in data.get('preguntas', []):
                q_num = question['metadata']['numero_pregunta']
                
                if q_num in answers:
                    old_answer = question['respuesta_correcta']
                    new_answer = answers[q_num]
                    
                    if old_answer != new_answer:
                        question['respuesta_correcta'] = new_answer
                        questions_updated += 1
            
            # Guardar archivo actualizado
            if questions_updated > 0:
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                print(f"  ✅ {questions_updated} respuestas actualizadas")
                updated_files += 1
                updated_questions += questions_updated
            else:
                print(f"  ℹ️  Sin cambios necesarios")
                
        except Exception as e:
            print(f"  ❌ Error procesando {yaml_file}: {e}")
    
    print(f"\n🎉 Actualización de respuestas completada:")
    print(f"  📄 Archivos actualizados: {updated_files}")
    print(f"  📝 Preguntas con respuestas corregidas: {updated_questions}")

def verify_answer_distribution():
    """Verifica la distribución de respuestas para validar que son realistas"""
    print(f"\n📊 Verificando distribución de respuestas...")
    
    data_dirs = ["capitan_yate", "patron_yate", "per"]
    
    for dir_name in data_dirs:
        data_dir = Path("data") / dir_name
        if not data_dir.exists():
            continue
            
        print(f"\n📁 {dir_name.upper()}:")
        
        yaml_files = list(data_dir.glob("madrid_2025_test*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                # Contar distribución de respuestas
                answer_counts = defaultdict(int)
                total_questions = 0
                
                for question in data.get('preguntas', []):
                    answer = question.get('respuesta_correcta', '')
                    if answer:
                        answer_counts[answer] += 1
                        total_questions += 1
                
                if total_questions > 0:
                    print(f"  {yaml_file.name} ({total_questions} preguntas):")
                    for letter in ['a', 'b', 'c', 'd']:
                        count = answer_counts[letter]
                        percentage = (count / total_questions) * 100
                        print(f"    {letter}: {count} ({percentage:.1f}%)")
                
            except Exception as e:
                print(f"  ❌ Error leyendo {yaml_file}: {e}")

if __name__ == "__main__":
    print("🚢 PROCESADOR DE RESPUESTAS OFICIALES")
    print("=" * 50)
    
    # Extraer respuestas del texto
    answers_by_exam = parse_answers_from_text()
    
    if not answers_by_exam:
        print("❌ No se pudieron extraer respuestas")
        exit(1)
    
    # Mostrar resumen
    print(f"\n📋 RESUMEN DE RESPUESTAS EXTRAÍDAS:")
    for exam_key, answers in answers_by_exam.items():
        print(f"  {exam_key}: {len(answers)} respuestas")
    
    # Actualizar archivos YAML
    update_yaml_files_with_official_answers(answers_by_exam)
    
    # Verificar distribución
    verify_answer_distribution()
    
    print(f"\n✅ Proceso completado. Las respuestas oficiales han sido aplicadas.")
