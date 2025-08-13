#!/usr/bin/env python3
"""
Extractor de exámenes PER para la región de Murcia desde PDFs
Especializado para el formato específico de los exámenes de Murcia

Características específicas de Murcia:
- Formato consistente en todos los exámenes
- Solo tipo Test 01 
- Preguntas numeradas: "1.- Texto pregunta" o "1. Texto pregunta" (formato variable)
- Opciones: "a) texto", "b) texto", etc.
- Respuestas correctas marcadas con texto subrayado
- Secciones marcadas en recuadros: "Unidad teórica N: NOMBRE"
"""

import fitz  # PyMuPDF
import yaml
import re
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MurciaExamPattern:
    """Patrón para identificar un examen de Murcia"""
    
    title: str = "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"
    community: str = "Murcia"
    total_questions: int = 45
    test_code: str = "test01"  # Siempre es test01 para Murcia
    
    def __init__(self, year: int, call: str):
        self.year = year
        self.call = call


# Categorías oficiales de PER (mismo formato que Madrid)
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
    11: "Carta de navegación",
}

# Distribución fija estándar PER por números de pregunta (específica para Murcia)
PER_MURCIA_DISTRIBUTION = {
    1: [1, 2, 3, 4],          # Nomenclatura náutica (4 preguntas)
    2: [5, 6],                # Elementos de amarre y fondeo (2 preguntas)
    3: [7, 8, 9, 10],         # Seguridad (4 preguntas)
    4: [11, 12],              # Legislación (2 preguntas)
    5: [13, 14, 15, 16, 17],  # Balizamiento (5 preguntas)
    6: [18, 19, 20, 21, 22, 23, 24, 25, 26, 27],  # Reglamento (RIPA) (10 preguntas)
    7: [28, 29],              # Maniobra (2 preguntas)
    8: [30, 31, 32],          # Emergencias en el mar (3 preguntas)
    9: [33, 34, 35, 36],      # Meteorología (4 preguntas)
    10: [37, 38, 39, 40, 41], # Teoría de navegación (5 preguntas)
    11: [42, 43, 44, 45],     # Cartas de navegación (4 preguntas)
}

# Mapeo inverso: número de pregunta -> categoría
QUESTION_TO_CATEGORY = {}
for category, questions in PER_MURCIA_DISTRIBUTION.items():
    for question_id in questions:
        QUESTION_TO_CATEGORY[question_id] = category

# Títulos de sección esperados en los PDFs de Murcia
MURCIA_SECTION_TITLES = [
    "Unidad teórica 1: NOMENCLATURA NÁUTICA",
    "Unidad teórica 2: ELEMENTOS DE AMARRE Y FONDEO", 
    "Unidad teórica 3: SEGURIDAD",
    "Unidad teórica 4: LEGISLACIÓN",
    "Unidad teórica 5: BALIZAMIENTO",
    "Unidad teórica 6: REGLAMENTO (RIPA)",
    "Unidad teórica 7: MANIOBRA",
    "Unidad teórica 8: EMERGENCIAS EN EL MAR",
    "Unidad teórica 9: METEOROLOGÍA",
    "Unidad teórica 10: TEORÍA DE NAVEGACIÓN",
    "Unidad teórica 11: CARTAS DE NAVEGACIÓN",
]


class MurciaExamExtractor:
    def __init__(self):
        self.questions = []
        self.errors = []
        self.warnings = []

    def log_error(self, message: str):
        """Registra un error para mostrar al final"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str):
        """Registra una advertencia para mostrar al final"""
        self.warnings.append(message)
        print(f"⚠️ WARNING: {message}")

    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extrae todo el texto del PDF de forma optimizada.
        Limpia cabeceras y pies de página específicos de Murcia.
        """
        print(f"📄 Extrayendo texto de {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Normalizar caracteres problemáticos antes de procesar
                page_text = self._normalize_text_characters(page_text)
                
                # Limpiar cabeceras y pies de página específicos de Murcia
                lines = page_text.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    line_clean = line.strip()
                    # Filtrar cabeceras "Tipo 1" y pies de página "P.E.R. - Tipo 1"
                    if (line_clean == "Tipo 1" or 
                        line_clean.startswith("P.E.R. - Tipo 1") or
                        re.match(r'^\d+\s*/\s*\d+$', line_clean)):  # Números de página como "1 / 10"
                        continue
                    cleaned_lines.append(line)
                
                text += '\n'.join(cleaned_lines) + "\n"
            
            doc.close()
            print(f"📊 Texto extraído: {len(text)} caracteres")
            return text
        except Exception as e:
            self.log_error(f"Error extrayendo texto del PDF: {str(e)}")
            return ""
    
    def _normalize_text_characters(self, text: str) -> str:
        """
        Normaliza caracteres problemáticos que PyMuPDF puede extraer incorrectamente.
        """
        # Diccionario de reemplazos para caracteres problemáticos
        replacements = {
            # Comillas problemáticas específicas de PDFs de Murcia
            # En los PDFs de Murcia, las comillas aparecen como < y =
            # Ejemplo: <El capitán de todo buque...= 
            # Se reemplazan por comillas estándar
            
            # Espacios problemáticos
            '\u00a0': ' ',  # Espacio no rompible a espacio normal
            '\u2009': ' ',  # Espacio fino a espacio normal
            '\u2007': ' ',  # Espacio de cifra a espacio normal
        }
        
        # Aplicar reemplazos básicos primero
        normalized_text = text
        for old_char, new_char in replacements.items():
            normalized_text = normalized_text.replace(old_char, new_char)
        
        # Manejo específico para comillas de Murcia: < al inicio de citas y = al final
        # Patrón: <texto contenido= se convierte en "texto contenido"
        # Solo aplicar si hay un patrón claro de cita
        quote_pattern = r'<([^<>=]+)='
        normalized_text = re.sub(quote_pattern, r'"\1"', normalized_text)
        
        return normalized_text

    def find_exam_start(self, text: str) -> int:
        """
        Encuentra el inicio del examen, ignorando las instrucciones iniciales.
        Busca "EXAMEN TIPO 1" seguido de la primera sección o pregunta.
        """
        # Buscar primero el marcador "EXAMEN TIPO 1"
        exam_type_patterns = [
            r"EXAMEN\s+TIPO\s+1",
            r"Unidad teórica 1:\s*NOMENCLATURA NÁUTICA",
            r"1\s*:\s*NOMENCLATURA NÁUTICA",  # Variación abreviada
        ]
        
        for pattern in exam_type_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"✅ Inicio del examen encontrado: '{match.group()}' en posición: {match.start()}")
                return match.start()
        
        # Si no se encuentra ningún patrón específico, buscar la primera pregunta
        self.log_warning("No se encontró el inicio del examen con el patrón esperado")
        first_question = re.search(r'1\.-\s', text)
        if first_question:
            print(f"✅ Primera pregunta encontrada en posición: {first_question.start()}")
            return max(0, first_question.start() - 100)  # Incluir un poco de contexto previo
        return 0

    def find_exam_end(self, text: str, start_pos: int) -> int:
        """
        Encuentra el final del examen.
        Se busca principalmente "ESPACIO PARA OPERACIONES" o se usa el final del archivo.
        """
        exam_text = text[start_pos:]
        
        # Buscar únicamente patrones claros de final de examen
        end_patterns = [
            r"ESPACIO PARA OPERACIONES",
            r"HOJA DE OPERACIONES",
        ]
        
        end_pos = len(exam_text)  # Por defecto, usar todo el texto
        
        # Buscar patrones de final
        for pattern in end_patterns:
            match = re.search(pattern, exam_text, re.IGNORECASE | re.DOTALL)
            if match:
                end_pos = match.start()
                print(f"✅ Final del examen encontrado: {pattern} en posición {start_pos + end_pos}")
                break
        
        # Si no se encontró ningún patrón, usar todo el texto
        if end_pos == len(exam_text):
            print(f"✅ Final del examen: usando final del archivo en posición {start_pos + end_pos}")
            
        return start_pos + end_pos

    def parse_questions_from_text(self, text: str, pattern: MurciaExamPattern) -> List[Dict]:
        """
        Extrae las preguntas del texto del examen de Murcia.
        Formato esperado: "1.- Pregunta texto..."
        Opciones: "a) opción", "b) opción", etc.
        Respuestas correctas pueden estar subrayadas en el texto.
        """
        questions = []
        
        # Encontrar la sección del examen
        start_pos = self.find_exam_start(text)
        end_pos = self.find_exam_end(text, start_pos)
        exam_section = text[start_pos:end_pos]
        
        print(f"📊 Procesando sección del examen: {len(exam_section)} caracteres")
        
        # Buscar todas las preguntas con su posición
        # MEJORADO: Manejo de formatos mixtos en el mismo examen
        question_matches = []
        
        # Probar diferentes patrones en orden de especificidad
        patterns = [
            r'(\d+)\.-\s+',    # Formato original: "1.- " (con espacios)
            r'(\d+)\.\s+',     # Formato nuevo: "1. " (con espacios)
            r'(\d+)\.-',       # Formato original sin espacios: "1.-"
            r'(\d+)\.',        # Formato nuevo sin espacios: "1."
        ]
        
        # Primero, intentar con un solo patrón
        best_single_pattern = None
        max_single_matches = 0
        best_quality_score = 0
        
        for pattern in patterns:
            temp_matches = []
            seen_questions = set()  # Para evitar duplicados
            
            for match in re.finditer(pattern, exam_section):
                q_num = int(match.group(1))
                if 1 <= q_num <= 45 and q_num not in seen_questions:  # Evitar duplicados
                    start_pos = match.start()
                    before_match = exam_section[max(0, start_pos-10):start_pos]  # Usar más contexto
                    
                    # Verificar que esté al inicio de línea (incluyendo espacios)
                    if before_match.endswith('\n') or start_pos == 0 or '\n' in before_match[-10:]:
                        temp_matches.append((q_num, match.start(), match.end()))
                        seen_questions.add(q_num)  # Marcar como vista
            
            # Calcular calidad del patrón
            question_numbers = [q[0] for q in temp_matches]
            unique_questions = set(question_numbers)
            consecutive_from_1 = len([q for q in range(1, 46) if q in unique_questions])
            
            # Priorizar calidad sobre cantidad
            quality_score = consecutive_from_1 * 1000 + len(temp_matches)  # Priorizar consecutividad
            
            # Preferir patrones que den exactamente 45 preguntas únicas
            if len(unique_questions) == 45:
                quality_score += 10000  # Bonus por exactitud
                
            if quality_score > best_quality_score or (quality_score == best_quality_score and len(temp_matches) > max_single_matches):
                max_single_matches = len(temp_matches)
                best_single_pattern = pattern
                question_matches = temp_matches
                best_quality_score = quality_score
        
        print(f"🎯 Mejor patrón individual '{best_single_pattern}' encontró {len(question_matches)} preguntas")
        
        # Si no tenemos todas las preguntas (menos de 43), intentar combinar patrones
        if len(question_matches) < 43:
            print(f"⚠️ Solo {len(question_matches)} preguntas con un patrón, intentando combinación...")
            
            # Combinar todos los patrones válidos
            combined_matches = {}  # usar dict para evitar duplicados
            patterns_used = []
            
            for pattern in patterns:
                pattern_matches = []
                for match in re.finditer(pattern, exam_section):
                    q_num = int(match.group(1))
                    if 1 <= q_num <= 45:
                        start_pos = match.start()
                        before_match = exam_section[max(0, start_pos-10):start_pos]  # Usar más contexto
                        
                        # Verificar que esté al inicio de línea (incluyendo espacios)
                        if before_match.endswith('\n') or start_pos == 0 or '\n' in before_match[-10:]:
                            # Solo agregar si no existe ya una pregunta con este número
                            if q_num not in combined_matches:
                                combined_matches[q_num] = (q_num, match.start(), match.end())
                                pattern_matches.append(q_num)
                
                if pattern_matches:
                    patterns_used.append(f"{pattern} ({len(pattern_matches)} preguntas)")
            
            if len(combined_matches) > len(question_matches):
                question_matches = list(combined_matches.values())
                print(f"✅ Combinación de patrones encontró {len(question_matches)} preguntas")
                print(f"📋 Patrones usados: {', '.join(patterns_used)}")
                pattern_used = "combinado"
            else:
                pattern_used = best_single_pattern
        else:
            pattern_used = best_single_pattern
        
        question_matches.sort()  # Ordenar por número de pregunta
        print(f"🔍 Encontradas {len(question_matches)} preguntas numeradas válidas")
        
        # Extraer cada pregunta individualmente
        for i, (question_num, start_pos_rel, end_pos_rel) in enumerate(question_matches):
            # Determinar el final de esta pregunta (inicio de la siguiente o final del texto)
            if i + 1 < len(question_matches):
                next_start = question_matches[i + 1][1]
                question_content = exam_section[end_pos_rel:next_start].strip()
            else:
                question_content = exam_section[end_pos_rel:].strip()
            
            # Parsear la pregunta individual
            question_data = self._parse_single_question(question_num, question_content, pattern)
                    
            if question_data:
                if self._validate_question(question_data):
                    questions.append(question_data)
                else:
                    self.log_error(f"Pregunta {question_num} no pasó la validación")
        
        # Ordenar por ID
        questions.sort(key=lambda x: x["id"])
        
        print(f"✅ Extraídas {len(questions)} preguntas válidas")
        
        # Verificar preguntas faltantes
        extracted_ids = {q["id"] for q in questions}
        expected_ids = set(range(1, 46))
        missing_ids = expected_ids - extracted_ids
        
        if missing_ids:
            self.log_warning(f"Preguntas faltantes: {sorted(missing_ids)}")
        
        return questions

    def _parse_single_question(self, question_num: int, question_content: str, pattern: MurciaExamPattern) -> Optional[Dict]:
        """
        Parsea una pregunta individual del formato de Murcia.
        Extrae pregunta, opciones y detecta la respuesta correcta por subrayado.
        """
        try:
            # Determinar la categoría basándose en el número de pregunta
            category = QUESTION_TO_CATEGORY.get(question_num, 1)
            category_name = PER_CATEGORIES[category]
            
            # Separar el enunciado de las opciones usando el patrón "a) "
            # Usar un patrón más flexible que capture opciones con diferentes espaciados
            parts = re.split(r'\n\s*([a-d])\)\s*', question_content)
            
            if len(parts) < 2:
                self.log_error(f"Pregunta {question_num}: No se pudieron separar las opciones")
                return None
                
            # El enunciado es la primera parte
            question_text = parts[0].strip()
            question_text = self._clean_question_text(question_text)
            
            # Procesar opciones (partes[1], partes[2], partes[3], partes[4], etc.)
            options = {}
            correct_answer = None
            
            # Las opciones vienen en pares: [letra, texto, letra, texto, ...]
            for i in range(1, len(parts), 2):
                if i + 1 >= len(parts):
                    break
                    
                letter = parts[i].lower()
                option_text = parts[i + 1].strip()
                
                # MEJORADO: Solo cortar texto si estamos en la opción 'd' y encontramos REALMENTE inicio de siguiente pregunta
                # Ser muy estricto para evitar cortar opciones que solo contengan números
                if letter == 'd':  # Solo verificar corte en la última opción
                    # Usar el patrón exacto que se está usando para este examen
                    pattern_to_use = pattern.pattern if hasattr(pattern, 'pattern') else r'(\d+)\.?\s*-?\s*'
                    next_question_match = re.search(pattern_to_use, option_text)
                    
                    if next_question_match:
                        next_num = int(next_question_match.group(1))
                        # Solo cortar si es un número de pregunta válido y exactamente la siguiente esperada
                        if 1 <= next_num <= 45 and next_num == question_num + 1:
                            # Verificar que REALMENTE parece inicio de pregunta (más estricto)
                            match_start = next_question_match.start()
                            
                            # El patrón debe estar al inicio de una nueva línea con espacios opcionalmente
                            text_before_pattern = option_text[:match_start]
                            lines_before = text_before_pattern.split('\n')
                            
                            # Si hay un salto de línea antes del patrón, es probable que sea nueva pregunta
                            if '\n' in text_before_pattern and (len(lines_before[-1].strip()) == 0 or match_start < 10):
                                # Cortar el texto antes del siguiente número de pregunta
                                cut_pos = next_question_match.start()
                                option_text = option_text[:cut_pos].strip()
                                self.log_warning(f"Pregunta {question_num} opción {letter}: cortado texto que incluía siguiente pregunta {next_num}")
                            else:
                                # El número está en medio del texto de la opción, no cortar
                                pass
                
                # Detectar respuesta correcta por subrayado u otros marcadores
                if self._is_correct_answer(option_text):
                    correct_answer = letter
                    option_text = self._clean_correct_answer_text(option_text)
                
                # Limpiar el texto de la opción (esto ahora incluye filtrado de títulos de sección)
                option_text = self._clean_option_text(option_text)
                options[letter] = option_text
            
            # Verificar que tenemos las 4 opciones esperadas
            expected_options = {'a', 'b', 'c', 'd'}
            missing_options = expected_options - set(options.keys())
            if missing_options:
                self.log_warning(f"Pregunta {question_num}: faltan opciones {missing_options}")
                # Completar con texto vacío
                for letter in missing_options:
                    options[letter] = ""
            
            return {
                "id": question_num,
                "question": question_text,
                "options": options,
                "category": category,
                "category_name": category_name,
                "correct_answer": correct_answer,
            }
            
        except Exception as e:
            self.log_error(f"Error procesando pregunta {question_num}: {str(e)}")
            return None

    def _clean_question_text(self, text: str) -> str:
        """
        Limpia el texto de la pregunta removiendo títulos de sección y otros elementos no deseados.
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Filtrar títulos de sección explícitos (pueden aparecer mezclados)
            if re.match(r'Unidad teórica \d+:', line, re.IGNORECASE):
                continue
                
            # MEJORADO: Filtrar líneas que son SOLO nombres de sección (títulos standalone)
            # Pero NO filtrar si la línea contiene texto adicional de pregunta
            section_names = ['NOMENCLATURA NÁUTICA', 'ELEMENTOS DE AMARRE', 'SEGURIDAD', 
                           'LEGISLACIÓN', 'BALIZAMIENTO', 'RIPA', 'MANIOBRA', 
                           'EMERGENCIAS', 'METEOROLOGÍA', 'NAVEGACIÓN']
            
            # Solo filtrar si la línea es EXACTAMENTE un nombre de sección o muy similar
            # No filtrar si contiene texto adicional de pregunta
            is_section_title_only = False
            for name in section_names:
                # Verificar si es solo el nombre de sección (con tolerancia a espacios/puntuación)
                if re.match(rf'^\s*{re.escape(name)}\s*[.:]?\s*$', line.upper()):
                    is_section_title_only = True
                    break
            
            if is_section_title_only:
                continue
                
            # Filtrar líneas vacías
            if not line:
                continue
                
            cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()

    def _clean_option_text(self, text: str) -> str:
        """
        Limpia el texto de una opción, removiendo saltos de línea innecesarios
        y títulos de sección que se hayan colado.
        """
        # Reemplazar saltos de línea múltiples con espacio
        text = re.sub(r'\n\s*\n', ' ', text)
        # Reemplazar saltos de línea simples con espacio, excepto cuando parecen listas
        text = re.sub(r'\n(?!\s*[-•*\d])', ' ', text)
        
        # NUEVO: Detectar y remover títulos de sección que se han colado
        # Patrón para títulos de sección: "Unidad teórica N: NOMBRE"
        section_pattern = r'\s*Unidad teórica \d+\s*:\s*[A-ZÁÉÍÓÚÑ\s]+(?:\([^)]*\))?\s*$'
        text = re.sub(section_pattern, '', text, flags=re.IGNORECASE)
        
        # También remover patrones más específicos que aparecen al final de opciones
        cleanup_patterns = [
            r'\s*Unidad teórica \d+\s*:\s*.*$',  # Cualquier título de sección al final
            r'\s*ELEMENTOS DE AMARRE Y FONDEO\s*$',
            r'\s*SEGURIDAD\s*$', 
            r'\s*LEGISLACIÓN\s*$',
            r'\s*BALIZAMIENTO\s*$',
            r'\s*REGLAMENTO \(RIPA\)\s*$',
            r'\s*MANIOBRA\s*$',
            r'\s*EMERGENCIAS EN EL MAR\s*$',
            r'\s*METEOROLOGÍA\s*$',
            r'\s*TEORÍA DE NAVEGACIÓN\s*$',
            r'\s*CARTA DE NAVEGACIÓN\s*$',
            r'\s*NOMENCLATURA NÁUTICA\s*$',
        ]
        
        for pattern in cleanup_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Limpiar espacios múltiples y puntos al final que puedan haber quedado
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Si después de limpiar queda solo un punto, removerlo
        if text == '.':
            text = ''
            
        return text

    def _is_correct_answer(self, option_text: str) -> bool:
        """
        Detecta si el texto de la opción corresponde a la respuesta correcta.
        En PDFs de Murcia, las respuestas correctas pueden estar subrayadas.
        """
        # Buscar marcadores comunes de subrayado en PDFs
        underline_indicators = [
            '\u0332',  # Caracter Unicode de subrayado
            '___',     # Subrayado con guiones bajos
            '__',      # Subrayado doble
        ]
        
        for indicator in underline_indicators:
            if indicator in option_text:
                return True
        
        # Buscar patrones de texto con formato especial (si los hay)
        # Esto puede necesitar ajuste según cómo aparezca el subrayado en los PDFs específicos
        
        return False

    def _clean_correct_answer_text(self, text: str) -> str:
        """
        Remueve los marcadores de respuesta correcta del texto.
        """
        # Remover marcadores de subrayado
        text = text.replace('\u0332', '')
        text = text.replace('___', '')
        text = text.replace('__', '')
        
        return text.strip()

    def _validate_question(self, question_data: Dict) -> bool:
        """
        Valida si una pregunta extraída es válida y completa.
        No inventa datos, solo valida lo extraído.
        """
        if not question_data:
            return False
            
        question_id = question_data.get("id")
        question_text = question_data.get("question", "").strip()
        options = question_data.get("options", {})
        
        # Validar longitud mínima del texto de pregunta
        if len(question_text) < 10:
            self.log_error(f"Pregunta {question_id}: texto demasiado corto: '{question_text}'")
            return False
            
        # Validar que tenga las 4 opciones
        expected_options = {"a", "b", "c", "d"}
        if not expected_options.issubset(set(options.keys())):
            missing = expected_options - set(options.keys())
            self.log_error(f"Pregunta {question_id}: faltan opciones {missing}")
            return False
        
        # Validar que las opciones tengan contenido mínimo
        empty_options = []
        for letter, option_text in options.items():
            if len(option_text.strip()) < 1:
                empty_options.append(letter)
        
        if empty_options:
            self.log_warning(f"Pregunta {question_id}: opciones vacías {empty_options}")
        
        # Validar estructura básica de pregunta
        if not (question_text.endswith('?') or 
                question_text.endswith('…') or 
                question_text.endswith('.') or
                ':' in question_text or
                any(word in question_text.lower() for word in 
                    ['qué', 'cuál', 'cómo', 'dónde', 'cuándo', 'indique', 'señale', 'se llama'])):
            self.log_warning(f"Pregunta {question_id}: estructura de pregunta inusual")
        
        return True

    def extract_exam(self, pdf_path: str, year: int, call: str) -> Dict:
        """
        Extrae un examen completo de Murcia con manejo robusto de errores.
        """
        pattern = MurciaExamPattern(year, call)
        
        print(f"🚢 Extrayendo examen de Murcia: {year} {call}")
        print(f"📄 Archivo: {os.path.basename(pdf_path)}")
        
        # Reiniciar contadores de errores
        self.errors = []
        self.warnings = []
        
        # Extraer texto del PDF
        text = self.extract_pdf_text(pdf_path)
        if not text:
            self.log_error("No se pudo extraer texto del PDF")
            return {}
        
        # Extraer preguntas
        questions = self.parse_questions_from_text(text, pattern)
        
        if not questions:
            self.log_error("No se extrajeron preguntas válidas")
            return {}
        
        # Agrupar por categoría
        questions_by_category = {}
        for question in questions:
            category = question["category"]  # Usar como entero, no como string
            if category not in questions_by_category:
                questions_by_category[category] = []
            questions_by_category[category].append(question)
        
        # Contar preguntas con respuestas
        questions_with_answers = sum(1 for q in questions if q.get("correct_answer") is not None)
        
        # Crear estructura final
        exam_data = {
            "exam_info": {
                "title": pattern.title,
                "subtitle": f"Código de Test 01",  # Siempre es Test 01 para Murcia
                "total_questions": len(questions),
                "expected_questions": pattern.total_questions,
                "categories": len(questions_by_category),
                "questions_with_answers": questions_with_answers,
                "community": pattern.community,
                "year": pattern.year,
                "call": pattern.call,
                "test_code": pattern.test_code,
            },
            "categories": {},
        }
        
        for category_id, category_questions in questions_by_category.items():
            exam_data["categories"][category_id] = {
                "name": PER_CATEGORIES[int(category_id)],  # Asegurar que se convierta a int para el lookup
                "questions": category_questions,
            }
        
        return exam_data

    def print_summary(self):
        """
        Imprime un resumen de errores y advertencias al final de la ejecución.
        """
        print("\n" + "="*60)
        print("📊 RESUMEN DE PROCESAMIENTO")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ Procesamiento completado sin errores ni advertencias")
        else:
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} ADVERTENCIAS:")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
                print()
            
            if self.errors:
                print(f"❌ {len(self.errors)} ERRORES:")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
                print()
                print("💡 Revisa estos errores y corrígelos manualmente si es necesario.")
        
        print("="*60)

    def generate_filename(self, year: int, call: str, base_dir: str = "data/exams/questions") -> str:
        """
        Genera nombre de archivo siguiendo el formato estándar.
        Formato: per-test01-murcia-YYYY-convocatoria.yaml
        """
        call_clean = call.lower().replace(" ", "-")
        filename = f"per-test01-murcia-{year}-{call_clean}.yaml"
        
        # Crear directorio por año
        year_dir = os.path.join(base_dir, "murcia", str(year))
        return os.path.join(year_dir, filename)

    def save_to_yaml(self, data: Dict, output_path: str):
        """Guarda los datos en formato YAML con manejo de errores."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print(f"💾 Datos guardados en {output_path}")
        except Exception as e:
            self.log_error(f"Error guardando archivo YAML: {str(e)}")
            raise


def main():
    """
    Función principal para ejecutar el extractor desde línea de comandos.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="🚢 Extractor de Preguntas de Exámenes PER de Murcia desde PDFs",
        epilog="""
Ejemplos de uso:
  %(prog)s --input-file data/raw/questions/murcia/2024/murcia-2024-junio.pdf
  %(prog)s --input-file /ruta/completa/murcia-2023-marzo.pdf --output-dir mi_directorio
  %(prog)s --input-file murcia-2022-noviembre.pdf --verbose

Este script extrae preguntas de exámenes PER de la región de Murcia desde archivos PDF
oficiales y las organiza automáticamente por categorías generando archivos YAML
estructurados.

Características específicas de Murcia:
- Todos los exámenes son tipo Test 01
- Preguntas numeradas con formato "1.- Texto pregunta"
- Opciones marcadas como "a) texto opción"
- Respuestas correctas identificadas por texto subrayado
- 45 preguntas distribuidas en 11 categorías estándar PER

El archivo de salida seguirá el formato: per-test01-murcia-{año}-{convocatoria}.yaml
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input-file", 
        required=True, 
        help="Archivo PDF con el examen de Murcia"
    )
    parser.add_argument(
        "--output-dir",
        default="data/exams/questions",
        help="Directorio donde guardar el archivo YAML (default: data/exams/questions)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada del procesamiento",
    )

    args = parser.parse_args()

    # Detectar automáticamente año y convocatoria desde el nombre del archivo
    pdf_filename = os.path.basename(args.input_file)
    
    # Formato esperado: murcia-YYYY-convocatoria.pdf
    match = re.search(r'murcia-(\d{4})-(\w+)\.pdf', pdf_filename)
    
    if match:
        year = int(match.group(1))
        call = match.group(2)
        if args.verbose:
            print(f"📅 Detectado automáticamente: Año {year}, Convocatoria {call}")
    else:
        print(f"❌ Error: Formato de archivo no reconocido: {pdf_filename}")
        print("💡 El formato esperado es: murcia-YYYY-convocatoria.pdf")
        print("   Ejemplo: murcia-2024-junio.pdf")
        return 1

    if args.verbose:
        print("🚢 Extractor de Preguntas PER - Murcia")
        print(f"📅 Año: {year}")
        print(f"📋 Convocatoria: {call}")
        print(f"📄 PDF origen: {args.input_file}")
        print(f"📁 Directorio salida: {args.output_dir}")
        print("-" * 60)

    # Verificar que el archivo PDF existe
    if not os.path.exists(args.input_file):
        print(f"❌ Error: No se encuentra el archivo PDF: {args.input_file}")
        return 1

    # Crear el extractor y procesar
    extractor = MurciaExamExtractor()

    try:
        # Extraer el examen
        exam_data = extractor.extract_exam(args.input_file, year, call)
        
        if not exam_data:
            print("❌ Error: No se pudo extraer el examen")
            extractor.print_summary()
            return 1

        # Generar nombre de archivo de salida
        output_file = extractor.generate_filename(year, call, args.output_dir)

        # Guardar en YAML
        extractor.save_to_yaml(exam_data, output_file)

        # Mostrar resumen
        exam_info = exam_data.get("exam_info", {})
        print("\n📊 RESUMEN DE EXTRACCIÓN:")
        print(f"   ✅ Preguntas extraídas: {exam_info.get('total_questions', 0)}/{exam_info.get('expected_questions', 0)}")
        print(f"   📚 Categorías encontradas: {exam_info.get('categories', 0)}")
        print(f"   📝 Preguntas con respuestas: {exam_info.get('questions_with_answers', 0)}")
        print(f"   💾 Archivo guardado: {output_file}")

        # Mostrar resumen de errores y advertencias
        extractor.print_summary()

        if args.verbose:
            print("\n💡 Para procesar más exámenes:")
            print("   python murcia_extract_questions.py --input-file otro-examen.pdf")

        return 0

    except Exception as e:
        print(f"❌ Error durante la extracción: {str(e)}")
        extractor.print_summary()
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
