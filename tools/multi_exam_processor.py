#!/usr/bin/env python3
"""
Procesador completo de PDFs para extraer todas las secciones de examen
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


class MultiExamPDFProcessor:
    """Procesador que extrae todos los tipos de examen de un PDF"""
    
    def __init__(self, pdfs_directory="pdfs", output_directory="data"):
        self.pdfs_dir = Path(pdfs_directory)
        self.output_dir = Path(output_directory)
        self.questions_file = self.pdfs_dir / "madrid-2025.pdf"
        self.answers_file = self.pdfs_dir / "madrid-2025-resp.pdf"
        
        # Configuración de tipos de examen
        self.exam_types = {
            'per': {
                'titles': [
                    'EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO',
                    'PATRÓN DE EMBARCACIONES DE RECREO'
                ],
                'category': 'per',
                'output_dir': 'per'
            },
            'patron_yate': {
                'titles': [
                    'EXAMEN DE PATRÓN DE YATE',
                    'PATRÓN DE YATE'
                ],
                'category': 'patron_yate',
                'output_dir': 'patron_yate'
            },
            'capitan_yate': {
                'titles': [
                    'EXAMEN DE CAPITÁN DE YATE',
                    'CAPITÁN DE YATE'
                ],
                'category': 'capitan_yate',
                'output_dir': 'capitan_yate'
            }
        }
        
        # Crear directorios de salida
        for exam_type, config in self.exam_types.items():
            output_path = self.output_dir / config['output_dir']
            output_path.mkdir(parents=True, exist_ok=True)
    
    def identify_exam_sections(self) -> Dict[str, Dict]:
        """Identifica las secciones de cada tipo de examen en el PDF"""
        logger.info("🔍 Identificando secciones de examen...")
        
        sections = {}
        
        with fitz.open(self.questions_file) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Buscar títulos de cada tipo de examen
                for exam_key, config in self.exam_types.items():
                    for title in config['titles']:
                        if title in text:
                            if exam_key not in sections:
                                sections[exam_key] = {
                                    'start_page': page_num + 1,
                                    'config': config,
                                    'title_found': title
                                }
                            logger.info(f"✅ Encontrado {title} en página {page_num + 1}")
        
        # Estimar rangos de páginas para cada sección
        section_keys = list(sections.keys())
        for i, exam_key in enumerate(section_keys):
            if i < len(section_keys) - 1:
                # No es la última sección, el final es el inicio de la siguiente
                next_exam_key = section_keys[i + 1]
                sections[exam_key]['end_page'] = sections[next_exam_key]['start_page'] - 1
            else:
                # Es la última sección, va hasta el final
                sections[exam_key]['end_page'] = len(doc)
        
        logger.info(f"📊 Secciones identificadas: {list(sections.keys())}")
        for exam_key, info in sections.items():
            logger.info(f"   {exam_key}: páginas {info['start_page']}-{info['end_page']}")
        
        return sections
    
    def extract_questions_from_section(self, start_page: int, end_page: int, exam_type: str) -> List[Dict]:
        """Extrae preguntas de una sección específica del PDF"""
        logger.info(f"📝 Extrayendo preguntas de {exam_type} (páginas {start_page}-{end_page})")
        
        questions = []
        current_question = None
        
        with fitz.open(self.questions_file) as doc:
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Detectar inicio de pregunta (número seguido de punto)
                    question_match = re.match(r'^(\d+)\.\s*(.+)', line)
                    if question_match:
                        # Guardar pregunta anterior si existe
                        if current_question and current_question.get('enunciado'):
                            questions.append(current_question)
                        
                        # Iniciar nueva pregunta
                        question_num = int(question_match.group(1))
                        question_text = question_match.group(2)
                        
                        current_question = {
                            'numero': question_num,
                            'enunciado': question_text,
                            'opciones': {},
                            'pagina': page_num + 1
                        }
                        continue
                    
                    # Detectar opciones (a), b), c), d))
                    option_match = re.match(r'^([abcd])\)\s*(.+)', line)
                    if option_match and current_question:
                        option_letter = option_match.group(1)
                        option_text = option_match.group(2)
                        current_question['opciones'][option_letter] = option_text
                        continue
                    
                    # Si no es inicio de pregunta ni opción, podría ser continuación
                    if current_question and len(current_question['opciones']) == 0:
                        # Continuación del enunciado
                        current_question['enunciado'] += ' ' + line
                    elif current_question and len(current_question['opciones']) > 0:
                        # Posible continuación de la última opción
                        last_option = list(current_question['opciones'].keys())[-1]
                        current_question['opciones'][last_option] += ' ' + line
        
        # Agregar última pregunta
        if current_question and current_question.get('enunciado'):
            questions.append(current_question)
        
        logger.info(f"✅ Extraídas {len(questions)} preguntas de {exam_type}")
        return questions
    
    def load_answers(self, start_question: int, end_question: int) -> Dict[int, str]:
        """Carga las respuestas desde el PDF de respuestas"""
        logger.info(f"📋 Cargando respuestas para preguntas {start_question}-{end_question}")
        
        answers = {}
        
        with fitz.open(self.answers_file) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Buscar patrones como "1-a", "2-b", etc.
                answer_matches = re.finditer(r'(\d+)-([abcd])', text)
                for match in answer_matches:
                    question_num = int(match.group(1))
                    answer_letter = match.group(2)
                    
                    if start_question <= question_num <= end_question:
                        answers[question_num] = answer_letter
        
        logger.info(f"✅ Cargadas {len(answers)} respuestas")
        return answers
    
    def create_yaml_structure(self, questions: List[Dict], answers: Dict[int, str], 
                            exam_type: str, config: Dict) -> Dict:
        """Crea la estructura YAML para un tipo de examen"""
        
        yaml_questions = []
        
        for q in questions:
            question_num = q['numero']
            correct_answer = answers.get(question_num, 'a')  # Por defecto 'a' si no se encuentra
            
            yaml_question = {
                'id': f"{exam_type}_{question_num:03d}_2025_madrid_p{question_num}",
                'enunciado': q['enunciado'].strip(),
                'opciones': q['opciones'],
                'respuesta_correcta': correct_answer,
                'metadata': {
                    'año': 2025,
                    'categoria': config['category'],
                    'comunidad_autonoma': 'madrid',
                    'convocatoria': 'madrid',
                    'numero_pregunta': question_num
                }
            }
            
            yaml_questions.append(yaml_question)
        
        return {
            'metadata': {
                'exam_type': exam_type,
                'category': config['category'],
                'source': 'madrid-2025',
                'total_questions': len(yaml_questions),
                'version': '1.0'
            },
            'preguntas': yaml_questions
        }
    
    def estimate_question_ranges(self, sections: Dict[str, Dict]) -> Dict[str, Tuple[int, int]]:
        """Estima los rangos de preguntas para cada tipo de examen basándose en estándares típicos"""
        
        ranges = {}
        
        # Rangos típicos para exámenes náuticos españoles
        if 'per' in sections:
            ranges['per'] = (1, 45)  # PER típicamente tiene 45 preguntas
        
        if 'patron_yate' in sections:
            if 'per' in sections:
                ranges['patron_yate'] = (46, 90)  # Siguiente rango después del PER
            else:
                ranges['patron_yate'] = (1, 45)
        
        if 'capitan_yate' in sections:
            if 'patron_yate' in sections:
                ranges['capitan_yate'] = (91, 135)  # Siguiente rango después de Patrón de Yate
            elif 'per' in sections:
                ranges['capitan_yate'] = (46, 90)
            else:
                ranges['capitan_yate'] = (1, 45)
        
        logger.info("📊 Rangos de preguntas estimados:")
        for exam_type, (start, end) in ranges.items():
            logger.info(f"   {exam_type}: preguntas {start}-{end}")
        
        return ranges
    
    def process_all_exams(self):
        """Procesa todos los tipos de examen encontrados en los PDFs"""
        logger.info("🚀 Iniciando procesamiento completo de exámenes")
        
        # 1. Identificar secciones
        sections = self.identify_exam_sections()
        
        if not sections:
            logger.error("❌ No se encontraron secciones de examen")
            return
        
        # 2. Estimar rangos de preguntas
        question_ranges = self.estimate_question_ranges(sections)
        
        # 3. Procesar cada tipo de examen
        for exam_type, section_info in sections.items():
            logger.info(f"\n🎯 Procesando {exam_type.upper()}")
            
            # Extraer preguntas de la sección
            questions = self.extract_questions_from_section(
                section_info['start_page'],
                section_info['end_page'],
                exam_type
            )
            
            if not questions:
                logger.warning(f"⚠️  No se encontraron preguntas para {exam_type}")
                continue
            
            # Cargar respuestas para el rango de preguntas
            if exam_type in question_ranges:
                start_q, end_q = question_ranges[exam_type]
                answers = self.load_answers(start_q, end_q)
            else:
                # Si no tenemos rango específico, usar el rango de preguntas encontradas
                question_numbers = [q['numero'] for q in questions]
                start_q, end_q = min(question_numbers), max(question_numbers)
                answers = self.load_answers(start_q, end_q)
            
            # Crear estructura YAML
            yaml_data = self.create_yaml_structure(
                questions, answers, exam_type, section_info['config']
            )
            
            # Guardar archivo YAML
            output_file = self.output_dir / section_info['config']['output_dir'] / 'madrid_2025.yaml'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            logger.info(f"✅ Guardado: {output_file}")
            logger.info(f"   📝 {len(questions)} preguntas procesadas")
            logger.info(f"   📋 {len(answers)} respuestas cargadas")
        
        logger.info("\n🎉 Procesamiento completado para todos los exámenes")


if __name__ == "__main__":
    processor = MultiExamPDFProcessor()
    processor.process_all_exams()
