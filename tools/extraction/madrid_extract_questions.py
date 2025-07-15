#!/usr/bin/env python3
"""
Extractor parametrizable de exámenes desde PDFs
Permite extraer exámenes específicos usando patrones de título y subtítulo
"""

import fitz  # PyMuPDF
import yaml
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ExamPattern:
    """Patrón para identificar un examen específico"""
    title: str          # Título del examen (ej: "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO")
    subtitle: str       # Subtítulo del examen (ej: "Código de Test 01")
    answer_prefix: str  # Prefijo para las respuestas (ej: "Respuestas al")
    total_questions: int # Número total de preguntas esperadas
    categories: Dict[int, str]  # Categorías del examen
    # Metadatos del examen
    community: str      # Comunidad autónoma donde se realizó (ej: "Madrid")
    year: int          # Año de realización (ej: 2025)
    call: str          # Convocatoria (ej: "Ordinaria", "Extraordinaria", "Enero", "Junio")
    test_code: str     # Código del test (ej: "Test01", "Test03")

# Categorías oficiales de PER
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

# Definir el patrón para PER Madrid 2025 Código de Test 01
PER_MADRID_2025_TEST_01 = ExamPattern(
    title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
    subtitle="Código de Test 01",
    answer_prefix="Respuestas al",
    total_questions=45,
    categories=PER_CATEGORIES,
    community="Madrid",
    year=2025,
    call="abril",  # Actualizado para coincidir con el PDF madrid-2025-abril.pdf
    test_code="test01"  # Actualizado para coincidir con el formato de archivo
)

# Definir el patrón para PER Madrid 2025 Código de Test 03 (que tiene pregunta anulada)
PER_MADRID_2025_TEST_03 = ExamPattern(
    title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
    subtitle="Código de Test 03",
    answer_prefix="Respuestas al",
    total_questions=45,
    categories=PER_CATEGORIES,
    community="Madrid",
    year=2025,
    call="abril",  # Actualizado para coincidir con el PDF madrid-2025-abril.pdf
    test_code="test03"  # Actualizado para coincidir con el formato de archivo
)

# Definir el patrón para PER Madrid 2025 Código de Test 02
PER_MADRID_2025_TEST_02 = ExamPattern(
    title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
    subtitle="Código de Test 02",
    answer_prefix="Respuestas al",
    total_questions=45,
    categories=PER_CATEGORIES,
    community="Madrid",
    year=2025,
    call="abril",
    test_code="test02"
)

# Definir el patrón para PER Madrid 2025 Código de Test 04
PER_MADRID_2025_TEST_04 = ExamPattern(
    title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
    subtitle="Código de Test 04",
    answer_prefix="Respuestas al",
    total_questions=45,
    categories=PER_CATEGORIES,
    community="Madrid",
    year=2025,
    call="abril",
    test_code="test04"
)

# Mantener compatibilidad con nombres anteriores
PER_TEST_01 = PER_MADRID_2025_TEST_01
PER_TEST_02 = PER_MADRID_2025_TEST_02
PER_TEST_03 = PER_MADRID_2025_TEST_03
PER_TEST_04 = PER_MADRID_2025_TEST_04

def create_per_pattern(community: str, year: int, call: str, test_code: str, 
                      total_questions: int = 45) -> ExamPattern:
    """
    Función helper para crear nuevos patrones de examen PER fácilmente.
    
    Args:
        community: Nombre de la comunidad autónoma (ej: "Madrid", "Barcelona", "Valencia")
        year: Año de realización (ej: 2025, 2024)
        call: Convocatoria (ej: "Ordinaria", "Extraordinaria", "Enero", "Junio")
        test_code: Código del test (ej: "Test01", "Test02", "Test03")
        total_questions: Número total de preguntas (por defecto 45)
    
    Returns:
        ExamPattern configurado para el examen especificado
    
    Ejemplo:
        # Para un examen de Valencia de junio 2024, test 02
        pattern = create_per_pattern("Valencia", 2024, "Junio", "Test02")
    """
    # Determinar el subtítulo basado en el código de test
    test_number = test_code.replace("Test", "").replace("test", "").zfill(2)
    subtitle = f"Código de Test {test_number}"
    
    return ExamPattern(
        title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
        subtitle=subtitle,
        answer_prefix="Respuestas al",
        total_questions=total_questions,
        categories=PER_CATEGORIES,
        community=community,
        year=year,
        call=call,
        test_code=test_code
    )

# Ejemplos de uso para otros exámenes:
# PER_VALENCIA_2024_JUNIO_TEST02 = create_per_pattern("Valencia", 2024, "Junio", "Test02")
# PER_BARCELONA_2023_EXTRAORDINARIA_TEST01 = create_per_pattern("Barcelona", 2023, "Extraordinaria", "Test01")

class ParametricExamExtractor:
    def __init__(self):
        self.questions = []
        self.answers = {}
    
    def generate_filename(self, pattern: ExamPattern, base_dir: str = "data") -> str:
        """
        Genera un nombre de archivo basado en los metadatos del examen.
        Formato: per-{modelo}-{comunidad}-{año}-{convocatoria}.yaml
        """
        # Normalizar valores para el nombre de archivo siguiendo el patrón oficial
        community_clean = pattern.community.lower().replace(" ", "-")
        call_clean = pattern.call.lower().replace(" ", "-")
        test_code_clean = pattern.test_code.lower()
        
        # Nuevo formato: per-test01-madrid-2025-abril.yaml
        filename = f"per-{test_code_clean}-{community_clean}-{pattern.year}-{call_clean}.yaml"
        return os.path.join(base_dir, filename)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae todo el texto del PDF."""
        print(f"📄 Extrayendo texto de {pdf_path}")
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    
    def find_exam_section(self, text: str, pattern: ExamPattern) -> Tuple[str, int, int]:
        """
        Encuentra la sección del examen específico en el texto.
        Retorna: (texto_seccion, posicion_inicio, posicion_fin)
        """
        # Permitir cabeceras intermedias entre el título y el subtítulo (hasta 200 caracteres)
        start_pattern = rf"{re.escape(pattern.title)}(.{{0,200}}?){re.escape(pattern.subtitle)}"
        print(f"🔍 Buscando patrón tolerante: {start_pattern}")
        start_match = re.search(start_pattern, text, re.IGNORECASE | re.DOTALL)
        if not start_match:
            # Si no encuentra, intentar patrón clásico por compatibilidad
            fallback_pattern = rf"{re.escape(pattern.title)}\s*{re.escape(pattern.subtitle)}"
            print(f"🔍 Buscando patrón clásico: {fallback_pattern}")
            start_match = re.search(fallback_pattern, text, re.IGNORECASE | re.DOTALL)
            if not start_match:
                print(f"❌ No se encontró el patrón de inicio del examen")
                return "", 0, 0
        start_pos = start_match.start()
        print(f"✅ Examen encontrado en posición: {start_pos}")
        
        # Buscar el final del examen (inicio del siguiente examen o final del documento)
        exam_text_from_start = text[start_pos:]
        
        # Patrones que indican el final del examen actual
        end_patterns = [
            rf"{re.escape(pattern.title)}\s*Código de Test \d+",  # Siguiente modelo del mismo examen
            r"EXAMEN DE [^{]+?Código de Test \d+",  # Cualquier otro examen
            r"Respuestas al EXAMEN"  # Inicio de respuestas
        ]
        
        end_pos = len(exam_text_from_start)
        for end_pattern in end_patterns:
            # Buscar después de los primeros 500 caracteres para evitar el título actual
            match = re.search(end_pattern, exam_text_from_start[500:], re.IGNORECASE)
            if match:
                candidate_end = match.start() + 500
                if candidate_end < end_pos:
                    end_pos = candidate_end
                    print(f"✅ Final encontrado con patrón: {end_pattern[:30]}... en posición: {candidate_end}")
                    break
        
        exam_section = exam_text_from_start[:end_pos]
        print(f"📊 Sección del examen extraída: {len(exam_section)} caracteres")
        
        return exam_section, start_pos, start_pos + end_pos
    
    def find_answer_section(self, text: str, pattern: ExamPattern) -> str:
        """
        Encuentra la sección de respuestas para el examen específico.
        """
        # Buscar la sección de respuestas específica para este test
        answer_pattern = rf"Respuestas\s+al\s+{re.escape(pattern.title)}\s*{re.escape(pattern.subtitle)}"
        
        match = re.search(answer_pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            print(f"❌ No se encontró la sección de respuestas para {pattern.subtitle}")
            return ""
        
        print(f"✅ Sección de respuestas encontrada")
        
        # Extraer la sección de respuestas
        answer_text = text[match.end():]
        
        # Buscar el final (siguiente test o fin de documento)
        end_patterns = [
            r"Respuestas\s+al\s+EXAMEN",
            r"EXAMEN\s+DE.*?Código\s+de\s+Test"
        ]
        
        end_pos = len(answer_text)
        for end_pattern in end_patterns:
            end_match = re.search(end_pattern, answer_text[100:], re.IGNORECASE)
            if end_match:
                end_pos = end_match.start() + 100
                break
        
        answer_section = answer_text[:end_pos]
        print(f"📊 Sección de respuestas: {len(answer_section)} caracteres")
        
        return answer_section
    
    def parse_questions_from_section(self, exam_section: str, pattern: ExamPattern) -> List[Dict]:
        """
        Extrae las preguntas de la sección del examen organizadas por categorías.
        """
        questions = []
        
        # Mapear títulos de categorías a números de categoría
        category_title_map = {
            "nomenclatura náutica": 1,
            "elementos de amarre y fondeo": 2,
            "seguridad": 3,
            "legislación": 4,
            "balizamiento": 5,
            "reglamento (ripa)": 6,
            "maniobra y navegación": 7,
            "emergencias en la mar": 8,
            "meteorología": 9,
            "teoría de la navegación": 10,
            "carta de navegación": 11
        }
        
        # Dividir el texto en líneas para procesamiento secuencial
        lines = exam_section.split('\n')
        current_category = 1  # Categoría por defecto
        current_category_name = pattern.categories[1]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Verificar si la línea es un título de categoría
            line_lower = line.lower().rstrip('.')
            if line_lower in category_title_map:
                current_category = category_title_map[line_lower]
                current_category_name = pattern.categories[current_category]
                print(f"� Encontrada categoría: {current_category} - {current_category_name}")
                i += 1
                continue
            # Verificar si la línea es una pregunta numerada con texto en la misma línea
            question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', line)
            if question_match:
                question_num = int(question_match.group(1))
                question_text_start = question_match.group(2)
                # Solo procesar preguntas en el rango válido
                if question_num < 1 or question_num > pattern.total_questions:
                    i += 1
                    continue
                # Verificar que NO sea parte de una regla del RIPA
                is_ripa_rule = (re.search(r'del\s+RIPA', question_text_start, re.IGNORECASE) or
                               re.search(r'de\s+la\s+Regla', question_text_start, re.IGNORECASE) or
                               re.search(r'Regla\s+\d+', line, re.IGNORECASE))
                if is_ripa_rule:
                    i += 1
                    continue
                # Recopilar todo el contenido de la pregunta
                question_content = question_match.group(2)
                i += 1
                # Continuar leyendo líneas hasta encontrar la siguiente pregunta o categoría
                while i < len(lines):
                    next_line = lines[i].strip()
                    question_pattern_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', next_line)
                    if question_pattern_match:
                        potential_question_num = int(question_pattern_match.group(1))
                        question_text_start = question_pattern_match.group(2)
                        is_valid_question_num = (1 <= potential_question_num <= pattern.total_questions and 
                                               potential_question_num > question_num)
                        is_ripa_rule = (re.search(r'del\s+RIPA', question_text_start, re.IGNORECASE) or
                                       re.search(r'de\s+la\s+Regla', question_text_start, re.IGNORECASE) or
                                       re.search(r'Regla\s+\d+', next_line, re.IGNORECASE))
                        if is_valid_question_num and not is_ripa_rule:
                            break
                    next_line_lower = next_line.lower().rstrip('.')
                    if next_line_lower in category_title_map:
                        break
                    if next_line:
                        question_content += '\n' + next_line
                    i += 1
                question_data = self._parse_single_question(question_num, question_content, current_category, current_category_name)
                if question_data and self._is_valid_question(question_data):
                    questions.append(question_data)
                continue
            # NUEVO: Verificar si la línea es solo el número de pregunta (ej: '42') y el texto empieza en la siguiente línea
            question_number_only = re.match(r'^\s*(\d{1,2})\s*$', line)
            if question_number_only:
                question_num = int(question_number_only.group(1))
                if question_num < 1 or question_num > pattern.total_questions:
                    i += 1
                    continue
                # Recoger el texto de la pregunta de la(s) siguiente(s) línea(s)
                i += 1
                question_content_lines = []
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Parar si encontramos la siguiente pregunta numerada o categoría
                    next_question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', next_line)
                    next_question_number_only = re.match(r'^\s*(\d{1,2})\s*$', next_line)
                    next_line_lower = next_line.lower().rstrip('.')
                    if (next_question_match or next_question_number_only or next_line_lower in category_title_map):
                        break
                    if next_line:
                        question_content_lines.append(next_line)
                    i += 1
                question_content = '\n'.join(question_content_lines)
                question_data = self._parse_single_question(question_num, question_content, current_category, current_category_name)
                if question_data and self._is_valid_question(question_data):
                    questions.append(question_data)
                continue
            # Si no es pregunta ni categoría, avanzar
            i += 1
        
        # Ordenar por ID para asegurar orden secuencial
        questions.sort(key=lambda x: x['id'])
        
        # NUEVA MEJORA: Detectar y eliminar duplicados por ID
        questions = self._remove_duplicate_ids(questions)
        
        # Buscar preguntas faltantes y intentar recuperarlas
        extracted_ids = set(q['id'] for q in questions)
        expected_ids = set(range(1, pattern.total_questions + 1))
        missing_ids = expected_ids - extracted_ids
        
        if missing_ids:
            print(f"⚠️  Preguntas faltantes detectadas: {sorted(missing_ids)}")
            print("🔍 Intentando recuperar preguntas faltantes...")
            
            # Buscar fragmentos que podrían ser preguntas faltantes
            recovered_questions = self._recover_missing_questions(exam_section, missing_ids, pattern, category_title_map)
            # Validar preguntas recuperadas
            valid_recovered = [q for q in recovered_questions if self._is_valid_question(q)]
            questions.extend(valid_recovered)
            questions.sort(key=lambda x: x['id'])
            
            # Eliminar duplicados una vez más después de la recuperación
            questions = self._remove_duplicate_ids(questions)
        
        print(f"✅ Extraídas {len(questions)} preguntas organizadas por categorías")
        return questions
    
    def _parse_single_question(self, question_num: int, content: str, category: int, category_name: str) -> Dict:
        """
        Procesa una pregunta individual y extrae su información.
        """
        # Separar líneas y encontrar pregunta y opciones
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(lines) < 2:  # Necesita al menos algo de contenido
            return None
        
        # Identificar pregunta y opciones
        question_lines = []
        options = {}  # Cambiar a diccionario con letras como claves
        options_started = False
        current_option_letter = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Buscar opciones a), b), c), d)
            option_match = re.match(r'^([a-d])\)\s*(.+)', line, re.IGNORECASE)
            if option_match:
                options_started = True
                current_option_letter = option_match.group(1).lower()
                option_text = option_match.group(2).strip()
                
                # Continuar leyendo líneas hasta encontrar la siguiente opción o el final
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # Verificar si la siguiente línea es una nueva opción
                    next_option_match = re.match(r'^([a-d])\)\s*(.+)', next_line, re.IGNORECASE)
                    if next_option_match:
                        # Es una nueva opción, no procesamos esta línea aquí
                        break
                    
                    # Verificar si es texto administrativo que no debería estar en la opción
                    admin_patterns = [
                        r'SUBDIRECCIÓN GENERAL',
                        r'ÁREA FUNCIONAL',
                        r'MINISTERIO',
                        r'DIRECCIÓN GENERAL',
                        r'CAPITANÍA MARÍTIMA',
                        r'GOBIERNO DE',
                        r'COMUNIDAD AUTÓNOMA',
                        r'CONSEJERÍA',
                        r'DEPARTAMENTO',
                        r'PÁGINA \d+',
                        r'^\d+\s*$',  # Solo números
                        r'^\d+\s*/\s*\d+\s*$',  # Numeración de páginas como "3/45"
                        r'EXAMEN DE PATRÓN',
                        r'CÓDIGO DE TEST',
                        r'MADRID\s*\d{4}',  # "MADRID 2025" etc.
                        r'ABRIL\s*\d{4}',   # "ABRIL 2025" etc.
                        r'JUNIO\s*\d{4}',   # "JUNIO 2024" etc.
                        r'NOVIEMBRE\s*\d{4}', # "NOVIEMBRE 2024" etc.
                        r'CONVOCATORIA',
                        r'ORDINARIA',
                        r'EXTRAORDINARIA',
                        r'NÁUTICA DE RECREO',
                        r'SEGURIDAD.*MARÍTIMA',
                        r'INSPECCIÓN MARÍTIMA',
                        r'CONTAMINACIÓN',
                        r'MADRID\s*[-–]\s*\d{4}',  # "MADRID - 2025" etc.
                        r'^\s*\d{1,2}\s*$'  # Líneas con solo números del 1-99
                    ]
                    
                    is_admin_text = any(re.search(pattern, next_line, re.IGNORECASE) for pattern in admin_patterns)
                    if is_admin_text:
                        # No incluir texto administrativo en la opción
                        break
                    
                    # Verificar si es muy similar al texto ya existente (posible repetición)
                    if len(option_text) > 20 and next_line.strip() in option_text:
                        break
                    
                    # Verificar si la línea podría ser el inicio de una nueva pregunta
                    potential_question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', next_line)
                    if potential_question_match:
                        potential_num = int(potential_question_match.group(1))
                        if 1 <= potential_num <= 45:  # Rango válido de preguntas
                            break
                    
                    # Es continuación de la opción actual
                    if next_line.strip():  # Solo agregar si no está vacía
                        option_text += ' ' + next_line.strip()
                    i += 1
                
                options[current_option_letter] = option_text
                # No incrementamos i aquí porque el bucle while ya lo hizo
                continue
            elif not options_started:
                # Si no hemos empezado con opciones, es parte de la pregunta
                question_lines.append(line)
            
            i += 1
        
        # Construir pregunta
        question_text = ' '.join(question_lines).strip()
        
        # Ser más tolerante: si no hay opciones suficientes, crear opciones por defecto
        expected_letters = ['a', 'b', 'c', 'd']
        for letter in expected_letters:
            if letter not in options:
                print(f"⚠️  Pregunta {question_num}: Falta opción {letter}, añadiendo por defecto")
                options[letter] = f"Opción {letter.upper()} (contenido incompleto)"
        
        # Validar que tenemos al menos una pregunta
        if len(question_text) < 5:
            # Si la pregunta es muy corta, usar todo el contenido
            question_text = ' '.join(lines).strip()
            if len(question_text) < 10:
                question_text = f"Pregunta {question_num} (contenido incompleto): {question_text}"
        
        # Crear la pregunta con nuevo formato
        return {
            'id': question_num,
            'question': question_text,
            'options': options,  # Ahora es un diccionario {'a': 'texto', 'b': 'texto', ...}
            'correct_answer': None,  # Se asignará después (será una letra a-d)
            'category': category,
            'category_name': category_name
        }
    
    def parse_answers_from_section(self, answer_section: str) -> Dict[int, str]:
        """
        Extrae las respuestas de la sección de respuestas.
        """
        answers = {}
        
        # El formato típico es: B 1 B 2 B 3 C 4 C 5 C 6 B 7 D 8...
        # Buscar pares letra-número
        answer_pairs = re.findall(r'([A-D])\s+(\d+)', answer_section)
        
        print(f"🔍 Encontrados {len(answer_pairs)} pares de respuesta")
        
        for letter, number in answer_pairs:
            question_num = int(number)
            # Solo incluir números de pregunta válidos (1-45)
            if 1 <= question_num <= 45:
                answers[question_num] = letter
        
        # Buscar respuestas anuladas con el formato específico del PDF
        # Formato encontrado: "45 1 ANULADA (Todas las respuestas se dan por válidas)"
        # Esto significa que después del número de pregunta hay una respuesta que está anulada
        
        # Patrón 1: Buscar "número respuesta ANULADA"
        anulada_pattern_1 = r'(\d+)\s+[A-D1-9]\s+ANULADA'
        matches_1 = re.findall(anulada_pattern_1, answer_section, re.IGNORECASE)
        for match in matches_1:
            question_num = int(match)
            if 1 <= question_num <= 45:
                answers[question_num] = "ANULADA"
                print(f"⚠️  Pregunta {question_num} marcada como ANULADA (patrón 1)")
        
        # Patrón 2: Buscar patrones más tradicionales
        anulada_patterns = [
            r'Pregunta\s+(\d+)\s+ANULADA',          # "Pregunta 42 ANULADA"
            r'(\d+)\s*[-:]\s*ANULADA',              # "42 - ANULADA" o "42: ANULADA"
            r'(\d+)\s+ANULADA\s*\([^)]*\)',         # "42 ANULADA (Todas las respuestas...)"
            r'(\d+)\s+ANULADA(?:\s|$)',             # "42 ANULADA" seguido de espacio o fin
        ]
        
        for pattern in anulada_patterns:
            matches = re.findall(pattern, answer_section, re.IGNORECASE)
            for match in matches:
                question_num = int(match if isinstance(match, str) else match[0])
                if 1 <= question_num <= 45:
                    answers[question_num] = "ANULADA"
                    print(f"⚠️  Pregunta {question_num} marcada como ANULADA (patrón tradicional)")
        
        # Log para debugging
        if 'anulada' in answer_section.lower():
            print("ℹ️  Texto 'ANULADA' encontrado en sección de respuestas")
            # Mostrar contexto alrededor de "ANULADA"
            lines = answer_section.split('\n')
            for i, line in enumerate(lines):
                if 'anulada' in line.lower():
                    context_start = max(0, i-2)
                    context_end = min(len(lines), i+3)
                    print(f"    Contexto líneas {context_start}-{context_end}:")
                    for j in range(context_start, context_end):
                        marker = ">>> " if j == i else "    "
                        print(f"    {marker}{lines[j]}")
        
        print(f"✅ Extraídas {len(answers)} respuestas")
        return answers
    
    def classify_question_by_content(self, question_text: str, categories: Dict[int, str]) -> int:
        """
        Clasifica una pregunta en una categoría basándose en su contenido.
        """
        question_lower = question_text.lower()
        
        # Patrones específicos para PER (se puede extender para otros exámenes)
        if categories == PER_CATEGORIES:
            # **DETECCIÓN PRIORITARIA DE RIPA**: Si menciona "ripa" o "regla X del ripa", es categoría 6
            # Patrones más amplios y específicos para detectar preguntas del RIPA
            ripa_patterns = [
                r'\bripa\b',  # Menciona "ripa" explícitamente
                r'regla\s+\d+\s+del\s+ripa',  # "regla X del ripa"
                r'según\s+la\s+regla\s+\d+',  # "según la regla X"
                r'conforme\s+a\s+la\s+regla\s+\d+',  # "conforme a la regla X"
                r'de\s+acuerdo\s+con\s+la\s+regla\s+\d+',  # "de acuerdo con la regla X"
                r'regla\s+\d+.*ripa',  # "regla X ... ripa"
                r'con\s+arreglo\s+a\s+la\s+regla\s+\d+',  # "con arreglo a la regla X"
                r'lo\s+establecido\s+en\s+la\s+regla\s+\d+',  # "lo establecido en la regla X"
                r'por\s+la\s+regla\s+\d+',  # "por la regla X"
                r'en\s+la\s+regla\s+\d+',  # "en la regla X"
                r'la\s+regla\s+\d+\s+establece',  # "la regla X establece"
                r'aplicación.*regla\s+\d+',  # "aplicación ... regla X"
                r'ámbito\s+de\s+aplicación.*regla',  # "ámbito de aplicación ... regla"
            ]
            
            for pattern in ripa_patterns:
                if re.search(pattern, question_lower):
                    return 6  # Categoría RIPA
            
            # Primero verificar reglas específicas para casos problemáticos
            if any(word in question_lower for word in ["nudo", "gaza", "cornamusa", "chicote", "amarrar", "fondear", "cabo"]):
                # Si menciona múltiples términos de amarre, es categoría 2
                amarre_count = sum(1 for word in ["nudo", "gaza", "cornamusa", "chicote", "amarrar", "fondear", "cabo", "filar", "virar", "levar"] if word in question_lower)
                if amarre_count >= 2:
                    return 2
            
            category_patterns = {
                1: ["bocina", "proa", "popa", "babor", "estribor", "eslora", "manga", "puntal", "calado", 
                    "casco", "cubierta", "timón", "roda", "codaste", "quilla", "aleta", "través", "desplazamiento", "crujía"],
                2: ["ancla", "fondeo", "amarre", "cabo", "nudo", "bita", "cornamusa", "muerto", "rezón",
                    "cadena", "orinque", "garreo", "virar", "filar", "levar", "zarpar", "llano", "gaza", "chicote", "amarrar", "sonda", "fondear", "lascar"],
                3: ["chaleco", "balsa", "bengala", "extintor", "botiquín", "supervivencia", "salvavidas",
                    "emergencia", "socorro", "epirb", "abandono", "rescate", "helicóptero", "aro", "estiba"],
                4: ["capitanía", "despacho", "permiso", "licencia", "normativa", "ley", "reglamento",
                    "autoridad", "certificado", "navegabilidad", "zona", "obligatorio"],
                5: ["boya", "baliza", "faro", "luz", "señal", "cardinal", "lateral", "marca", "enfilación",
                    "sector", "destellos", "ocultaciones", "ritmo", "alcance"],
                6: ["abordaje", "rumbo", "cruce", "alcance", "maniobra", "preferencia", "paso", "ripa",
                    "buque", "embarcación", "motor", "vela", "fondeado", "visibilidad", "luces", "marcas", "señales", "acústicas", "luminosas"],
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
        else:
            # Para otros exámenes, usar clasificación básica
            category_patterns = {i: [] for i in categories.keys()}
        
        # Contar coincidencias por categoría
        category_scores = {}
        for category, patterns in category_patterns.items():
            score = sum(1 for pattern in patterns if pattern in question_lower)
            if score > 0:
                category_scores[category] = score
        
        # Devolver la categoría con mayor puntuación, o la primera categoría por defecto
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return list(categories.keys())[0]  # Primera categoría por defecto
    
    def extract_exam(self, questions_pdf: str, pattern: ExamPattern) -> Dict:
        """
        Extrae un examen completo usando el patrón especificado.
        Solo extrae las preguntas, sin respuestas.
        """
        print(f"🚢 Extrayendo examen: {pattern.title} - {pattern.subtitle}")
        
        # Extraer preguntas del PDF
        questions_text = self.extract_text_from_pdf(questions_pdf)
        exam_section, _, _ = self.find_exam_section(questions_text, pattern)
        
        if not exam_section:
            print("❌ No se pudo encontrar la sección del examen")
            return {}
        
        questions = self.parse_questions_from_section(exam_section, pattern)
        print(f"✅ Extraídas {len(questions)} preguntas organizadas por categorías")
        
        # Nota: Las respuestas se asignarán usando el script OCR madrid_extract_answers.py
        print("💡 Consejo: Usa 'python madrid_extract_answers.py --exam-type PER --test-model TEST01' para extraer respuestas")
        
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
                'title': pattern.title,
                'subtitle': pattern.subtitle,
                'total_questions': len(questions),
                'expected_questions': pattern.total_questions,
                'categories': len(questions_by_category),
                'questions_with_answers': sum(1 for q in questions if q['correct_answer'] is not None),
                # Nuevos metadatos
                'community': pattern.community,
                'year': pattern.year,
                'call': pattern.call,
                'test_code': pattern.test_code
            },
            'categories': {}
        }
        
        for category_id, category_questions in questions_by_category.items():
            exam_data['categories'][category_id] = {
                'name': pattern.categories[category_id],
                'questions': category_questions
            }
        
        return exam_data
    
    def save_to_yaml(self, data: Dict, output_path: str):
        """Guarda los datos en formato YAML."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        print(f"💾 Datos guardados en {output_path}")
    
    def _recover_missing_questions(self, exam_section: str, missing_ids: set, pattern: ExamPattern, category_title_map: Dict[str, int]) -> List[Dict]:
        """
        Intenta recuperar preguntas que no fueron extraídas correctamente.
        """
        recovered = []
        lines = exam_section.split('\n')
        
        for missing_id in sorted(missing_ids):
            print(f"🔍 Buscando pregunta {missing_id}...")
            
            # Buscar patrones más específicos para evitar falsos positivos
            for i, line in enumerate(lines):
                # Patrón específico: número + espacio + texto que no sea solo número
                pattern_match = re.match(rf'^\s*{missing_id}\s+([^\d\s].*)', line)
                if pattern_match:
                    print(f"✓ Posible coincidencia para pregunta {missing_id} en línea {i}: {line[:80]}...")
                    
                    # Recopilar contenido desde esta línea
                    content_lines = [pattern_match.group(1)]  # Usar solo el texto después del número
                    j = i + 1
                    collected_chars = len(pattern_match.group(1))
                    
                    while j < len(lines) and collected_chars < 1000:  # Límite de seguridad
                        current_line = lines[j].strip()
                        if not current_line:
                            j += 1
                            continue
                        
                        # Parar si encontramos otra pregunta numerada válida
                        next_question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', current_line)
                        if next_question_match:
                            next_num = int(next_question_match.group(1))
                            if 1 <= next_num <= pattern.total_questions and next_num != missing_id:
                                break
                        
                        # Parar si encontramos una nueva categoría
                        current_line_lower = current_line.lower().rstrip('.')
                        if current_line_lower in category_title_map:
                            break
                        
                        content_lines.append(current_line)
                        collected_chars += len(current_line)
                        j += 1
                    
                    if content_lines:
                        content = '\n'.join(content_lines)
                        
                        # Asignar a una categoría por defecto o intentar detectarla
                        category = 1  # Por defecto
                        category_name = pattern.categories[1]
                        
                        # Intentar detectar categoría basándose en contenido previo
                        for k in range(max(0, i-10), i):
                            prev_line = lines[k].strip().lower().rstrip('.')
                            if prev_line in category_title_map:
                                category = category_title_map[prev_line]
                                category_name = pattern.categories[category]
                                break
                        
                        # Intentar clasificar por contenido si no se encontró categoría
                        if category == 1:
                            category = self.classify_question_by_content(content, pattern.categories)
                            category_name = pattern.categories[category]
                        
                        print(f"✅ Recuperada pregunta {missing_id} en categoría {category_name}")
                        
                        question_data = self._parse_single_question(missing_id, content, category, category_name)
                        if question_data:
                            recovered.append(question_data)
                        break
            
            # Si ya recuperamos la pregunta, pasar a la siguiente
            if any(q['id'] == missing_id for q in recovered):
                continue
        
        return recovered

    def _is_valid_question(self, question_data: Dict) -> bool:
        """
        Valida si una pregunta extraída es válida y completa.
        
        Criterios de validación:
        1. La pregunta debe tener al menos 10 caracteres de texto significativo
        2. Debe tener las 4 opciones (a, b, c, d)
        3. El texto de la pregunta no debe ser solo fragmentos o palabras sueltas
        4. Las opciones deben tener contenido mínimo
        """
        if not question_data:
            return False
        
        question_text = question_data.get('question', '').strip()
        options = question_data.get('options', {})
        
        # 1. Validar longitud mínima de la pregunta
        if len(question_text) < 10:
            print(f"❌ Pregunta {question_data.get('id')} rechazada: texto muy corto ('{question_text}')")
            return False
        
        # 2. Filtrar fragmentos que claramente no son preguntas
        invalid_fragments = [
            'millas.',
            'metros.',
            'nudos.',
            'grados.',
            'minutos.',
            'segundos.',
            'horas.',
            'días.',
            'años.',
        ]
        
        if question_text.lower() in invalid_fragments:
            print(f"❌ Pregunta {question_data.get('id')} rechazada: fragmento inválido ('{question_text}')")
            return False
        
        # 3. Validar que tenga las 4 opciones
        expected_options = {'a', 'b', 'c', 'd'}
        if not expected_options.issubset(set(options.keys())):
            missing_options = expected_options - set(options.keys())
            print(f"❌ Pregunta {question_data.get('id')} rechazada: faltan opciones {missing_options}")
            return False
        
        # 4. Validar que las opciones tengan contenido mínimo
        for letter, option_text in options.items():
            if len(option_text.strip()) < 3:
                print(f"⚠️  Pregunta {question_data.get('id')} opción {letter} muy corta: '{option_text.strip()}' (revisar manualmente)")
        
        # 5. Validar que la pregunta tenga estructura de pregunta (signos de interrogación, etc.)
        # o al menos contenido sustancial
        has_question_structure = (
            '?' in question_text or
            ':' in question_text or  # Muchas preguntas terminan con ":"
            question_text.lower().startswith(('qué', 'cuál', 'cómo', 'dónde', 'cuándo', 'por qué', 'indique', 'señale', 'conforme', 'según', 'de acuerdo', 'en relación', 'con respecto', 'ante una', 'en caso de', 'se define', 'todo buque', 'un buque')) or
            len(question_text.split()) >= 4 or  # Relajado: al menos 4 palabras
            question_text.strip().endswith('...')  # O termina en puntos suspensivos
        )
        
        if not has_question_structure:
            print(f"❌ Pregunta {question_data.get('id')} rechazada: no parece una pregunta válida ('{question_text[:50]}...')")
            return False
        
        return True

    def _remove_duplicate_ids(self, questions: List[Dict]) -> List[Dict]:
        """
        Elimina preguntas duplicadas basándose en el ID, manteniendo la de mejor calidad.
        """
        from collections import defaultdict
        
        # Agrupar preguntas por ID
        questions_by_id = defaultdict(list)
        for q in questions:
            questions_by_id[q['id']].append(q)
        
        # Resolver duplicados
        final_questions = []
        for question_id, question_list in questions_by_id.items():
            if len(question_list) == 1:
                # No hay duplicados
                final_questions.append(question_list[0])
            else:
                # Hay duplicados, elegir el mejor
                print(f"⚠️  Detectados {len(question_list)} duplicados para pregunta {question_id}")
                
                best_question = self._choose_best_question(question_list)
                final_questions.append(best_question)
                
                # Mostrar información de debug
                for i, q in enumerate(question_list):
                    marker = "✅ ELEGIDA" if q == best_question else "❌ Descartada"
                    print(f"   {marker}: '{q['question'][:50]}...' (categoría {q['category']})")
        
        return final_questions

    def _choose_best_question(self, question_candidates: List[Dict]) -> Dict:
        """
        Elige la mejor pregunta entre varios candidatos duplicados.
        
        Criterios de selección (en orden de prioridad):
        1. Pregunta con todas las opciones válidas
        2. Pregunta con texto más largo y sustancial
        3. Pregunta que no contenga fragmentos como "contenido incompleto"
        4. Pregunta de categoría más apropiada según contenido
        """
        # Filtrar candidatos válidos
        valid_candidates = [q for q in question_candidates if self._is_valid_question(q)]
        
        if not valid_candidates:
            # Si ninguno es válido, tomar el que tenga más texto
            return max(question_candidates, key=lambda q: len(q.get('question', '')))
        
        if len(valid_candidates) == 1:
            return valid_candidates[0]
        
        # Múltiples candidatos válidos, aplicar criterios de calidad
        def quality_score(question):
            score = 0
            text = question.get('question', '')
            options = question.get('options', {})
            
            # Puntos por longitud del texto
            score += len(text)
            
            # Penalizar si contiene "incompleto"
            if 'incompleto' in text.lower():
                score -= 50
            
            # Puntos por opciones de calidad
            for option_text in options.values():
                if 'incompleto' in option_text.lower():
                    score -= 10
                else:
                    score += len(option_text)
            
            # Bonos por estructura de pregunta
            if '?' in text:
                score += 20
            
            if any(starter in text.lower() for starter in ['qué', 'cuál', 'cómo', 'indique', 'señale']):
                score += 15
            
            return score
        
        # Elegir el candidato con mayor puntuación
        best_candidate = max(valid_candidates, key=quality_score)
        return best_candidate


def main():
    """
    Función principal para ejecutar el extractor desde línea de comandos.
    
    Extrae preguntas de exámenes PER desde archivos PDF oficiales y las organiza
    por categorías en formato YAML estructurado.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='🚢 Extractor de Preguntas de Exámenes PER desde PDFs',
        epilog='''
Ejemplos de uso:
  %(prog)s --input-file data/raw/questions/madrid-2025-abril.pdf --test-code test01
  %(prog)s --input-file /ruta/completa/examen.pdf --test-code test04 --output-dir mi_directorio --verbose
  
Este script extrae preguntas de exámenes PER de archivos PDF oficiales y las
organiza automáticamente por categorías (Nomenclatura, RIPA, Seguridad, etc.)
generando archivos YAML estructurados listos para su procesamiento.

Categorías PER soportadas:
  1. Nomenclatura náutica        7. Maniobra y navegación
  2. Elementos de amarre         8. Emergencias en la mar  
  3. Seguridad                   9. Meteorología
  4. Legislación                10. Teoría de la navegación
  5. Balizamiento               11. Carta de navegación
  6. Reglamento (RIPA)

El archivo de salida seguirá el formato: per-{test}-{comunidad}-{año}-{convocatoria}.yaml
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input-file', required=True, 
                       help='Archivo PDF con las preguntas del examen')
    parser.add_argument('--test-code', required=True, 
                       choices=['test01', 'test02', 'test03', 'test04'], 
                       help='Código del test a extraer. Disponibles: test01, test02, test03, test04')
    parser.add_argument('--output-dir', default='data/exams', 
                       help='Directorio donde guardar el archivo YAML (default: data/exams)')
    parser.add_argument('--verbose', action='store_true',
                       help='Mostrar información detallada del procesamiento')
    
    args = parser.parse_args()
    
    # Detectar automáticamente año y convocatoria desde el nombre del archivo PDF
    pdf_filename = os.path.basename(args.input_file)
    
    # Extraer información del nombre del archivo (formato: madrid-YYYY-convocatoria.pdf)
    import re
    match = re.search(r'madrid-(\d{4})-(\w+)\.pdf', pdf_filename)
    
    if match:
        year = int(match.group(1))
        call = match.group(2)
        if args.verbose:
            print(f"📅 Detectado automáticamente: Año {year}, Convocatoria {call}")
    else:
        # Valores por defecto si no se puede detectar
        year = 2025
        call = "abril"
        if args.verbose:
            print(f"⚠️  No se pudo detectar año/convocatoria del nombre del archivo, usando valores por defecto: {year} {call}")
    
    # Crear patrón dinámicamente basado en los parámetros
    pattern = create_per_pattern("Madrid", year, call, args.test_code)
    
    if args.verbose:
        print(f"🚢 Extractor de Preguntas PER")
        print(f"📋 Examen: {pattern.title}")
        print(f"🏷️  Test: {pattern.subtitle}")
        print(f"📄 PDF origen: {args.input_file}")
        print(f"📁 Directorio salida: {args.output_dir}")
        print("-" * 60)
    
    # Verificar que el archivo PDF existe
    if not os.path.exists(args.input_file):
        print(f"❌ Error: No se encuentra el archivo PDF: {args.input_file}")
        print(f"💡 Verifica que la ruta sea correcta y que el archivo exista")
        return 1
    
    # Crear el extractor y procesar
    extractor = ParametricExamExtractor()
    
    try:
        # Extraer el examen
        exam_data = extractor.extract_exam(args.input_file, pattern)
        
        if not exam_data:
            print("❌ Error: No se pudo extraer el examen")
            return 1
        
        # Generar nombre de archivo de salida
        output_file = extractor.generate_filename(pattern, args.output_dir)
        
        # Guardar en YAML
        extractor.save_to_yaml(exam_data, output_file)
        
        # Mostrar resumen
        exam_info = exam_data.get('exam_info', {})
        print(f"\n📊 Resumen de extracción:")
        print(f"   ✅ Preguntas extraídas: {exam_info.get('total_questions', 0)}/{exam_info.get('expected_questions', 0)}")
        print(f"   📚 Categorías encontradas: {exam_info.get('categories', 0)}")
        print(f"   📝 Preguntas con respuestas: {exam_info.get('questions_with_answers', 0)}")
        print(f"   💾 Archivo guardado: {output_file}")
        
        if args.verbose:
            print(f"\n💡 Para agregar respuestas, usa:")
            print(f"   python madrid_extract_answers_v2.py --input-file respuestas.pdf")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error durante la extracción: {str(e)}")
        print(f"💡 Verifica que el PDF contenga el examen especificado ({pattern.subtitle})")
        return 1


if __name__ == "__main__":
    exit(main())
