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
    call="Ordinaria",
    test_code="Test01"
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
    call="Ordinaria",
    test_code="Test03"
)

# Mantener compatibilidad con nombres anteriores
PER_TEST_01 = PER_MADRID_2025_TEST_01
PER_TEST_03 = PER_MADRID_2025_TEST_03

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
        Formato: per_{comunidad}_{año}_{convocatoria}_{codigo_test}.yaml
        """
        # Normalizar valores para el nombre de archivo
        community_clean = pattern.community.lower().replace(" ", "_")
        call_clean = pattern.call.lower().replace(" ", "_")
        test_code_clean = pattern.test_code.lower()
        
        filename = f"per_{community_clean}_{pattern.year}_{call_clean}_{test_code_clean}.yaml"
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
        # Construir patrón de búsqueda para el inicio del examen
        start_pattern = rf"{re.escape(pattern.title)}\s*{re.escape(pattern.subtitle)}"
        
        print(f"🔍 Buscando patrón: {start_pattern}")
        
        start_match = re.search(start_pattern, text, re.IGNORECASE | re.DOTALL)
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
            
            # Verificar si la línea es una pregunta numerada de forma más específica
            # Debe ser: número al inicio + espacio + texto que no sea solo número
            question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', line)
            if question_match:
                question_num = int(question_match.group(1))
                
                # Solo procesar preguntas en el rango válido
                if question_num < 1 or question_num > pattern.total_questions:
                    i += 1
                    continue
                
                # Recopilar todo el contenido de la pregunta
                question_content = question_match.group(2)
                i += 1
                
                # Continuar leyendo líneas hasta encontrar la siguiente pregunta o categoría
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Parar si encontramos la siguiente pregunta numerada
                    # Ser más específico: número válido + espacio + texto que no sea solo número
                    if re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', next_line):
                        next_question_num = int(re.match(r'^\s*(\d{1,2})', next_line).group(1))
                        # Solo parar si es un número de pregunta válido y mayor al actual
                        if 1 <= next_question_num <= pattern.total_questions and next_question_num > question_num:
                            break
                    
                    # Parar si encontramos una nueva categoría
                    next_line_lower = next_line.lower().rstrip('.')
                    if next_line_lower in category_title_map:
                        break
                    
                    # Añadir la línea al contenido de la pregunta
                    if next_line:
                        question_content += '\n' + next_line
                    i += 1
                
                # Procesar el contenido completo de la pregunta
                question_data = self._parse_single_question(question_num, question_content, current_category, current_category_name)
                if question_data:
                    questions.append(question_data)
            else:
                i += 1
        
        # Ordenar por ID para asegurar orden secuencial
        questions.sort(key=lambda x: x['id'])
        
        # Buscar preguntas faltantes y intentar recuperarlas
        extracted_ids = set(q['id'] for q in questions)
        expected_ids = set(range(1, pattern.total_questions + 1))
        missing_ids = expected_ids - extracted_ids
        
        if missing_ids:
            print(f"⚠️  Preguntas faltantes detectadas: {sorted(missing_ids)}")
            print("🔍 Intentando recuperar preguntas faltantes...")
            
            # Buscar fragmentos que podrían ser preguntas faltantes
            recovered_questions = self._recover_missing_questions(exam_section, missing_ids, pattern, category_title_map)
            questions.extend(recovered_questions)
            questions.sort(key=lambda x: x['id'])
        
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
        
        for line in lines:
            # Buscar opciones a), b), c), d)
            option_match = re.match(r'^([a-d])\)\s*(.+)', line, re.IGNORECASE)
            if option_match:
                options_started = True
                option_letter = option_match.group(1).lower()
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            elif not options_started:
                # Si no hemos empezado con opciones, es parte de la pregunta
                question_lines.append(line)
        
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
        
        # Nota: Las respuestas se asignarán usando el script OCR analyze_pdf_structure.py
        print("💡 Consejo: Usa 'python analyze_pdf_structure.py --exam-type PER --test-model TEST01' para extraer respuestas")
        
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

def main():
    """Función principal para extraer el examen de PER."""
    extractor = ParametricExamExtractor()
    
    # Rutas de los PDFs
    pdf_questions = "/workspaces/per-tests/data/raw/questions/madrid-2025.pdf"
    pdf_answers = "/workspaces/per-tests/data/raw/answers/madrid-2025-resp.pdf"
    
    # Verificar que existen los PDFs
    if not os.path.exists(pdf_questions):
        print(f"❌ Error: No se encuentra {pdf_questions}")
        return
    if not os.path.exists(pdf_answers):
        print(f"❌ Error: No se encuentra {pdf_answers}")
        return
    
    # Extraer el examen de PER Madrid 2025 Código de Test 01
    exam_data = extractor.extract_exam(pdf_questions, PER_MADRID_2025_TEST_01)
    
    if not exam_data:
        print("❌ No se pudo extraer el examen")
        return
    
    # Generar nombre de archivo automáticamente
    output_path = extractor.generate_filename(PER_MADRID_2025_TEST_01, "/workspaces/per-tests/data/exams")
    extractor.save_to_yaml(exam_data, output_path)
    
    # Mostrar estadísticas
    print(f"\n{'='*60}")
    print(f"📊 ESTADÍSTICAS DEL EXAMEN EXTRAÍDO")
    print(f"{'='*60}")
    info = exam_data['exam_info']
    print(f"📋 Título: {info['title']}")
    print(f"🏷️  Subtítulo: {info['subtitle']}")
    print(f"🏛️  Comunidad: {info['community']}")
    print(f"📅 Año: {info['year']}")
    print(f"📢 Convocatoria: {info['call']}")
    print(f"🔢 Código de Test: {info['test_code']}")
    print(f"❓ Preguntas extraídas: {info['total_questions']}")
    print(f"🎯 Preguntas esperadas: {info['expected_questions']}")
    print(f"✅ Preguntas con respuesta: {info['questions_with_answers']}")
    print(f"📂 Categorías: {info['categories']}")
    print(f"💾 Archivo generado: {output_path}")
    
    print(f"\n📈 DISTRIBUCIÓN POR CATEGORÍA:")
    for cat_id, cat_data in exam_data['categories'].items():
        questions_with_answers = sum(1 for q in cat_data['questions'] if q['correct_answer'] is not None)
        print(f"  {cat_id:2d}. {cat_data['name']:<25}: {len(cat_data['questions']):2d} preguntas ({questions_with_answers} con respuesta)")

if __name__ == "__main__":
    main()
