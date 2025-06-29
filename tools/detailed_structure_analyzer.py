#!/usr/bin/env python3
"""
Análisis detallado de la estructura de exámenes
"""

import fitz
import re

def analyze_exam_structure():
    print("🔍 Análisis detallado de la estructura...")
    
    doc = fitz.open("pdfs/madrid-2025.pdf")
    
    # Páginas clave identificadas
    key_pages = {
        'CAPITÁN DE YATE': [1, 19],
        'PATRÓN DE YATE': [36, 47],
        'PATRÓN DE EMBARCACIONES DE RECREO': [59, 72, 85, 98, 111, 115]
    }
    
    exam_sections = []
    
    for exam_type, pages in key_pages.items():
        print(f"\n🎯 Analizando {exam_type}")
        
        for page_num in pages:
            page = doc[page_num - 1]  # PyMuPDF usa índices 0-based
            text = page.get_text()
            
            # Buscar código de test
            test_code_match = re.search(r'Código de Test (\d+)', text)
            test_code = test_code_match.group(1) if test_code_match else "desconocido"
            
            # Buscar primera pregunta para entender la numeración
            first_question_match = re.search(r'^\s*(\d+)\s+(.{20,80})', text, re.MULTILINE)
            first_question_num = first_question_match.group(1) if first_question_match else "?"
            
            print(f"  📄 Página {page_num}:")
            print(f"    - Código de Test: {test_code}")
            print(f"    - Primera pregunta: #{first_question_num}")
            
            # Contar preguntas en esta página
            question_matches = re.findall(r'^\s*(\d+)\s+', text, re.MULTILINE)
            print(f"    - Preguntas en página: {len(question_matches)}")
            
            if question_matches:
                print(f"    - Rango de preguntas: {question_matches[0]} - {question_matches[-1]}")
            
            exam_sections.append({
                'exam_type': exam_type,
                'page': page_num,
                'test_code': test_code,
                'first_question': first_question_num,
                'questions_in_page': len(question_matches)
            })
    
    # Determinar rangos completos
    print(f"\n📊 RANGOS ESTIMADOS POR TIPO DE EXAMEN:")
    
    exam_ranges = {}
    for exam_type in key_pages.keys():
        sections = [s for s in exam_sections if s['exam_type'] == exam_type]
        if sections:
            first_questions = [int(s['first_question']) for s in sections if s['first_question'].isdigit()]
            if first_questions:
                min_q = min(first_questions)
                max_q = max(first_questions) + 20  # Estimación conservadora
                exam_ranges[exam_type] = (min_q, max_q)
                print(f"  {exam_type}: preguntas {min_q} - {max_q}")
    
    doc.close()
    return exam_ranges

def identify_question_ranges_by_content():
    """Identifica rangos de preguntas analizando el contenido completo"""
    print(f"\n🔢 Identificando rangos de preguntas por contenido...")
    
    doc = fitz.open("pdfs/madrid-2025.pdf")
    
    all_questions = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Encontrar todas las preguntas numeradas
        question_matches = re.finditer(r'^\s*(\d+)\s+(.{10,100})', text, re.MULTILINE)
        for match in question_matches:
            question_num = int(match.group(1))
            question_text = match.group(2).strip()
            
            all_questions.append({
                'number': question_num,
                'page': page_num + 1,
                'text': question_text
            })
    
    # Agrupar por rangos
    all_questions.sort(key=lambda x: x['number'])
    
    print(f"Total de preguntas encontradas: {len(all_questions)}")
    
    if all_questions:
        print(f"Rango completo: {all_questions[0]['number']} - {all_questions[-1]['number']}")
        
        # Mostrar distribución
        ranges = [
            (1, 30, "CAPITÁN DE YATE (estimado)"),
            (31, 60, "PATRÓN DE YATE (estimado)"),
            (61, 135, "PER (estimado)")
        ]
        
        for start, end, label in ranges:
            questions_in_range = [q for q in all_questions if start <= q['number'] <= end]
            if questions_in_range:
                pages = sorted(set(q['page'] for q in questions_in_range))
                print(f"  {label}: {len(questions_in_range)} preguntas, páginas {pages[0]}-{pages[-1]}")
    
    doc.close()
    return all_questions

if __name__ == "__main__":
    exam_ranges = analyze_exam_structure()
    all_questions = identify_question_ranges_by_content()
