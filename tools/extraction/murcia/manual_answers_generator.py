#!/usr/bin/env python3
"""
Generador manual de archivos JSON de respuestas para exámenes de Murcia
Solicita por línea de comandos las respuestas correctas para cada pregunta
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import os

def validate_answer_input(value):
    """Valida la entrada de respuesta del usuario - permite múltiples opciones"""
    value = value.lower().strip()
    
    # Casos especiales
    if value in ['anulada', 'atras', 'salir']:
        return value
    
    # Verificar que solo contiene letras válidas (a, b, c, d)
    valid_letters = set('abcd')
    input_letters = set(value)
    
    if not input_letters.issubset(valid_letters):
        invalid_chars = input_letters - valid_letters
        return f"error_invalid_chars_{invalid_chars}"
    
    if len(input_letters) == 0:
        return "error_empty"
    
    # Ordenar las letras para consistencia
    sorted_letters = ''.join(sorted(input_letters))
    return sorted_letters

def create_manual_answers_json():
    """Crea archivo JSON de respuestas manualmente"""
    
    print("🚢 GENERADOR MANUAL DE RESPUESTAS - MURCIA")
    print("="*60)
    
    # Solicitar año y convocatoria
    while True:
        year = input("📅 Año del examen (ej: 2024): ").strip()
        if year.isdigit() and 2015 <= int(year) <= 2030:
            break
        print("❌ Año inválido. Debe ser un número entre 2015 y 2030")
    
    # Convocatorias comunes como sugerencia
    convocatorias_comunes = ["marzo", "abril", "junio", "julio", "octubre", "noviembre", "diciembre"]
    
    print(f"📋 Convocatorias comunes: {convocatorias_comunes}")
    print("💡 También puedes introducir convocatorias específicas como: 9enero, 10enero, 17abril, 18abril, etc.")
    
    while True:
        convocatoria = input("📋 Convocatoria: ").strip().lower()
        
        # Validar que no esté vacía
        if not convocatoria:
            print("❌ La convocatoria no puede estar vacía")
            continue
            
        # Validar formato básico (letras y números, sin espacios ni caracteres especiales)
        import re
        if not re.match(r'^[a-z0-9]+$', convocatoria):
            print("❌ Formato inválido. Use solo letras y números, sin espacios ni caracteres especiales")
            print("   Ejemplos válidos: marzo, 9enero, 17abril, noviembre")
            continue
            
        # La convocatoria es válida
        break
    
    print(f"\n✅ Configuración: {year} - {convocatoria}")
    print("="*60)
    
    # Verificar si ya existe el archivo
    output_dir = Path(f"data/exams/answers/murcia/{year}")
    output_file = output_dir / f"per-test01-murcia-{year}-{convocatoria}.json"
    
    if output_file.exists():
        overwrite = input(f"⚠️  El archivo {output_file} ya existe. ¿Sobreescribir? (s/n): ").strip().lower()
        if overwrite != 's':
            print("Operación cancelada.")
            return
    
    # Crear directorio si no existe
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Cargar preguntas desde el archivo YAML de preguntas (si existe)
    questions_file = Path(f"data/exams/questions/murcia/{year}/per-test01-murcia-{year}-{convocatoria}.yaml")
    questions_text = {}
    
    if questions_file.exists():
        print(f"📄 Archivo de preguntas encontrado: {questions_file}")
        try:
            import yaml
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions_data = yaml.safe_load(f)
            
            # Extraer texto de preguntas para mostrar
            for category_id, category_data in questions_data.get('categories', {}).items():
                for question in category_data.get('questions', []):
                    q_id = question.get('id')
                    q_text = question.get('question', '')
                    questions_text[q_id] = q_text[:100] + "..." if len(q_text) > 100 else q_text
        except ImportError:
            print("⚠️  PyYAML no instalado, continuando sin mostrar preguntas")
        except Exception as e:
            print(f"⚠️  Error cargando preguntas: {e}")
    else:
        print(f"⚠️  No se encontró archivo de preguntas en: {questions_file}")
    
    print("\n🎯 INTRODUCIENDO RESPUESTAS CORRECTAS")
    print("="*60)
    print("Para cada pregunta, introduce la(s) letra(s) de la(s) respuesta(s) correcta(s):")
    print("  - Una sola respuesta: a, b, c, d")
    print("  - Múltiples respuestas: abc, bd, ac, etc.")
    print("  - Pregunta anulada: anulada")
    print("También puedes usar 'atras' para volver a la pregunta anterior, 'salir' para cancelar")
    print("="*60)
    
    answers = {}
    current_question = 1
    
    while current_question <= 45:
        # Mostrar información de la pregunta si está disponible
        if current_question in questions_text:
            print(f"\n📝 Q{current_question}: {questions_text[current_question]}")
        
        prompt = f"Q{current_question:2d}/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): "
        user_input = input(prompt).strip().lower()
        
        # Comandos especiales
        if user_input == 'salir':
            print("❌ Operación cancelada por el usuario")
            return
        elif user_input == 'atras' and current_question > 1:
            current_question -= 1
            if str(current_question) in answers:
                del answers[str(current_question)]
            continue
        elif user_input == 'atras' and current_question == 1:
            print("⚠️  Ya estás en la primera pregunta")
            continue
        
        # Validar respuesta
        validated_answer = validate_answer_input(user_input)
        
        if validated_answer.startswith('error_invalid_chars_'):
            invalid_chars = validated_answer.replace('error_invalid_chars_', '').strip('{}')
            print(f"❌ Caracteres inválidos: {invalid_chars}. Solo usa: a, b, c, d, anulada, atras, salir")
            continue
        elif validated_answer == 'error_empty':
            print("❌ Respuesta vacía. Usa: a, b, c, d, abc, bd, anulada, atras, salir")
            continue
        elif validated_answer in ['anulada', 'atras', 'salir']:
            if validated_answer == 'anulada':
                answers[str(current_question)] = 'anulada'
                current_question += 1
            # atras y salir ya se manejan arriba
        else:
            # Es una respuesta válida (una o múltiples letras)
            if len(validated_answer) == 1:
                answers[str(current_question)] = validated_answer
            else:
                # Múltiples respuestas - convertir a array
                answers[str(current_question)] = list(validated_answer)
            current_question += 1
    
    # Confirmar todas las respuestas
    print("\n📋 RESUMEN DE RESPUESTAS INTRODUCIDAS:")
    print("="*60)
    
    # Mostrar en grupos de 5
    for i in range(0, 45, 5):
        line_answers = []
        for j in range(i + 1, min(i + 6, 46)):
            answer = answers.get(str(j), '?')
            # Formatear respuesta para mostrar
            if isinstance(answer, list):
                answer_str = ''.join(answer)
            else:
                answer_str = answer
            line_answers.append(f"Q{j:2d}:{answer_str}")
        print(" | ".join(line_answers))
    
    # Contar distribución
    distribution = {}
    single_answers = 0
    multiple_answers = 0
    anuladas = 0
    
    for answer in answers.values():
        if answer == 'anulada':
            anuladas += 1
            distribution['anulada'] = distribution.get('anulada', 0) + 1
        elif isinstance(answer, list):
            multiple_answers += 1
            key = ''.join(answer)
            distribution[f'múltiple:{key}'] = distribution.get(f'múltiple:{key}', 0) + 1
            # También contar cada letra individual para estadísticas
            for letter in answer:
                distribution[letter] = distribution.get(letter, 0) + 1
        else:
            single_answers += 1
            distribution[answer] = distribution.get(answer, 0) + 1
    
    print(f"\n📊 Distribución: {dict(sorted(distribution.items()))}")
    print(f"📈 Resumen: {single_answers} simples, {multiple_answers} múltiples, {anuladas} anuladas")
    
    confirm = input("\n✅ ¿Confirmar y generar archivo JSON? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Operación cancelada")
        return
    
    # Generar estructura JSON
    json_data = {
        "exam_type": "PER",
        "test_model": "TEST01",
        "total_answers": 45,
        "answers": answers,
        "source_pdf": f"murcia-{year}-{convocatoria}.pdf",
        "generated_at": datetime.now().isoformat(),
        "pdf_info": {
            "comunidad": "murcia",
            "año": year,
            "convocatoria": convocatoria
        }
    }
    
    # Guardar archivo
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 ÉXITO: Archivo generado correctamente")
        print(f"📁 Ubicación: {output_file}")
        print(f"📊 Total respuestas: {len(answers)}")
        print(f"📈 Resumen: {single_answers} simples, {multiple_answers} múltiples, {anuladas} anuladas")
        
    except Exception as e:
        print(f"❌ Error guardando archivo: {e}")

def batch_mode():
    """Modo batch para procesar múltiples exámenes"""
    print("🚢 MODO BATCH - MÚLTIPLES EXÁMENES")
    print("="*60)
    
    # Mostrar exámenes disponibles
    questions_base = Path("data/exams/questions/murcia")
    if not questions_base.exists():
        print(f"❌ No se encontró directorio: {questions_base}")
        return
    
    available_exams = []
    for year_dir in sorted(questions_base.iterdir()):
        if year_dir.is_dir():
            for yaml_file in year_dir.glob("*.yaml"):
                # Extraer información del nombre del archivo
                filename = yaml_file.stem  # per-test01-murcia-2024-marzo
                parts = filename.split('-')
                if len(parts) >= 5:
                    year = parts[3]
                    convocatoria = parts[4]
                    
                    # Verificar si ya existe el JSON
                    json_file = Path(f"data/exams/answers/murcia/{year}/per-test01-murcia-{year}-{convocatoria}.json")
                    status = "✅" if json_file.exists() else "❌"
                    
                    available_exams.append({
                        "year": year,
                        "convocatoria": convocatoria,
                        "yaml_file": yaml_file,
                        "json_file": json_file,
                        "exists": json_file.exists(),
                        "status": status
                    })
    
    if not available_exams:
        print("❌ No se encontraron exámenes de Murcia")
        return
    
    print(f"\n📚 EXÁMENES DISPONIBLES ({len(available_exams)} total):")
    print("="*60)
    
    for i, exam in enumerate(available_exams, 1):
        print(f"{i:2d}. {exam['status']} {exam['year']}-{exam['convocatoria']}")
    
    pending_exams = [exam for exam in available_exams if not exam['exists']]
    if pending_exams:
        print(f"\n⏳ PENDIENTES DE PROCESAR: {len(pending_exams)}")
        for exam in pending_exams:
            print(f"  - {exam['year']}-{exam['convocatoria']}")
    
    completed_exams = [exam for exam in available_exams if exam['exists']]
    if completed_exams:
        print(f"\n✅ YA COMPLETADOS: {len(completed_exams)}")

def main():
    parser = argparse.ArgumentParser(description="Generador manual de respuestas para exámenes de Murcia")
    parser.add_argument("--batch", action="store_true", help="Mostrar estado de todos los exámenes")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_mode()
    else:
        create_manual_answers_json()

if __name__ == "__main__":
    main()
