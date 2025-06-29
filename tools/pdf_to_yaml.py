#!/usr/bin/env python3
"""
Procesador de PDFs a YAML para exámenes PER

Este script procesa los PDFs oficiales y los convierte a archivos YAML
con la estructura que diseñamos para la aplicación.
"""

import fitz  # PyMuPDF
import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFToYAMLProcessor:
    """Procesador que convierte PDFs de exámenes a archivos YAML"""
    
    def __init__(self, pdfs_directory="pdfs", output_directory="data"):
        self.pdfs_dir = Path(pdfs_directory)
        self.output_dir = Path(output_directory)
        self.questions_file = None
        self.answers_file = None
        self.extracted_exams = {}
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(exist_ok=True)
        
    def find_files(self):
        """Encuentra los archivos PDF"""
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            if "resp" in pdf_file.name.lower():
                self.answers_file = pdf_file
            else:
                self.questions_file = pdf_file
                
        logger.info(f"Archivo de preguntas: {self.questions_file}")
        logger.info(f"Archivo de respuestas: {self.answers_file}")
        
    def extract_questions_from_pdf(self) -> Dict[str, List]:
        """Extrae todas las preguntas del PDF"""
        if not self.questions_file:
            logger.error("No se encontró archivo de preguntas")
            return {}
            
        logger.info("Extrayendo preguntas del PDF...")
        
        exams_data = {}
        current_exam_type = None
        current_test_code = None
        current_questions = []
        
        with fitz.open(self.questions_file) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # Detectar tipo de examen y código
                exam_type_match = re.search(r'EXAMEN DE (.+?)\n', text)
                if exam_type_match:
                    exam_type = exam_type_match.group(1).strip()
                    if "CAPITÁN DE YATE" in exam_type:
                        current_exam_type = "capitan_yate"
                    elif "PATRÓN DE YATE" in exam_type:
                        current_exam_type = "patron_yate"
                    elif "PATRÓN DE EMBARCACIÓN" in exam_type or "PER" in exam_type:
                        current_exam_type = "per"
                        
                # Detectar código de test
                test_code_match = re.search(r'Código de Test (\d+)', text)
                if test_code_match:
                    current_test_code = test_code_match.group(1)
                    
                # Extraer preguntas de esta página
                questions = self._extract_questions_from_page(text, page_num + 1)
                current_questions.extend(questions)
                
                # Si encontramos un nuevo examen, guardar el anterior
                if exam_type_match and current_exam_type and current_questions:
                    key = f"{current_exam_type}_test_{current_test_code}"
                    if key not in exams_data:
                        exams_data[key] = []
                    exams_data[key] = current_questions.copy()
                    logger.info(f"Procesando {key}: {len(current_questions)} preguntas")
                    
        return exams_data
    
    def _extract_questions_from_page(self, text: str, page_num: int) -> List[Dict]:
        """Extrae preguntas de una página específica"""
        questions = []
        
        # Patrón para encontrar preguntas numeradas
        # Busca: número + espacio + texto hasta encontrar opciones a), b), c), d)
        question_pattern = r'(\d+)\s+([^a-d\)]*?)(?=a\)|$)'
        
        matches = re.finditer(question_pattern, text, re.DOTALL)
        
        for match in matches:
            question_num = match.group(1)
            question_text = match.group(2).strip()
            
            if len(question_text) > 10:  # Filtrar coincidencias muy cortas
                # Buscar opciones para esta pregunta
                options = self._extract_options_for_question(text, match.end())
                
                if options:  # Solo agregar si encontramos opciones
                    question_data = {
                        'number': int(question_num),
                        'text': question_text,
                        'options': options,
                        'page': page_num
                    }
                    questions.append(question_data)
                    
        return questions
    
    def _extract_options_for_question(self, text: str, start_pos: int) -> Dict[str, str]:
        """Extrae las opciones a), b), c), d) para una pregunta"""
        options = {}
        
        # Buscar opciones después de la posición actual
        remaining_text = text[start_pos:start_pos + 1000]  # Limitar búsqueda
        
        option_pattern = r'([a-d])\)\s*([^a-d\)]*?)(?=[a-d]\)|\d+\s|$)'
        option_matches = re.finditer(option_pattern, remaining_text, re.DOTALL)
        
        for match in option_matches:
            letter = match.group(1)
            option_text = match.group(2).strip()
            
            if option_text and len(option_text) > 2:
                options[letter] = option_text
                
        return options if len(options) >= 2 else {}  # Al menos 2 opciones
    
    def extract_answers_from_pdf(self) -> Dict[str, List[str]]:
        """Extrae las respuestas del PDF de respuestas"""
        if not self.answers_file:
            logger.error("No se encontró archivo de respuestas")
            return {}
            
        logger.info("Extrayendo respuestas del PDF...")
        
        answers_data = {}
        current_test = None
        
        with fitz.open(self.answers_file) as doc:
            for page in doc:
                text = page.get_text()
                
                # Detectar código de test
                test_match = re.search(r'Código de Test (\d+)', text)
                if test_match:
                    current_test = f"test_{test_match.group(1)}"
                    answers_data[current_test] = []
                    
                # Extraer respuestas (formato: letra sola en línea)
                answer_pattern = r'^([A-D])$'
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if re.match(answer_pattern, line):
                        if current_test:
                            answers_data[current_test].append(line.lower())
                            
        return answers_data
    
    def match_questions_with_answers(self, questions_data: Dict, answers_data: Dict) -> Dict:
        """Asocia preguntas con respuestas correctas"""
        logger.info("Asociando preguntas con respuestas...")
        
        matched_data = {}
        
        for exam_key, questions in questions_data.items():
            # Extraer el número de test del key
            test_num = re.search(r'test_(\d+)', exam_key)
            if not test_num:
                continue
                
            test_key = f"test_{test_num.group(1)}"
            answers = answers_data.get(test_key, [])
            
            matched_questions = []
            
            for i, question in enumerate(questions):
                if i < len(answers):
                    question['correct_answer'] = answers[i]
                    matched_questions.append(question)
                else:
                    logger.warning(f"No hay respuesta para pregunta {i+1} en {exam_key}")
                    
            matched_data[exam_key] = matched_questions
            logger.info(f"{exam_key}: {len(matched_questions)} preguntas con respuestas")
            
        return matched_data
    
    def convert_to_yaml_format(self, matched_data: Dict, exam_type: str = "per") -> Dict:
        """Convierte los datos extraídos al formato YAML que usamos"""
        yaml_data = {
            'metadata': {
                'exam_type': exam_type,
                'category': 'mixed',  # Las categorías las asignaremos manualmente después
                'version': '1.0'
            },
            'preguntas': []
        }
        
        # Tomar el primer test de PER (si existe)
        per_tests = [k for k in matched_data.keys() if exam_type in k]
        if not per_tests:
            logger.warning(f"No se encontraron tests de tipo {exam_type}")
            return yaml_data
            
        first_test = per_tests[0]
        questions = matched_data[first_test]
        
        for question in questions:
            if 'correct_answer' not in question:
                continue
                
            yaml_question = {
                'id': f"{exam_type}_{question['number']:03d}_2025_madrid_p{question['number']}",
                'enunciado': question['text'],
                'opciones': question['options'],
                'respuesta_correcta': question['correct_answer'],
                'metadata': {
                    'categoria': 'mixed',  # A categorizar manualmente
                    'convocatoria': 'madrid',
                    'año': 2025,
                    'comunidad_autonoma': 'madrid',
                    'numero_pregunta': question['number']
                }
            }
            
            yaml_data['preguntas'].append(yaml_question)
            
        return yaml_data
    
    def save_yaml_file(self, data: Dict, filename: str):
        """Guarda los datos en formato YAML"""
        output_path = self.output_dir / f"{filename}.yaml"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
        logger.info(f"Archivo YAML guardado: {output_path}")
        
    def process_pdfs(self):
        """Proceso principal"""
        logger.info("🚀 Iniciando procesamiento de PDFs...")
        
        # Paso 1: Encontrar archivos
        self.find_files()
        
        if not self.questions_file or not self.answers_file:
            logger.error("No se encontraron ambos archivos PDF")
            return
            
        # Paso 2: Extraer preguntas
        questions_data = self.extract_questions_from_pdf()
        
        # Paso 3: Extraer respuestas
        answers_data = self.extract_answers_from_pdf()
        
        # Paso 4: Asociar preguntas con respuestas
        matched_data = self.match_questions_with_answers(questions_data, answers_data)
        
        # Paso 5: Convertir a formato YAML para cada tipo de examen
        for exam_type in ['per', 'capitan_yate', 'patron_yate']:
            yaml_data = self.convert_to_yaml_format(matched_data, exam_type)
            if yaml_data['preguntas']:
                self.save_yaml_file(yaml_data, f"{exam_type}_madrid_2025")
                
        logger.info("✅ Procesamiento completado!")


if __name__ == "__main__":
    processor = PDFToYAMLProcessor()
    processor.process_pdfs()
