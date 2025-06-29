#!/usr/bin/env python3
"""
Script para procesar únicamente las preguntas de PER del primer modelo de examen,
clasificándolas por categorías oficiales.
"""

import fitz  # PyMuPDF
import yaml
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Categorías oficiales de PER según especificación del usuario
PER_CATEGORIES = {
    1: "Nomenclatura náutica",
    2: "Elementos de amarre y fondeo",
    3: "Seguridad",
    4: "Legislación",
    5: "Balizamiento",
    6: "Reglamento (RIPA)",
    7: "Maniobra y navegación",
    8: "Emergencias en la mar",
    9: "Meteorología",
    10: "Teoría de la navegación",
    11: "Carta de navegación"
}

class PERProcessor:
    def __init__(self):
        self.questions = []
        self.answers = {}
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae todo el texto del PDF."""
        print(f"Extrayendo texto de {pdf_path}")
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def classify_question_by_content(self, question_text: str) -> int:
        """
        Clasifica una pregunta en una de las 11 categorías basándose en su contenido.
        """
        question_lower = question_text.lower()
        
        # Patrones mejorados para cada categoría
        category_patterns = {
            1: ["bocina", "proa", "popa", "babor", "estribor", "eslora", "manga", "puntal", "calado", 
                "casco", "cubierta", "timón", "roda", "codaste", "quilla", "aleta", "través", "cabo"],
            2: ["ancla", "fondeo", "amarre", "cabo", "nudo", "bita", "cornamusa", "muerto", "rezón",
                "cadena", "orinque", "garreo", "virar", "filar", "levar", "zarpar"],
            3: ["chaleco", "balsa", "bengala", "extintor", "botiquín", "supervivencia", "salvavidas",
                "emergencia", "socorro", "epirb", "abandono", "rescate", "helicóptero", "radar"],
            4: ["capitanía", "despacho", "permiso", "licencia", "normativa", "ley", "reglamento",
                "autoridad", "certificado", "navegabilidad", "zona", "obligatorio"],
            5: ["boya", "baliza", "faro", "luz", "señal", "cardinal", "lateral", "marca", "enfilación",
                "sector", "destellos", "ocultaciones", "ritmo", "alcance"],
            6: ["abordaje", "rumbo", "cruce", "alcance", "maniobra", "preferencia", "paso", "ripa",
                "buque", "embarcación", "motor", "vela", "fondeado", "visibilidad"],
            7: ["rumbo", "derrota", "posición", "navegación", "maniobra", "gobierno", "caída",
                "arribada", "orzada", "virada", "trasluchada", "ceñida", "largo", "través"],
            8: ["abandono", "emergencia", "socorro", "supervivencia", "situación", "peligro",
                "naufragio", "varada", "incendio", "vía", "agua", "remolque"],
            9: ["viento", "presión", "borrasca", "anticiclón", "tiempo", "temporal", "escala",
                "beaufort", "marejada", "oleaje", "meteorología", "barómetro"],
            10: ["coordenadas", "latitud", "longitud", "meridiano", "paralelo", "carta", "plotear",
                 "estima", "situación", "demora", "marcación", "altura", "sonda"],
            11: ["carta", "escala", "símbolo", "proyección", "meridiano", "paralelo", "rosa",
                 "distancia", "milla", "nudo", "plotear", "navegación", "situación"]
        }
        
        # Contar coincidencias para cada categoría
        category_scores = {}
        for category, patterns in category_patterns.items():
            score = sum(1 for pattern in patterns if pattern in question_lower)
            if score > 0:
                category_scores[category] = score
        
        # Devolver la categoría con mayor puntuación, o 1 por defecto
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return 1  # Categoría por defecto (Nomenclatura náutica)
    
    def extract_per_questions_first_model(self, pdf_path: str) -> List[Dict]:
        """Extrae las preguntas de PER del primer modelo únicamente."""
        text = self.extract_text_from_pdf(pdf_path)
        
        # Buscar el inicio del primer modelo de PER
        per_start_pattern = r"EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO.*?Código de Test 01"
        per_match = re.search(per_start_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not per_match:
            print("No se encontró el inicio del PER Código de Test 01")
            return []
        
        # Extraer texto desde el inicio del PER hasta el siguiente examen
        per_text = text[per_match.start():]
        
        # Buscar el final del primer modelo (inicio del segundo examen de PER o fin)
        end_patterns = [
            r"EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO.*?Código de Test 02",
            r"EXAMEN.*?Código de Test",
            r"MINISTERIO.*?DE TRANSPORTES.*?Y MOVILIDAD SOSTENIBLE.*?DIRECCIÓN GENERAL"
        ]
        
        end_pos = len(per_text)
        for pattern in end_patterns:
            match = re.search(pattern, per_text[100:], re.IGNORECASE | re.DOTALL)  # Evitar coincidencia inmediata
            if match and match.start() + 100 < end_pos:
                end_pos = match.start() + 100
        
        per_first_model_text = per_text[:end_pos]
        
        # Extraer preguntas del primer modelo
        questions = self.parse_questions_from_text(per_first_model_text)
        
        # Clasificar cada pregunta
        for question in questions:
            category = self.classify_question_by_content(question['question'])
            question['category'] = category
            question['category_name'] = PER_CATEGORIES[category]
        
        return questions
    
    def parse_questions_from_text(self, text: str) -> List[Dict]:
        """Parse questions from the extracted text."""
        questions = []
        
        # Patrón mejorado para encontrar preguntas numeradas
        # Buscar: número + espacio + texto de pregunta + opciones a), b), c), d)
        question_pattern = r'(\d+)\s+([^0-9]+?)(?=\d+\s+[^0-9]|$)'
        matches = re.findall(question_pattern, text, re.DOTALL)
        
        for number, content in matches:
            question_num = int(number)
            if question_num > 100:  # Filtrar números muy altos que no son preguntas
                continue
                
            # Limpiar contenido
            content = content.strip()
            if len(content) < 30:  # Filtrar contenido muy corto
                continue
            
            # Separar pregunta de opciones
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if len(lines) < 4:  # Necesita al menos pregunta + 3 opciones
                continue
            
            # Encontrar dónde empiezan las opciones
            question_lines = []
            options = []
            options_started = False
            
            for line in lines:
                # Buscar opciones a), b), c), d)
                option_match = re.match(r'^([a-d])\)\s*(.+)', line, re.IGNORECASE)
                if option_match:
                    options_started = True
                    option_text = option_match.group(2).strip()
                    options.append(option_text)
                elif not options_started:
                    question_lines.append(line)
            
            # Construir pregunta
            question_text = ' '.join(question_lines).strip()
            
            # Validar que tenemos pregunta y al menos 3 opciones
            if len(question_text) > 10 and len(options) >= 3:
                questions.append({
                    'id': question_num,
                    'question': question_text,
                    'options': options[:4],  # Máximo 4 opciones
                    'correct_answer': None  # Se añadirá después
                })
        
        return questions
    
    def extract_per_answers(self, pdf_path: str) -> Dict[int, str]:
        """Extrae las respuestas del PER del primer modelo."""
        text = self.extract_text_from_pdf(pdf_path)
        answers = {}
        
        # Buscar la sección de respuestas para PER Código de Test 01
        answer_pattern = r"Respuestas al EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO\s+Código de Test 01\s+([A-D]\s+\d+.*?)(?=Respuestas al EXAMEN|$)"
        answer_match = re.search(answer_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if answer_match:
            answer_text = answer_match.group(1)
            print(f"Texto de respuestas encontrado: {len(answer_text)} caracteres")
            
            # El formato es: B 1 B 2 B 3 C 4 C 5 C 6 B 7 D 8 B 9...
            # Extraer pares letra-número
            answer_pairs = re.findall(r'([A-D])\s+(\d+)', answer_text)
            print(f"Pares encontrados: {len(answer_pairs)}")
            
            for letter, number in answer_pairs:
                answers[int(number)] = letter
        else:
            print("No se encontró la sección de respuestas de PER")
        
        return answers
    
    def process_per_exam(self, pdf_questions_path: str, pdf_answers_path: str) -> Dict:
        """Procesa un examen completo de PER."""
        print("Procesando preguntas de PER (primer modelo)...")
        
        # Extraer preguntas
        questions = self.extract_per_questions_first_model(pdf_questions_path)
        print(f"Extraídas {len(questions)} preguntas")
        
        # Extraer respuestas
        answers = self.extract_per_answers(pdf_answers_path)
        print(f"Extraídas {len(answers)} respuestas")
        
        # Asignar respuestas correctas
        for question in questions:
            if question['id'] in answers:
                answer_letter = answers[question['id']]
                answer_index = ord(answer_letter) - ord('A')
                if 0 <= answer_index < len(question['options']):
                    question['correct_answer'] = answer_index
        
        # Agrupar por categoría
        questions_by_category = {}
        for question in questions:
            category = question['category']
            if category not in questions_by_category:
                questions_by_category[category] = []
            questions_by_category[category].append(question)
        
        # Crear estructura final
        exam_data = {
            'exam_info': {
                'title': 'Patrón de Embarcación de Recreo (PER)',
                'source': 'Madrid 2025 - Modelo A',
                'total_questions': len(questions),
                'categories': len(questions_by_category)
            },
            'categories': {}
        }
        
        for category_id, category_questions in questions_by_category.items():
            exam_data['categories'][category_id] = {
                'name': PER_CATEGORIES[category_id],
                'questions': category_questions
            }
        
        return exam_data
    
    def save_to_yaml(self, data: Dict, output_path: str):
        """Guarda los datos en formato YAML."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        print(f"Datos guardados en {output_path}")

def main():
    processor = PERProcessor()
    
    # Rutas de los PDFs
    pdf_questions = "/workspaces/per-tests/pdfs/madrid-2025.pdf"
    pdf_answers = "/workspaces/per-tests/pdfs/madrid-2025-resp.pdf"
    
    # Verificar que existen los PDFs
    if not os.path.exists(pdf_questions):
        print(f"Error: No se encuentra {pdf_questions}")
        return
    if not os.path.exists(pdf_answers):
        print(f"Error: No se encuentra {pdf_answers}")
        return
    
    # Procesar el examen de PER
    exam_data = processor.process_per_exam(pdf_questions, pdf_answers)
    
    # Guardar resultado
    output_path = "/workspaces/per-tests/data/per_questions.yaml"
    processor.save_to_yaml(exam_data, output_path)
    
    # Mostrar estadísticas
    print("\n=== ESTADÍSTICAS ===")
    print(f"Total de preguntas: {exam_data['exam_info']['total_questions']}")
    print(f"Categorías: {exam_data['exam_info']['categories']}")
    print("\nDistribución por categoría:")
    for cat_id, cat_data in exam_data['categories'].items():
        print(f"  {cat_id}. {cat_data['name']}: {len(cat_data['questions'])} preguntas")

if __name__ == "__main__":
    main()
