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

# Distribución fija estándar PER por números de pregunta
PER_STANDARD_DISTRIBUTION = {
    1: [1, 2, 3, 4],                    # Nomenclatura náutica (4 preguntas)
    2: [5, 6],                          # Elementos de amarre y fondeo (2 preguntas)
    3: [7, 8, 9, 10],                   # Seguridad (4 preguntas)
    4: [11, 12],                        # Legislación (2 preguntas)
    5: [13, 14, 15, 16, 17],            # Balizamiento (5 preguntas)
    6: [18, 19, 20, 21, 22, 23, 24, 25, 26, 27],  # Reglamento (RIPA) (10 preguntas)
    7: [28, 29],                        # Maniobra y navegación (2 preguntas)
    8: [30, 31, 32],                    # Emergencias en la mar (3 preguntas)
    9: [33, 34, 35, 36],                # Meteorología (4 preguntas)
    10: [37, 38, 39, 40, 41],           # Teoría de la navegación (5 preguntas)
    11: [42, 43, 44, 45]                # Carta de navegación (4 preguntas)
}

# Mapeo inverso: número de pregunta -> categoría
QUESTION_TO_CATEGORY = {}
for category, questions in PER_STANDARD_DISTRIBUTION.items():
    for question_id in questions:
        QUESTION_TO_CATEGORY[question_id] = category

# Nota: Los patrones específicos han sido eliminados.
# Ahora se generan dinámicamente usando create_per_pattern() basándose en los parámetros.

def create_per_pattern(community: str, year: int, call: str, test_number: str, 
                      total_questions: int = 45) -> ExamPattern:
    """
    Función para crear patrones de examen PER dinámicamente.
    
    Args:
        community: Nombre de la comunidad autónoma (ej: "Madrid", "Barcelona", "Valencia")
        year: Año de realización (ej: 2025, 2024)
        call: Convocatoria (ej: "Ordinaria", "Extraordinaria", "Enero", "Junio")
        test_number: Número del test de 2 dígitos (ej: "01", "02", "03", "04", "05")
        total_questions: Número total de preguntas (por defecto 45)
    
    Returns:
        ExamPattern configurado para el examen especificado
    
    Ejemplo:
        # Para un examen de Valencia de junio 2024, test 02
        pattern = create_per_pattern("Valencia", 2024, "Junio", "02")
    """
    # Asegurar que el número del test tenga 2 dígitos
    test_number_formatted = test_number.zfill(2)
    
    # Generar el código de test en formato testXX
    test_code = f"test{test_number_formatted}"
    
    # Generar el subtítulo
    subtitle = f"Código de Test {test_number_formatted}"
    
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
# PER_VALENCIA_2024_JUNIO_TEST02 = create_per_pattern("Valencia", 2024, "Junio", "02")
# PER_BARCELONA_2023_EXTRAORDINARIA_TEST01 = create_per_pattern("Barcelona", 2023, "Extraordinaria", "01")

class ParametricExamExtractor:
    def __init__(self):
        self.questions = []
        self.answers = {}
    
    def validate_section_distribution(self, exam_section: str, pattern: ExamPattern) -> Dict[int, List[int]]:
        """
        Valida que las secciones detectadas en el PDF coincidan con la distribución estándar PER.
        
        Returns:
            Dict con la distribución detectada: {categoria: [lista_de_preguntas_encontradas]}
        """
        print("🔍 Validando distribución de secciones vs estándar PER...")
        
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
        
        # Encontrar todas las secciones de categorías en el texto
        detected_sections = {}
        lines = exam_section.split('\n')
        
        current_category = None
        current_questions = []
        
        for i, line in enumerate(lines):
            line_clean = line.strip().lower().rstrip('.')
            
            # Verificar si es un título de categoría
            if line_clean in category_title_map:
                # Guardar la categoría anterior si existe
                if current_category is not None and current_questions:
                    detected_sections[current_category] = current_questions.copy()
                
                current_category = category_title_map[line_clean]
                current_questions = []
                print(f"📍 Detectada sección: {current_category} - {PER_CATEGORIES[current_category]}")
                continue
            
            # Buscar preguntas numeradas
            question_match = re.match(r'^\s*(\d{1,2})\s+', line)
            if question_match and current_category is not None:
                question_num = int(question_match.group(1))
                if 1 <= question_num <= pattern.total_questions:
                    current_questions.append(question_num)
        
        # Guardar la última categoría
        if current_category is not None and current_questions:
            detected_sections[current_category] = current_questions.copy()
        
        # Validar contra la distribución estándar
        print("\n📊 Comparación secciones detectadas vs distribución estándar:")
        print("=" * 80)
        
        validation_warnings = []
        all_detected_questions = set()
        
        for category in range(1, 12):  # Categorías 1-11
            standard_questions = PER_STANDARD_DISTRIBUTION[category]
            detected_questions = detected_sections.get(category, [])
            category_name = PER_CATEGORIES[category]
            
            # Verificar si las preguntas detectadas coinciden con las estándar
            standard_set = set(standard_questions)
            detected_set = set(detected_questions)
            
            missing_in_section = standard_set - detected_set
            extra_in_section = detected_set - standard_set
            
            status = "✅" if standard_set == detected_set else "⚠️"
            
            print(f"{status} Cat {category:2d} - {category_name:25s}")
            print(f"     Estándar: {standard_questions}")
            print(f"     Detectado: {detected_questions}")
            
            if missing_in_section:
                print(f"     ❌ Faltan en sección: {sorted(missing_in_section)}")
                validation_warnings.append(f"Categoría {category}: faltan preguntas {sorted(missing_in_section)}")
            
            if extra_in_section:
                print(f"     ❌ Sobran en sección: {sorted(extra_in_section)}")
                validation_warnings.append(f"Categoría {category}: sobran preguntas {sorted(extra_in_section)}")
            
            all_detected_questions.update(detected_questions)
            print()
        
        # Verificar preguntas totales
        expected_total = set(range(1, pattern.total_questions + 1))
        missing_global = expected_total - all_detected_questions
        extra_global = all_detected_questions - expected_total
        
        if missing_global:
            print(f"🚨 Preguntas faltantes globalmente: {sorted(missing_global)}")
            validation_warnings.append(f"Faltan preguntas globalmente: {sorted(missing_global)}")
        
        if extra_global:
            print(f"🚨 Preguntas extra globalmente: {sorted(extra_global)}")
            validation_warnings.append(f"Preguntas extra globalmente: {sorted(extra_global)}")
        
        if validation_warnings:
            print("\n⚠️  ADVERTENCIAS DE VALIDACIÓN:")
            for warning in validation_warnings:
                print(f"   • {warning}")
        else:
            print("\n✅ Distribución de secciones VÁLIDA - coincide con estándar PER")
        
        return detected_sections
    
    def _is_legitimate_section_title(self, line: str, category_title_map: Dict[str, int], 
                                   previous_lines: List[str], next_lines: List[str]) -> bool:
        """
        Determina si una línea es realmente un título de sección o solo una palabra coincidente.
        
        Criterios para ser un título legítimo:
        1. La línea debe contener SOLO el nombre de la categoría (sin otros textos significativos)
        2. No debe estar claramente dentro de una opción de respuesta
        3. Debe haber indicios de que es un cambio de sección real
        """
        line_clean = line.strip().lower().rstrip('.')
        
        # Verificar que la línea coincida con un título de categoría
        if line_clean not in category_title_map:
            return False
        
        # Criterio 1: La línea debe ser PRINCIPALMENTE el título
        # Permitir títulos que son esencialmente solo el nombre de la categoría
        line_words = line.strip().split()
        expected_category_words = line_clean.split()
        
        # Si hay muchas palabras extra, es sospechoso
        if len(line_words) > len(expected_category_words) + 2:  # Permitir 2 palabras extra
            return False
        
        # Criterio 2: Verificar que NO esté claramente dentro de opciones de respuesta
        # Buscar evidencia clara de que estamos en opciones (múltiples opciones recientes)
        recent_options_count = 0
        for prev_line in previous_lines[-5:]:  # Revisar las últimas 5 líneas
            if re.search(r'^[a-d]\)', prev_line.strip(), re.IGNORECASE):
                recent_options_count += 1
        
        # Si hay 2 o más opciones recientes, probablemente estamos dentro de opciones
        if recent_options_count >= 2:
            return False
        
        # Criterio 3: Verificar si hay evidencia de fin de pregunta/opción anterior
        # Buscar patrones que sugieren que la pregunta anterior terminó
        has_completion_evidence = False
        
        if previous_lines:
            # Revisar las últimas líneas para ver si hay evidencia de fin de pregunta
            for i, prev_line in enumerate(previous_lines[-3:]):  # Últimas 3 líneas
                prev_stripped = prev_line.strip()
                
                # Evidencia fuerte de fin de pregunta/opción
                if (prev_stripped == '' or  # Línea vacía
                    prev_stripped.endswith('.') or  # Termina con punto
                    prev_stripped.endswith('?') or  # Pregunta completa
                    re.match(r'^\d{1,2}\s+', prev_stripped) or  # Inicio de nueva pregunta
                    re.search(r'^[a-d]\).*[.]$', prev_stripped, re.IGNORECASE)):  # Opción terminada
                    has_completion_evidence = True
                    break
        
        # Criterio 4: Si no hay evidencia clara de fin de pregunta, ser más permisivo
        # para títulos de sección que aparecen en posiciones lógicas
        
        # Si hemos encontrado evidencia de fin de pregunta, es muy probable que sea legítimo
        if has_completion_evidence:
            return True
        
        # Si no hay evidencia clara, verificar si es una sola línea aislada con el título exacto
        line_trimmed = line.strip().rstrip('.')
        if line_trimmed.lower() == line_clean:
            # Es exactamente el título de categoría, probablemente es legítimo
            # A menos que claramente esté dentro de una opción
            if previous_lines and len(previous_lines) > 0:
                last_line = previous_lines[-1].strip()
                # Si la línea anterior es parte de una opción incompleta, rechazar
                if (last_line and 
                    not last_line.endswith(('.', '?', ':', ';')) and
                    not re.match(r'^[a-d]\)', last_line, re.IGNORECASE)):
                    return False
            return True
        
        return False
    
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
        
    def extract_text_from_pdf(self, pdf_path: str, start_page: Optional[int] = None) -> str:
        """
        Extrae todo el texto del PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            start_page: Página desde la cual empezar la extracción (base 1). Si es None, extrae desde el principio.
        """
        print(f"📄 Extrayendo texto de {pdf_path}")
        if start_page:
            print(f"📖 Iniciando extracción desde la página {start_page}")
        
        doc = fitz.open(pdf_path)
        text = ""
        
        # Obtener información del documento antes de procesarlo
        total_pages = len(doc)
        
        # Determinar el rango de páginas
        start_idx = (start_page - 1) if start_page else 0
        start_idx = max(0, start_idx)  # Asegurar que no sea negativo
        
        # Validar que la página de inicio no exceda el total de páginas
        if start_idx >= total_pages:
            doc.close()
            raise ValueError(f"La página de inicio {start_page} excede el total de páginas del documento ({total_pages})")
        
        for page_num in range(start_idx, total_pages):
            page = doc[page_num]
            text += page.get_text() + "\n"
        
        doc.close()
        print(f"📊 Texto extraído desde página {start_idx + 1} hasta {total_pages}")
        return text
    
    def find_exam_section(self, text: str, pattern: ExamPattern, start_page_specified: bool = False) -> Tuple[str, int, int]:
        """
        Encuentra la sección del examen específico en el texto.
        Retorna: (texto_seccion, posicion_inicio, posicion_fin)
        
        Args:
            text: Texto completo del PDF
            pattern: Patrón del examen a buscar
            start_page_specified: Si se especificó una página de inicio, busca de forma más flexible
        """
        # Si se especificó una página de inicio, intentar búsqueda más flexible
        if start_page_specified:
            print(f"🔍 Búsqueda flexible activada (página de inicio especificada)")
            
            # Intentar encontrar solo el subtítulo (código de test)
            subtitle_pattern = rf"{re.escape(pattern.subtitle)}"
            subtitle_match = re.search(subtitle_pattern, text, re.IGNORECASE)
            
            if subtitle_match:
                print(f"✅ Encontrado subtítulo '{pattern.subtitle}' en posición: {subtitle_match.start()}")
                start_pos = subtitle_match.start()
                # Buscar hacia atrás para incluir posible título previo
                search_start = max(0, start_pos - 500)
                exam_text_from_start = text[search_start:]
                
                # Buscar el final del examen
                end_pos = self._find_exam_end(exam_text_from_start, pattern)
                exam_section = exam_text_from_start[:end_pos]
                
                print(f"📊 Sección del examen extraída (modo flexible): {len(exam_section)} caracteres")
                return exam_section, search_start, search_start + end_pos
            
            # Si no encuentra el subtítulo, buscar patrones de pregunta directamente
            print(f"🔍 Buscando patrones de pregunta directamente...")
            question_pattern = r'\n\s*\d+\s+[¿A-ZÁÉÍÓÚÑ]'  # Incluir preguntas que empiezan con ¿
            question_matches = list(re.finditer(question_pattern, text))
            
            if question_matches:
                print(f"✅ Encontradas {len(question_matches)} posibles preguntas")
                
                # Buscar el inicio real de las preguntas
                # Priorizar preguntas que empiecen desde el número 1
                start_pos = question_matches[0].start()
                for match in question_matches:
                    match_text = text[match.start():match.start()+50]
                    if re.search(r'\b1\s+[¿A-ZÁÉÍÓÚÑ]', match_text):
                        start_pos = match.start()
                        print(f"✅ Encontrada pregunta 1 en posición: {start_pos}")
                        break
                
                # Tomar una sección generosa para capturar todas las preguntas
                end_pos = len(text)
                
                # Buscar el final basándose en el límite de 45 preguntas
                for i, match in enumerate(question_matches):
                    match_text = text[match.start():match.start()+50]
                    # Buscar el número de pregunta
                    question_num_match = re.search(r'\b(\d+)\s+[¿A-ZÁÉÍÓÚÑ]', match_text)
                    if question_num_match:
                        question_num = int(question_num_match.group(1))
                        if question_num == pattern.total_questions:  # Pregunta 45 para PER
                            # Buscar el final de esta pregunta (hasta la siguiente pregunta o final)
                            if i + 1 < len(question_matches):
                                end_pos = question_matches[i + 1].start()
                                print(f"✅ Final del test detectado: pregunta {question_num} termina en posición: {end_pos}")
                            else:
                                # Es la última pregunta encontrada, tomar una sección generosa
                                end_pos = min(len(text), match.start() + 2000)
                                print(f"✅ Final del test detectado: pregunta {question_num} (última detectada)")
                            break
                        elif question_num > pattern.total_questions:
                            # Si encontramos una pregunta con número mayor, el test anterior terminó
                            end_pos = match.start()
                            print(f"✅ Final del test detectado: pregunta {question_num} excede límite, terminando en posición: {end_pos}")
                            break
                
                exam_section = text[start_pos:end_pos]
                print(f"📊 Sección del examen extraída (modo pregunta directa): {len(exam_section)} caracteres")
                return exam_section, start_pos, end_pos
        
        # Búsqueda normal (existente)
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
        end_pos = self._find_exam_end(exam_text_from_start, pattern)
        
        exam_section = exam_text_from_start[:end_pos]
        print(f"📊 Sección del examen extraída: {len(exam_section)} caracteres")
        
        return exam_section, start_pos, start_pos + end_pos
    
    def _find_exam_end(self, exam_text_from_start: str, pattern: ExamPattern) -> int:
        """
        Encuentra el final de la sección del examen.
        """
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
        
        return end_pos
    
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
            
            # Verificar si la línea es un título de categoría LEGÍTIMO
            line_lower = line.lower().rstrip('.')
            if line_lower in category_title_map:
                # Validar que sea realmente un título de sección
                previous_lines = lines[max(0, i-5):i]  # 5 líneas anteriores
                next_lines = lines[i+1:i+6]  # 5 líneas siguientes
                
                if self._is_legitimate_section_title(line, category_title_map, previous_lines, next_lines):
                    current_category = category_title_map[line_lower]
                    current_category_name = pattern.categories[current_category]
                    print(f"✅ Título de sección LEGÍTIMO: {current_category} - {current_category_name}")
                    i += 1
                    continue
                else:
                    print(f"🚫 IGNORADO falso título de sección: '{line}' (parte de opción de respuesta)")
            
            # Verificar si la línea es una pregunta numerada con texto en la misma línea
            question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', line)
            if question_match:
                question_num = int(question_match.group(1))
                question_text_start = question_match.group(2)
                
                # Solo procesar preguntas en el rango válido
                if question_num < 1 or question_num > pattern.total_questions:
                    # Si encontramos una pregunta mayor al límite, terminamos el parsing
                    if question_num > pattern.total_questions:
                        print(f"🛑 Terminando extracción: encontrada pregunta {question_num} que excede el límite de {pattern.total_questions}")
                        break
                    i += 1
                    continue
                # Verificar que NO sea solo una referencia a regla del RIPA (sin ser una pregunta real)
                # Las preguntas reales suelen empezar con palabras como "Según", "Conforme", "De acuerdo", etc.
                is_ripa_reference_only = (
                    # Solo filtramos si es una referencia sin contexto de pregunta
                    re.match(r'^\s*del\s+RIPA\s*$', question_text_start, re.IGNORECASE) or
                    re.match(r'^\s*de\s+la\s+Regla\s+\d+\s*$', question_text_start, re.IGNORECASE) or
                    re.match(r'^\s*Regla\s+\d+\s*$', question_text_start, re.IGNORECASE)
                )
                if is_ripa_reference_only:
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
                        # Solo filtrar referencias de RIPA que no son preguntas reales
                        is_ripa_reference_only = (
                            re.match(r'^\s*del\s+RIPA\s*$', question_text_start, re.IGNORECASE) or
                            re.match(r'^\s*de\s+la\s+Regla\s+\d+\s*$', question_text_start, re.IGNORECASE) or
                            re.match(r'^\s*Regla\s+\d+\s*$', question_text_start, re.IGNORECASE)
                        )
                        if is_valid_question_num and not is_ripa_reference_only:
                            break
                    
                    # Verificar si es un falso título de categoría
                    next_line_lower = next_line.lower().rstrip('.')
                    if next_line_lower in category_title_map:
                        # Validar si es realmente un título de sección
                        previous_lines_for_validation = lines[max(0, i-5):i]
                        next_lines_for_validation = lines[i+1:i+6]
                        
                        if self._is_legitimate_section_title(next_line, category_title_map, 
                                                           previous_lines_for_validation, 
                                                           next_lines_for_validation):
                            # Es un título legítimo, parar aquí
                            break
                        else:
                            # Es un falso título, continuar agregando a la pregunta
                            print(f"🚫 IGNORADO falso título en pregunta {question_num}: '{next_line}'")
                            if next_line:
                                question_content += '\n' + next_line
                            i += 1
                            continue
                    
                    # Es contenido normal de la pregunta
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
                    # Si encontramos una pregunta mayor al límite, terminamos el parsing
                    if question_num > pattern.total_questions:
                        print(f"🛑 Terminando extracción: encontrada pregunta {question_num} que excede el límite de {pattern.total_questions}")
                        break
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
    
    def _parse_single_question(self, question_num: int, content: str, detected_category: int, detected_category_name: str) -> Dict:
        """
        Procesa una pregunta individual y extrae su información.
        Implementa doble validación: sección detectada vs distribución estándar PER.
        """
        # PASO 1: Determinar la categoría estándar según el número de pregunta
        standard_category = QUESTION_TO_CATEGORY.get(question_num)
        if standard_category is None:
            print(f"⚠️  Pregunta {question_num} fuera del rango estándar (1-45)")
            return None
        
        standard_category_name = PER_CATEGORIES[standard_category]
        
        # PASO 2: Comparar categoría detectada vs estándar
        if detected_category != standard_category:
            print(f"🔄 Pregunta {question_num}: CORRECCIÓN de categoría")
            print(f"   📍 Detectada en sección: {detected_category} - {detected_category_name}")
            print(f"   ✅ Corrigiendo a estándar: {standard_category} - {standard_category_name}")
            
            # Usar la categoría estándar
            final_category = standard_category
            final_category_name = standard_category_name
        else:
            # Las categorías coinciden
            print(f"✅ Pregunta {question_num}: categoría {standard_category} - {standard_category_name} (coincide)")
            final_category = standard_category
            final_category_name = standard_category_name
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
                option_line_count = 0  # Contador para evitar opciones infinitas
                max_option_lines = 15  # Límite máximo de líneas por opción (para casos complejos)
                
                while i < len(lines) and option_line_count < max_option_lines:
                    next_line = lines[i]
                    option_line_count += 1
                    
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
                    # IMPORTANTE: No confundir sub-elementos i), ii), iii) con números de pregunta
                    potential_question_match = re.match(r'^\s*(\d{1,2})\s+([^\d\s].*)', next_line)
                    if potential_question_match:
                        potential_num = int(potential_question_match.group(1))
                        if 1 <= potential_num <= 45:  # Rango válido de preguntas
                            break
                    
                    # Verificar si es un sub-elemento de la opción (i), ii), iii), etc.)
                    # Estos deben ser incluidos en la opción actual
                    is_sub_element = re.match(r'^\s*[ivx]+\)\s+', next_line, re.IGNORECASE)
                    
                    # Es continuación de la opción actual
                    if next_line.strip():  # Solo agregar si no está vacía
                        if is_sub_element:
                            # Para sub-elementos, agregar con un separado visual
                            option_text += '; ' + next_line.strip()
                        else:
                            # Para texto normal, agregar con espacio
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
            'category': final_category,
            'category_name': final_category_name
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
    
    def extract_exam(self, questions_pdf: str, pattern: ExamPattern, start_page: Optional[int] = None) -> Dict:
        """
        Extrae un examen completo usando el patrón especificado.
        Solo extrae las preguntas, sin respuestas.
        
        Args:
            questions_pdf: Ruta al archivo PDF con las preguntas
            pattern: Patrón del examen a extraer
            start_page: Página desde la cual empezar la búsqueda (base 1). Útil cuando la cabecera está en imagen.
        """
        print(f"🚢 Extrayendo examen: {pattern.title} - {pattern.subtitle}")
        if start_page:
            print(f"📖 Iniciando búsqueda desde la página {start_page}")
        
        # Extraer preguntas del PDF
        questions_text = self.extract_text_from_pdf(questions_pdf, start_page)
        exam_section, _, _ = self.find_exam_section(questions_text, pattern, start_page is not None)
        
        if not exam_section:
            print("❌ No se pudo encontrar la sección del examen")
            if start_page:
                print(f"💡 Verifica que el examen {pattern.subtitle} esté presente desde la página {start_page}")
            else:
                print(f"💡 Si la cabecera del examen está en una imagen, prueba con --start-page N")
            return {}
        
        # VALIDACIÓN: Verificar distribución de secciones antes del parsing
        print("\n" + "="*80)
        print("🔍 PASO 1: VALIDACIÓN DE DISTRIBUCIÓN DE SECCIONES")
        print("="*80)
        detected_distribution = self.validate_section_distribution(exam_section, pattern)
        
        print("\n" + "="*80)
        print("🔧 PASO 2: EXTRACCIÓN DE PREGUNTAS CON CORRECCIÓN AUTOMÁTICA")
        print("="*80)
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
                        
                        # Si no se encontró categoría en las líneas previas, mantener la categoría por defecto
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
  %(prog)s --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 01
  %(prog)s --input-file /ruta/completa/examen.pdf --test-code 05 --output-dir mi_directorio --verbose
  %(prog)s --input-file examen.pdf --test-code 03 --start-page 5
  
Uso del parámetro --start-page:
  Cuando la cabecera del examen (título + código de test) está en una imagen
  y no es detectada por OCR, usa --start-page para indicar desde qué página
  empezar la búsqueda del contenido del examen.
  
  Ejemplo: Si el Test 03 empieza en la página 7:
  %(prog)s --input-file examen.pdf --test-code 03 --start-page 7
  
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
                       choices=['01', '02', '03', '04', '05'], 
                       help='Número del test a extraer. Disponibles: 01, 02, 03, 04, 05')
    parser.add_argument('--output-dir', default='data/exams', 
                       help='Directorio donde guardar el archivo YAML (default: data/exams)')
    parser.add_argument('--start-page', type=int, 
                       help='Página desde la cual empezar la búsqueda del examen (base 1). Útil cuando la cabecera está en imagen y no es detectada por OCR')
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
        if args.start_page:
            print(f"📖 Página inicial: {args.start_page}")
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
        exam_data = extractor.extract_exam(args.input_file, pattern, args.start_page)
        
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
