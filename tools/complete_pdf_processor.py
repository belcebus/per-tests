#!/usr/bin/env python3
"""
Procesador completo que extrae todos los exámenes por tipo y código de test
"""

import fitz
import re
import yaml
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompletePDFProcessor:
    """Extrae todos los tipos de examen y códigos de test"""
    
    def __init__(self):
        self.pdfs_dir = Path("pdfs")
        self.output_dir = Path("data")
        self.questions_file = self.pdfs_dir / "madrid-2025.pdf"
        self.answers_file = self.pdfs_dir / "madrid-2025-resp.pdf"
        
        # Estructura de exámenes detectada
        self.exam_structure = {
            'CAPITÁN DE YATE': {
                'output_dir': 'capitan_yate',
                'category': 'capitan_yate',
                'tests': [
                    {'code': '01', 'start_page': 1},
                    {'code': '02', 'start_page': 19}
                ]
            },
            'PATRÓN DE YATE': {
                'output_dir': 'patron_yate',
                'category': 'patron_yate',
                'tests': [
                    {'code': '01', 'start_page': 36},
                    {'code': '02', 'start_page': 47}
                ]
            },
            'PATRÓN DE EMBARCACIONES DE RECREO': {
                'output_dir': 'per',
                'category': 'per',
                'tests': [
                    {'code': '01', 'start_page': 59},
                    {'code': '02', 'start_page': 72},
                    {'code': '03', 'start_page': 85},
                    {'code': '04', 'start_page': 98}
                ]
            }
        }
        
        # Crear directorios de salida
        for exam_type, config in self.exam_structure.items():
            output_path = self.output_dir / config['output_dir']
            output_path.mkdir(parents=True, exist_ok=True)
    
    def find_section_end_page(self, start_page: int, all_start_pages: list) -> int:
        """Encuentra la página final de una sección"""
        next_pages = [p for p in all_start_pages if p > start_page]
        if next_pages:
            return min(next_pages) - 1
        else:
            # Es la última sección, usar el final del documento
            with fitz.open(self.questions_file) as doc:
                return len(doc)
    
    def extract_questions_from_section(self, start_page: int, end_page: int, exam_type: str, test_code: str) -> list:
        """Extrae preguntas de una sección específica"""
        logger.info(f"📝 Extrayendo {exam_type} Test {test_code} (páginas {start_page}-{end_page})")
        
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
                    
                    # Detectar inicio de pregunta
                    question_match = re.match(r'^(\d+)\s+(.+)', line)
                    if question_match:
                        # Guardar pregunta anterior
                        if current_question and self._is_question_complete(current_question):
                            questions.append(current_question)
                        
                        # Nueva pregunta
                        question_num = int(question_match.group(1))
                        question_text = question_match.group(2)
                        
                        current_question = {
                            'numero': question_num,
                            'enunciado': question_text,
                            'opciones': {},
                            'pagina': page_num + 1
                        }
                        continue
                    
                    # Detectar opciones
                    option_match = re.match(r'^([abcd])\)\s*(.+)', line)
                    if option_match and current_question:
                        option_letter = option_match.group(1)
                        option_text = option_match.group(2)
                        current_question['opciones'][option_letter] = option_text
                        continue
                    
                    # Continuación de texto
                    if current_question:
                        if len(current_question['opciones']) == 0:
                            # Continuación del enunciado
                            current_question['enunciado'] += ' ' + line
                        elif len(current_question['opciones']) > 0:
                            # Continuación de la última opción
                            last_option = list(current_question['opciones'].keys())[-1]
                            current_question['opciones'][last_option] += ' ' + line
        
        # Agregar última pregunta
        if current_question and self._is_question_complete(current_question):
            questions.append(current_question)
        
        logger.info(f"✅ {len(questions)} preguntas extraídas de {exam_type} Test {test_code}")
        return questions
    
    def _is_question_complete(self, question: dict) -> bool:
        """Verifica si una pregunta está completa"""
        return (question.get('enunciado') and 
                len(question.get('opciones', {})) >= 2 and  # Al menos 2 opciones
                question.get('numero'))
    
    def load_answers_for_test(self, exam_type: str, test_code: str, questions: list) -> dict:
        """Carga respuestas para un test específico"""
        if not questions:
            return {}
        
        logger.info(f"📋 Cargando respuestas para {exam_type} Test {test_code}")
        
        answers = {}
        question_numbers = [q['numero'] for q in questions]
        
        with fitz.open(self.answers_file) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Buscar el código de test correcto
                if f"Test {test_code}" in text or f"Código de Test {test_code}" in text:
                    # Buscar respuestas en formato "1-a", "2-b", etc.
                    answer_matches = re.finditer(r'(\d+)-([abcd])', text)
                    for match in answer_matches:
                        question_num = int(match.group(1))
                        answer_letter = match.group(2)
                        
                        if question_num in question_numbers:
                            answers[question_num] = answer_letter
        
        logger.info(f"✅ {len(answers)} respuestas cargadas")
        return answers
    
    def create_yaml_structure(self, questions: list, answers: dict, exam_type: str, test_code: str, config: dict) -> dict:
        """Crea estructura YAML para un test específico"""
        
        yaml_questions = []
        
        for q in questions:
            question_num = q['numero']
            correct_answer = answers.get(question_num, 'a')  # Default 'a' si no se encuentra
            
            yaml_question = {
                'id': f"{config['category']}_{question_num:03d}_2025_madrid_test{test_code}_p{question_num}",
                'enunciado': self._clean_text(q['enunciado']),
                'opciones': {k: self._clean_text(v) for k, v in q['opciones'].items()},
                'respuesta_correcta': correct_answer,
                'metadata': {
                    'año': 2025,
                    'categoria': config['category'],
                    'comunidad_autonoma': 'madrid',
                    'convocatoria': 'madrid',
                    'test_code': test_code,
                    'numero_pregunta': question_num
                }
            }
            
            yaml_questions.append(yaml_question)
        
        return {
            'metadata': {
                'exam_type': config['category'],
                'category': config['category'],
                'test_code': test_code,
                'source': 'madrid-2025',
                'total_questions': len(yaml_questions),
                'version': '1.0'
            },
            'preguntas': yaml_questions
        }
    
    def _clean_text(self, text: str) -> str:
        """Limpia y normaliza texto"""
        if not text:
            return ""
        # Remover espacios extras y normalizar
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    def process_all_exams(self):
        """Procesa todos los exámenes"""
        logger.info("🚀 Iniciando procesamiento completo de todos los exámenes")
        
        # Obtener todas las páginas de inicio para calcular finales
        all_start_pages = []
        for exam_type, config in self.exam_structure.items():
            for test in config['tests']:
                all_start_pages.append(test['start_page'])
        
        total_questions_processed = 0
        
        for exam_type, config in self.exam_structure.items():
            logger.info(f"\n🎯 Procesando {exam_type}")
            
            for test in config['tests']:
                test_code = test['code']
                start_page = test['start_page']
                end_page = self.find_section_end_page(start_page, all_start_pages)
                
                # Extraer preguntas
                questions = self.extract_questions_from_section(
                    start_page, end_page, exam_type, test_code
                )
                
                if not questions:
                    logger.warning(f"⚠️  No se encontraron preguntas para {exam_type} Test {test_code}")
                    continue
                
                # Cargar respuestas
                answers = self.load_answers_for_test(exam_type, test_code, questions)
                
                # Crear estructura YAML
                yaml_data = self.create_yaml_structure(questions, answers, exam_type, test_code, config)
                
                # Guardar archivo
                filename = f"madrid_2025_test{test_code}.yaml"
                output_file = self.output_dir / config['output_dir'] / filename
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                logger.info(f"✅ Guardado: {output_file}")
                logger.info(f"   📝 {len(questions)} preguntas, 📋 {len(answers)} respuestas")
                
                total_questions_processed += len(questions)
        
        logger.info(f"\n🎉 Procesamiento completado!")
        logger.info(f"📊 Total de preguntas procesadas: {total_questions_processed}")
        
        # Crear resumen
        self.create_summary_report()
    
    def create_summary_report(self):
        """Crea un reporte resumen del procesamiento"""
        report_file = self.output_dir / "processing_summary.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Resumen del Procesamiento de Exámenes\n\n")
            f.write(f"Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for exam_type, config in self.exam_structure.items():
                f.write(f"## {exam_type}\n\n")
                f.write(f"- Directorio: `{config['output_dir']}/`\n")
                f.write(f"- Categoría: `{config['category']}`\n")
                f.write(f"- Tests procesados:\n")
                
                for test in config['tests']:
                    filename = f"madrid_2025_test{test['code']}.yaml"
                    filepath = self.output_dir / config['output_dir'] / filename
                    if filepath.exists():
                        f.write(f"  - ✅ Test {test['code']}: `{filename}`\n")
                    else:
                        f.write(f"  - ❌ Test {test['code']}: No procesado\n")
                
                f.write("\n")
        
        logger.info(f"📄 Reporte guardado en: {report_file}")

if __name__ == "__main__":
    processor = CompletePDFProcessor()
    processor.process_all_exams()
