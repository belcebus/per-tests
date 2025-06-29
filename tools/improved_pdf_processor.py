#!/usr/bin/env python3
"""
Procesador mejorado de PDFs a YAML basado en la estructura real detectada
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


class ImprovedPDFProcessor:
    """Procesador mejorado basado en la estructura real de los PDFs"""
    
    def __init__(self, pdfs_directory="pdfs", output_directory="data/extracted"):
        self.pdfs_dir = Path(pdfs_directory)
        self.output_dir = Path(output_directory)
        self.questions_file = self.pdfs_dir / "madrid-2025.pdf"
        self.answers_file = self.pdfs_dir / "madrid-2025-resp.pdf"
        
        # Crear directorio de salida
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_pdf_structure(self):
        """Analiza la estructura completa del PDF para entender el formato"""
        logger.info("🔍 Analizando estructura del PDF...")
        
        with fitz.open(self.questions_file) as doc:
            exam_types = []
            test_codes = []
            
            # Analizar primeras 10 páginas para detectar patrones
            for page_num in range(min(10, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                
                # Buscar tipos de examen
                if "EXAMEN DE" in text:
                    exam_match = re.search(r'EXAMEN DE (.+)', text)
                    if exam_match:
                        exam_type = exam_match.group(1).strip()
                        if exam_type not in exam_types:
                            exam_types.append(exam_type)
                            logger.info(f"Tipo de examen detectado: {exam_type}")
                
                # Buscar códigos de test
                test_match = re.search(r'Código de Test (\d+)', text)
                if test_match:
                    test_code = test_match.group(1)
                    if test_code not in test_codes:
                        test_codes.append(test_code)
                        logger.info(f"Código de test detectado: {test_code}")
                        
                # Mostrar muestra de preguntas (solo primera vez)
                if page_num == 1:  # Segunda página suele tener preguntas
                    logger.info(f"Muestra de contenido (página {page_num + 1}):")
                    logger.info(text[:300])
                    
            return exam_types, test_codes
    
    def extract_questions_for_exam_type(self, target_exam_type: str) -> List[Dict]:
        """Extrae preguntas para un tipo específico de examen"""
        logger.info(f"📝 Extrayendo preguntas para: {target_exam_type}")
        
        questions = []
        in_target_exam = False
        current_question = None
        current_options = {}
        
        with fitz.open(self.questions_file) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # Detectar si estamos en el examen correcto
                if f"EXAMEN DE {target_exam_type}" in text:
                    in_target_exam = True
                    logger.info(f"Inicio de {target_exam_type} en página {page_num + 1}")
                    continue
                elif "EXAMEN DE" in text and target_exam_type not in text:
                    if in_target_exam:
                        logger.info(f"Fin de {target_exam_type} en página {page_num + 1}")
                        break
                    continue
                
                if not in_target_exam:
                    continue
                
                # Extraer preguntas de esta página
                page_questions = self._extract_questions_from_text(text, page_num + 1)
                questions.extend(page_questions)
                
                if len(page_questions) > 0:
                    logger.info(f"Página {page_num + 1}: {len(page_questions)} preguntas extraídas")
        
        logger.info(f"Total extraído para {target_exam_type}: {len(questions)} preguntas")
        return questions
    
    def _extract_questions_from_text(self, text: str, page_num: int) -> List[Dict]:
        """Extrae preguntas de un texto dado"""
        questions = []
        
        # Dividir por líneas para un análisis más preciso
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Buscar líneas que empiecen con número (posibles preguntas)
            if re.match(r'^\d+\s+', line):
                question_match = re.match(r'^(\d+)\s+(.+)', line)
                if question_match:
                    question_num = int(question_match.group(1))
                    question_text = question_match.group(2)
                    
                    # Recopilar texto de pregunta (puede continuar en siguientes líneas)
                    i += 1
                    while i < len(lines) and not re.match(r'^[a-d]\)', lines[i].strip()):
                        if lines[i].strip() and not re.match(r'^\d+\s+', lines[i].strip()):
                            question_text += " " + lines[i].strip()
                        i += 1
                    
                    # Recopilar opciones
                    options = {}
                    while i < len(lines) and re.match(r'^[a-d]\)', lines[i].strip()):
                        option_match = re.match(r'^([a-d])\)\s*(.+)', lines[i].strip())
                        if option_match:
                            letter = option_match.group(1)
                            option_text = option_match.group(2)
                            
                            # La opción puede continuar en la siguiente línea
                            i += 1
                            while (i < len(lines) and 
                                   lines[i].strip() and 
                                   not re.match(r'^[a-d]\)', lines[i].strip()) and
                                   not re.match(r'^\d+\s+', lines[i].strip())):
                                option_text += " " + lines[i].strip()
                                i += 1
                            
                            options[letter] = option_text
                        else:
                            i += 1
                    
                    # Solo agregar si tenemos al menos 2 opciones
                    if len(options) >= 2:
                        questions.append({
                            'number': question_num,
                            'text': question_text.strip(),
                            'options': options,
                            'page': page_num
                        })
                    
                    continue
            
            i += 1
        
        return questions
    
    def extract_answers(self) -> Dict[str, List[str]]:
        """Extrae respuestas del PDF de respuestas"""
        logger.info("📋 Extrayendo respuestas...")
        
        answers_data = {}
        
        with fitz.open(self.answers_file) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                lines = text.split('\n')
                
                current_exam = None
                current_test = None
                
                for line in lines:
                    line = line.strip()
                    
                    # Detectar tipo de examen
                    if "EXAMEN DE" in line:
                        if "CAPITÁN DE YATE" in line:
                            current_exam = "capitan_yate"
                        elif "PATRÓN DE YATE" in line:
                            current_exam = "patron_yate"
                        elif "PATRÓN DE EMBARCACIÓN" in line or "PER" in line:
                            current_exam = "per"
                    
                    # Detectar código de test
                    test_match = re.match(r'Código de Test (\d+)', line)
                    if test_match and current_exam:
                        current_test = f"{current_exam}_test_{test_match.group(1)}"
                        answers_data[current_test] = []
                    
                    # Recoger respuestas (letras solas)
                    if re.match(r'^[A-D]$', line) and current_test:
                        answers_data[current_test].append(line.lower())
        
        # Mostrar resumen
        for test_key, answers in answers_data.items():
            logger.info(f"{test_key}: {len(answers)} respuestas")
        
        return answers_data
    
    def create_yaml_for_exam_type(self, exam_type: str, questions: List[Dict], answers: Dict[str, List[str]]):
        """Crea archivo YAML para un tipo específico de examen"""
        
        # Buscar respuestas para este tipo de examen
        exam_answers = None
        for test_key, test_answers in answers.items():
            if exam_type in test_key:
                exam_answers = test_answers
                break
        
        if not exam_answers:
            logger.warning(f"No se encontraron respuestas para {exam_type}")
            return
        
        # Crear estructura YAML
        yaml_data = {
            'metadata': {
                'exam_type': exam_type,
                'category': 'mixed',
                'version': '1.0',
                'source': 'madrid-2025',
                'total_questions': len(questions)
            },
            'preguntas': []
        }
        
        # Procesar cada pregunta
        for i, question in enumerate(questions):
            if i < len(exam_answers):
                yaml_question = {
                    'id': f"{exam_type}_{question['number']:03d}_2025_madrid_p{question['number']}",
                    'enunciado': question['text'],
                    'opciones': question['options'],
                    'respuesta_correcta': exam_answers[i],
                    'metadata': {
                        'categoria': 'mixed',  # A categorizar manualmente después
                        'convocatoria': 'madrid',
                        'año': 2025,
                        'comunidad_autonoma': 'madrid',
                        'numero_pregunta': question['number']
                    }
                }
                yaml_data['preguntas'].append(yaml_question)
        
        # Guardar archivo
        filename = f"{exam_type}_madrid_2025.yaml"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"✅ Archivo guardado: {output_path}")
        logger.info(f"   Preguntas procesadas: {len(yaml_data['preguntas'])}")
    
    def process_all_exams(self):
        """Procesa todos los tipos de examen"""
        logger.info("🚀 Iniciando procesamiento completo...")
        
        # Analizar estructura
        exam_types, test_codes = self.analyze_pdf_structure()
        
        # Extraer respuestas
        answers = self.extract_answers()
        
        # Mapeo de tipos de examen
        exam_type_mapping = {
            "CAPITÁN DE YATE": "capitan_yate",
            "PATRÓN DE YATE": "patron_yate",
            "PATRÓN DE EMBARCACIÓN DE RECREO": "per"
        }
        
        # Procesar cada tipo de examen detectado
        for exam_type_spanish in exam_types:
            exam_type = exam_type_mapping.get(exam_type_spanish)
            if exam_type:
                logger.info(f"\n📚 Procesando {exam_type_spanish}...")
                questions = self.extract_questions_for_exam_type(exam_type_spanish)
                
                if questions:
                    self.create_yaml_for_exam_type(exam_type, questions, answers)
                else:
                    logger.warning(f"No se extrajeron preguntas para {exam_type_spanish}")
        
        logger.info("\n✅ Procesamiento completado!")


if __name__ == "__main__":
    processor = ImprovedPDFProcessor()
    processor.process_all_exams()
