#!/usr/bin/env python3
"""
Script para extraer respuestas del PDF de respuestas oficiales usando OCR

PROPÓSITO:
Este script procesa el PDF de respuestas oficiales y extrae las respuestas correctas 
usando OCR (Reconocimiento Óptico de Caracteres).

ESTRUCTURA DEL PDF:
- Cada página contiene respuestas de un tipo de examen específico
- Al inicio de cada página se indica el tipo de examen y modelo
- Las respuestas están numeradas consecutivamente (1, 2, 3, ...)
- Los valores válidos son: a, b, c, d, o "ANULADA"

TIPOS DE EXAMEN SOPORTADOS:
- PER: Patrón de Embarcación de Recreo
- PATRON_YATE: Patrón de Yate  
- CAPITAN_YATE: Capitán de Yate
- LICENCIA_NAVEGACION: Licencia de Navegación

IMPORTANTE - RUTA DEL PDF OBLIGATORIA:
El script requiere que especifiques la ruta completa al archivo PDF de respuestas.
No hay autodescubrimiento automático para evitar confusiones cuando hay múltiples PDFs.

INFORMACIÓN EXTRAÍDA DEL NOMBRE DEL ARCHIVO:
Del nombre del archivo PDF se extrae automáticamente:
- Comunidad (ej: madrid)
- Año (ej: 2025)
- Convocatoria (ej: abril)
Patrón esperado: comunidad-año-convocatoria.pdf

EJEMPLOS DE USO:
# Extraer respuestas de un examen específico
python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2025-abril.pdf" --exam-type PER --test-model TEST02

# Extraer todas las respuestas de todos los exámenes del PDF
python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2024-noviembre.pdf"

# Extraer respuestas de un tipo específico
python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2025-abril.pdf" --exam-type PER

PARÁMETROS:
--pdf-path: Ruta al archivo PDF (OBLIGATORIO)
--exam-type: Tipo de examen a extraer (PER, PATRON_YATE, CAPITAN_YATE, LICENCIA_NAVEGACION)
--test-model: Modelo específico del test (TEST01, TEST02, etc.)
--output-dir: Directorio de salida (por defecto: extracted_answers)

SALIDA:
- extracted_answers/: Directorio con archivos de texto por página
- extracted_answers/[exam_type]_[test_model]_answers.json: Respuestas específicas
- extracted_answers/exam_answers_complete.json: Todas las respuestas extraídas
"""

# OPTIMIZACIONES APLICADAS:
# - DPI aumentado a 600 para mejor calidad OCR
# - Preparado para usar PyMuPDF cuando esté disponible
# - Sistema de puntuación mejorado para seleccionar mejor resultado


from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
import json
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Añadir el directorio del proyecto al path para importaciones
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import settings

class PDFAnswerExtractor:
    """
    Extractor de respuestas del PDF oficial usando OCR
    """
    
    def __init__(self, pdf_path: str, output_dir: str = None, 
                 target_exam_type: Optional[str] = None, target_test_model: Optional[str] = None):
        # La ruta del PDF es obligatoria
        if pdf_path is None:
            raise ValueError("La ruta del archivo PDF es obligatoria. Use --pdf-path para especificarla.")
            
        self.pdf_path = Path(pdf_path)
        
        # Verificar que el archivo PDF existe
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"El archivo PDF no existe: {self.pdf_path}")
            
        if output_dir is None:
            # Usar directorio configurado para archivos extraídos
            output_dir = settings.get_extracted_path()
        else:
            output_dir = Path(output_dir)
            
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Filtros específicos
        self.target_exam_type = target_exam_type
        self.target_test_model = target_test_model
        
        # Extraer información del PDF para generar nombres de archivo
        self.pdf_info = self._extract_pdf_info_from_name()
        
        print(f"📄 Usando archivo PDF: {self.pdf_path}")
        print(f"📁 Directorio salida: {self.output_dir}")
        
        # Patrones para detectar tipos de examen (mejorados para OCR)
        self.exam_patterns = {
            'PER': [
                r'PATRÓN DE EMBARCACIONES DE RECREO',
                r'PATRON DE EMBARCACIONES DE RECREO',
                r'EMBARCACIONES DE RECREO',
                r'PER',
                # Patrones más flexibles para OCR problemático
                r'(?:aa)?(?:AND|ANG|ANB).*(?:AANDC|AANDA|AND)',  # Para "aaANDCAANDA" type patterns
                r'Cd{1,2}0{1,2}[dl]0{1,2}[1-4]',  # Para "Cdd01", "Cd001", etc.
                r'(?:Cc|C){1,2}[d]{1,2}0{1,2}[dl]0{1,2}[1-4]',  # Variaciones OCR del código
                # Patrones específicos para errores severos de OCR (como aaANDANDBACACNDC)
                r'(?:aa)?(?:AND|ANG|ANB|ANC)(?:AND|ANG|ANB|ANC)?(?:B|D|C)?(?:A|B|C|D)(?:C|A|B|D)(?:A|B|C|D)(?:C|N|M)(?:D|B|A)(?:C|D|A)',
                r'(?:aa)?(?:AND){1,2}(?:BAC|DAC|CAC|BAD)(?:AC|AD|AB)(?:NDC|CDC|NDA)',  # Específico para "aaANDANDBACACNDC"
            ],
            'PATRON_YATE': [
                r'PATRÓN DE YATE',
                r'PATRON DE YATE'
            ],
            'CAPITAN_YATE': [
                r'CAPITÁN DE YATE',
                r'CAPITAN DE YATE'
            ],
            'LICENCIA_NAVEGACION': [
                r'LICENCIA DE NAVEGACIÓN',
                r'LICENCIA DE NAVEGACION'
            ]
        }
        
        # Patrones para detectar modelos de test (mejorados)
        self.test_patterns = [
            r'CÓDIGO DE TEST\s*(\d+)',
            r'CODIGO DE TEST\s*(\d+)',
            r'TEST\s*(\d+)',
            r'Cdd(\d+)',  # Patrón específico que aparece en el OCR
            r'Cd0?d0?(\d+)',  # Variaciones del patrón Cdd01
            r'(?:Cc|C){1,2}[d]{1,2}0{1,2}[dl]0{1,2}([1-4])',  # Patrones OCR más flexibles
        ]
    
    def _extract_pdf_info_from_name(self) -> dict:
        """
        Extrae información del nombre del archivo PDF siguiendo el patrón:
        comunidad-año-convocatoria.pdf (ej: madrid-2025-abril.pdf)
        """
        pdf_info = {
            'comunidad': 'unknown',
            'año': 'unknown',
            'convocatoria': 'unknown'
        }
        
        # Extraer nombre del archivo sin extensión
        filename = self.pdf_path.stem
        
        # Patrón esperado: comunidad-año-convocatoria
        # Ej: madrid-2025-abril
        parts = filename.split('-')
        
        if len(parts) >= 3:
            pdf_info['comunidad'] = parts[0]
            pdf_info['año'] = parts[1]
            pdf_info['convocatoria'] = parts[2]
        elif len(parts) == 2:
            # Fallback si solo hay 2 partes
            pdf_info['comunidad'] = parts[0]
            pdf_info['año'] = parts[1]
        
        print(f"📋 Info extraída del PDF: {pdf_info}")
        return pdf_info
    
    def _generate_output_filename(self, exam_type: str, test_model: str) -> str:
        """
        Genera el nombre del archivo de salida siguiendo el patrón:
        {tipo}-{modelo}-{comunidad}-{año}-{convocatoria}.json
        """
        # Convertir tipo de examen a formato de archivo
        exam_type_lower = exam_type.lower()
        test_model_lower = test_model.lower()
        
        # Construir nombre usando la información del PDF
        filename = f"{exam_type_lower}-{test_model_lower}-{self.pdf_info['comunidad']}-{self.pdf_info['año']}-{self.pdf_info['convocatoria']}.json"
        
        print(f"📝 Nombre de archivo generado: {filename}")
        return filename

    def enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Mejora la imagen para obtener máxima precisión en el OCR con técnicas avanzadas
        Prioriza calidad sobre recursos de procesamiento
        """
        import cv2
        import numpy as np
        from PIL import ImageOps
        
        # Convertir a escala de grises si no lo está
        if image.mode != 'L':
            image = image.convert('L')
        
        # 1. Redimensionado optimizado para máxima calidad
        width, height = image.size
        if width < 4500:  # Umbral optimizado para calidad y rendimiento
            scale_factor = 4500 / width  # Factor de escala balanceado
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"   🔍 Imagen redimensionada a {new_width}x{new_height} para máxima calidad OCR")
        
        # 2. Convertir a numpy array para procesamiento avanzado con OpenCV
        img_array = np.array(image)
        
        # 3. Aplicar filtros de suavizado para reducir artefactos
        img_array = cv2.medianBlur(img_array, 3)
        img_array = cv2.GaussianBlur(img_array, (3, 3), 0)
        
        # 4. Mejora de contraste adaptativa con CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img_array = clahe.apply(img_array)
        
        # 5. Sin binarización - mejor resultado según pruebas OCR
        # Mantener la imagen procesada sin binarización adicional
        print(f"   🎯 Usando procesamiento sin binarización (configuración óptima)")
        
        # 10. Convertir de vuelta a PIL Image
        image = Image.fromarray(img_array)
        
        # 11. Aplicar mejoras adicionales con PIL
        # Contraste final (aumentado para mejor OCR)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.2)  # Optimizado a 2.2 según pruebas OCR
        
        # Nitidez final (aumentada para mejor definición)
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(3.2)  # Optimizado a 3.2 según pruebas OCR
        
        print(f"   ✅ Imagen procesada con técnicas avanzadas para OCR de máxima calidad")
        return image
    
    def extract_text_from_pdf(self) -> List[str]:
        """
        Convierte cada página del PDF en imagen y extrae el texto con OCR
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {self.pdf_path}")
        
        print(f"📄 Procesando PDF: {self.pdf_path}")
        print("🔄 Convirtiendo páginas a imágenes...")
        
        # Convertir PDF a imágenes (DPI balanceado para calidad y rendimiento)
        images = convert_from_path(str(self.pdf_path), dpi=600)
        print(f"✅ {len(images)} páginas convertidas")
        
        extracted_texts = []
        
        for i, image in enumerate(images):
            print(f"🔍 Procesando página {i+1}/{len(images)}...")
            
            # Mejorar imagen para OCR
            enhanced_image = self.enhance_image_for_ocr(image)
            
            # Aplicar OCR con múltiples configuraciones especializadas
            try:
                # Configuración 1: General para texto completo
                config_general = '--oem 3 --psm 6'
                text_general = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng',
                    config=config_general
                )
                
                # Configuración 2: Específica para números y respuestas
                config_specific = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDabcdANULADA.():=- '
                text_specific = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng', 
                    config=config_specific
                )
                
                # Configuración 3: Optimizada para líneas individuales
                config_lines = '--oem 3 --psm 13 -c tessedit_char_whitelist=0123456789ABCDabcd.():=- '
                text_lines = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng',
                    config=config_lines
                )
                
                # Configuración 4: Muy específica para números (problemas como 41→4)
                config_numbers = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDabcd'
                text_numbers = pytesseract.image_to_string(
                    enhanced_image,
                    lang='eng',
                    config=config_numbers
                )
                
                # Configuración 5: Para encabezados y texto completo (más permisiva)
                config_headers = '--oem 3 --psm 4'
                text_headers = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng',
                    config=config_headers
                )
                
                # Configuración 6: Bloques de texto completo con motor LSTM
                config_lstm = '--oem 1 --psm 6'
                text_lstm = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng',
                    config=config_lstm
                )
                
                # Evaluar cada configuración basándose en diferentes criterios
                candidates = []
                
                # Contar patrones de respuesta (formato: número + letra)
                pattern_answers = r'\d+\s*[ABCDabcd]'
                
                # Contar palabras clave de encabezados
                header_keywords = ['EXAMEN', 'RESPUESTAS', 'MADRID', 'PER', 'PATRON', 'CAPITAN', 'YATE', 'TEST']
                
                for config_name, text in [
                    ('general', text_general),
                    ('specific', text_specific), 
                    ('lines', text_lines),
                    ('numbers', text_numbers),
                    ('headers', text_headers),
                    ('lstm', text_lstm)
                ]:
                    answer_count = len(re.findall(pattern_answers, text))
                    header_count = sum(1 for keyword in header_keywords if keyword in text.upper())
                    
                    # Puntuación combinada: priorizamos respuestas pero también encabezados
                    score = answer_count * 2 + header_count
                    
                    candidates.append((config_name, text, answer_count, header_count, score))
                
                # Seleccionar la mejor configuración
                best_config, text, answer_count, header_count, best_score = max(candidates, key=lambda x: x[4])
                
                print(f"   🎯 Mejor configuración: {best_config} (respuestas: {answer_count}, encabezados: {header_count}, puntuación: {best_score})")
                
                # Si ninguna configuración detectó respuestas, usar la que detectó más encabezados
                if answer_count == 0:
                    header_candidates = [(name, txt, h_count) for name, txt, a_count, h_count, score in candidates if h_count > 0]
                    if header_candidates:
                        best_config, text, header_count = max(header_candidates, key=lambda x: x[2])
                        print(f"   📋 Configuración alternativa por encabezados: {best_config} (encabezados: {header_count})")
                
                # Si aún no hay resultados útiles, usar la configuración general
                if answer_count == 0 and header_count == 0:
                    text = text_general
                    best_config = 'general'
                    print(f"   ⚠️  Usando configuración general como respaldo")
                
                if answer_count > 0:
                    print(f"   ✅ Mejor resultado con configuración '{best_config}': {answer_count} respuestas detectadas")
                else:
                    print(f"   ⚠️  No se detectaron respuestas claras, usando resultado general")
                
                extracted_texts.append(text)
                
                # Guardar texto extraído para revisión
                text_file = self.output_dir / f"page_{i+1}_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== PÁGINA {i+1} ===\n\n")
                    f.write(text)
                
                print(f"   📝 Texto extraído: {len(text)} caracteres")
                
            except Exception as e:
                print(f"   ❌ Error en OCR página {i+1}: {e}")
                extracted_texts.append("")
        
        return extracted_texts
    
    def detect_exam_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detecta el tipo de examen y modelo en el texto de una página
        """
        text_upper = text.upper()
        
        # Primero verificar si hay exclusiones (exámenes que NO son PER aunque lo parezcan)
        exclusion_patterns = [
            r'CON PNB LIBERADO',
            r'PNB LIBERADO',
            r'LIBERADO',
        ]
        
        for exclusion_pattern in exclusion_patterns:
            if re.search(exclusion_pattern, text_upper):
                print(f"   🚫 Página excluida por patrón: {exclusion_pattern}")
                return None, None
        
        # Detectar tipo de examen
        exam_type = None
        for exam, patterns in self.exam_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    exam_type = exam
                    break
            if exam_type:
                break
        
        # Detectar modelo de test con lógica mejorada
        test_model = None
        
        # Primero intentar con patrones específicos
        for pattern in self.test_patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    test_num = int(match.group(1))
                    test_model = f"TEST{test_num:02d}"
                    break
                except (ValueError, IndexError):
                    continue
        
        # Si no se encontró modelo específico, inferir por contexto
        if not test_model and exam_type == 'PER':
            # Lógica de inferencia basada en patrones comunes del contenido
            # Si contiene "Cdd01" o similar, probablemente es TEST01
            if re.search(r'Cd{1,2}0{1,2}[dl]0{1,2}1', text_upper):
                test_model = "TEST01"
            # Si contiene "Cdd02" o similar, probablemente es TEST02  
            elif re.search(r'Cd{1,2}0{1,2}[dl]0{1,2}2', text_upper):
                test_model = "TEST02"
            # Si contiene "Cdd03" o similar, probablemente es TEST03
            elif re.search(r'Cd{1,2}0{1,2}[dl]0{1,2}3', text_upper):
                test_model = "TEST03"
            # Estrategia de inferencia por posición de página (basada en experiencia previa)
            else:
                # Analizar el contenido de las respuestas para hacer inferencia más inteligente
                lines = text.split('\n')
                response_count = 0
                for line in lines:
                    if re.search(r'\d+\s*[ABCDabcd]', line):
                        response_count += 1
                
                # Si hay muchas respuestas y patrones específicos, puede ser TEST01
                if response_count >= 40:  # La mayoría de respuestas están presentes
                    # Buscar patrones específicos que sugieran TEST01
                    if re.search(r'(?:aa)?(?:AND|ANG|ANB).*(?:AANDC|AANDA|AND)', text_upper):
                        test_model = "TEST01"
        
        return exam_type, test_model
    
    def extract_answers_from_text(self, text: str) -> Dict[int, str]:
        """
        Extrae las respuestas numeradas del texto de una página con lógica de numeración consecutiva
        """
        answers = {}
        lines = text.split('\n')
        
        print(f"   📋 Procesando {len(lines)} líneas de texto...")
        
        # Contador para numeración consecutiva
        expected_next_question = 1
        last_valid_question = 0
        
        # Patrones para detectar respuestas numeradas (simplificados)
        answer_patterns = [
            r'^(\d{1,2})\s*[\.\)\:\-]*\s*([ABCDabcd])(?:\s|$)',  # "1 A", "1. B", "1) C", "1: D", "1- A"
            r'^(\d{1,2})([ABCDabcd])(?:\s|$)',  # "1A", "2B"
            r'(\d{1,2})\s*[\.\)\:\-]*\s*([ABCDabcd])(?:\s|$)',  # Números en cualquier parte de la línea
        ]
        
        # Patrones para detectar líneas que contienen respuestas pero con números problemáticos
        answer_with_bad_number_patterns = [
            r'^(\d+)\s*[\.\)\:\-]*\s*([ABCDabcd])(?:\s|$)',  # Cualquier número + respuesta
            r'^([^\s]*)\s*[\.\)\:\-]*\s*([ABCDabcd])(?:\s|$)',  # Cualquier "número" + respuesta
            r'([ABCDabcd])(?:\s|$)',  # Solo respuesta, sin número claro
        ]
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            original_line = line
            line = self._clean_ocr_line(line)
            
            found_answer = False
            
            # Primera pasada: intentar detectar números válidos (1-2 dígitos en rango 1-45)
            for pattern in answer_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    try:
                        question_num = int(match.group(1))
                        answer = match.group(2).lower()
                        
                        # Validar que es una respuesta válida y número en rango correcto
                        if answer in ['a', 'b', 'c', 'd'] and 1 <= question_num <= 45:
                            # Para números válidos de 1-2 dígitos en rango, ser permisivo
                            if question_num not in answers:
                                answers[question_num] = answer
                                last_valid_question = question_num
                                expected_next_question = max(expected_next_question, question_num + 1)
                                print(f"   ✅ Pregunta {question_num}: {answer.upper()}")
                                found_answer = True
                        elif question_num > 45:
                            print(f"   ⚠️  Ignorando pregunta {question_num} (fuera de rango 1-45)")
                    except (ValueError, IndexError):
                        continue
            
            if found_answer:
                continue
            
            # Segunda pasada: aplicar lógica consecutiva para números problemáticos
            for pattern in answer_with_bad_number_patterns:
                match = re.match(pattern, line)
                if match:
                    try:
                        # Extraer la respuesta (siempre será el último grupo que matchee [ABCDabcd])
                        answer = None
                        for group in match.groups():
                            if group and group.lower() in ['a', 'b', 'c', 'd']:
                                answer = group.lower()
                                break
                        
                        if not answer:
                            continue
                        
                        # Obtener el "número" problemático para logging
                        problematic_number = match.group(1) if len(match.groups()) >= 2 else "sin número"
                        
                        # Aplicar numeración consecutiva
                        corrected_num = expected_next_question
                        
                        if corrected_num <= 45 and corrected_num not in answers:
                            answers[corrected_num] = answer
                            last_valid_question = corrected_num
                            expected_next_question = corrected_num + 1
                            print(f"   🔧 Pregunta {corrected_num}: {answer.upper()} (numeración consecutiva, era '{problematic_number}')")
                            found_answer = True
                            break
                    except (ValueError, IndexError):
                        continue
            
            # Tercera pasada: buscar respuestas anuladas
            if not found_answer and re.search(r'anulada|nula', line, re.IGNORECASE):
                # Buscar si hay un número en la línea
                num_match = re.search(r'(\d+)', line)
                if num_match:
                    try:
                        question_num = self._normalize_question_number(num_match.group(1))
                        if question_num and 1 <= question_num <= 45:
                            if self._is_consecutive_valid(question_num, expected_next_question, last_valid_question):
                                if question_num not in answers:
                                    answers[question_num] = "ANULADA"
                                    last_valid_question = question_num
                                    expected_next_question = question_num + 1
                                    print(f"   🚫 Pregunta {question_num}: ANULADA")
                            else:
                                # Aplicar lógica consecutiva para anuladas también
                                corrected_num = expected_next_question
                                if corrected_num <= 45 and corrected_num not in answers:
                                    answers[corrected_num] = "ANULADA"
                                    last_valid_question = corrected_num
                                    expected_next_question = corrected_num + 1
                                    print(f"   🚫 Pregunta {corrected_num}: ANULADA (corregido por lógica consecutiva)")
                    except ValueError:
                        continue
                else:
                    # Si no hay número, usar consecutiva
                    corrected_num = expected_next_question
                    if corrected_num <= 45 and corrected_num not in answers:
                        answers[corrected_num] = "ANULADA"
                        last_valid_question = corrected_num
                        expected_next_question = corrected_num + 1
                        print(f"   🚫 Pregunta {corrected_num}: ANULADA (numeración consecutiva)")
        
        print(f"   📊 Total respuestas extraídas: {len(answers)}")
        print(f"   � Última pregunta procesada: {last_valid_question}")
        print(f"   🔄 Siguiente pregunta esperada: {expected_next_question}")
        
        return answers
    
    def _is_consecutive_valid(self, question_num: int, expected_next: int, last_valid: int) -> bool:
        """
        Verifica si un número de pregunta es válido considerando la secuencia consecutiva
        """
        # Si es la primera pregunta
        if last_valid == 0:
            return question_num == 1
        
        # Si es exactamente la siguiente esperada
        if question_num == expected_next:
            return True
        
        # Permitir saltos hacia adelante razonables (hasta 5 preguntas)
        # Esto maneja casos donde el OCR se saltó algunas líneas
        if expected_next <= question_num <= expected_next + 5:
            return True
        
        # Permitir números hacia atrás solo si son cercanos (máximo 3 preguntas)
        # Esto maneja casos donde el OCR detectó preguntas fuera de orden
        if expected_next - 3 <= question_num < expected_next:
            return True
        
        # Para números muy grandes (probablemente errores OCR como 465)
        if question_num > 45:
            return False
        
        # Para otros casos, ser más permisivo y aceptar el número si está en rango válido
        if 1 <= question_num <= 45:
            return True
        
        return False
    
    def _normalize_question_number(self, raw_number: str) -> Optional[int]:
        """
        Normaliza números de pregunta que pueden tener errores de OCR
        """
        try:
            # Remover espacios y caracteres no numéricos del inicio
            number_str = re.sub(r'^[^\d]*', '', raw_number)
            number_str = re.sub(r'[^\d].*$', '', number_str)  # Quitar todo después del primer no-dígito
            
            if not number_str:
                return None
            
            # Si es un número de 3+ dígitos, usar solo los primeros 2
            if len(number_str) >= 3:
                number_str = number_str[:2]
            
            question_num = int(number_str)
            
            # Validar que esté en rango de preguntas válido (1-45 para PER)
            if 1 <= question_num <= 45:
                return question_num
            else:
                return None
                
        except (ValueError, IndexError):
            return None

    def _clean_ocr_line(self, line: str) -> str:
        """
        Limpia y normaliza una línea de texto OCR
        """
        # Eliminar caracteres extraños comunes en OCR
        line = re.sub(r'[|\\]', '', line)
        
        # Normalizar espacios múltiples
        line = re.sub(r'\s+', ' ', line)
        
        return line.strip()
    
    def _fix_ocr_answer(self, ocr_answer: str) -> Optional[str]:
        """
        Corrige errores comunes en las respuestas extraídas por OCR
        """
        ocr_answer = ocr_answer.upper()
        
        # Mapeo de errores comunes de OCR
        ocr_fixes = {
            'CC': 'c',
            'Cc': 'c',
            'AA': 'a',
            'Aa': 'a',
            'BB': 'b',
            'Bb': 'b',
            'DD': 'd',
            'Dd': 'd',
            'OA': 'a',
            'OB': 'b',
            'OC': 'c',
            'OD': 'd',  # Muy común en el OCR
            'Od': 'd',
        }
        
        return ocr_fixes.get(ocr_answer)
    
    def _validate_and_fix_answers(self, answers: Dict[int, str], expected_count: int = 45) -> Dict[int, str]:
        """
        Valida y corrige las respuestas extraídas, detectando preguntas faltantes
        """
        print(f"   🔍 Validando respuestas extraídas...")
        print(f"   📊 Encontradas: {len(answers)}, Esperadas: {expected_count}")
        
        # Detectar preguntas faltantes
        expected_questions = set(range(1, expected_count + 1))
        found_questions = set(answers.keys())
        missing_questions = expected_questions - found_questions
        
        if missing_questions:
            print(f"   ⚠️  Preguntas faltantes: {sorted(missing_questions)}")
            
            # Intentar recuperar preguntas faltantes con patrones más flexibles
            # (Esto se haría procesando el texto original nuevamente)
            
        else:
            print(f"   ✅ Todas las {expected_count} preguntas encontradas")
        
        # Validar que todas las respuestas son válidas
        invalid_answers = []
        for q_num, answer in answers.items():
            if answer not in ['a', 'b', 'c', 'd', 'ANULADA']:
                invalid_answers.append((q_num, answer))
        
        if invalid_answers:
            print(f"   ⚠️  Respuestas inválidas encontradas: {invalid_answers}")
            # Limpiar respuestas inválidas
            for q_num, _ in invalid_answers:
                del answers[q_num]
        
        print(f"   ✅ Validación completada: {len(answers)} respuestas válidas")
        return answers
    
    def _attempt_recovery_of_missing_answers(self, text: str, missing_questions: set) -> Dict[int, str]:
        """
        Intenta recuperar preguntas faltantes con patrones más flexibles
        """
        recovered = {}
        lines = text.split('\n')
        
        print(f"   🔄 Intentando recuperar {len(missing_questions)} preguntas faltantes...")
        print(f"   🔍 Preguntas faltantes: {sorted(list(missing_questions))}")
        
        # Crear un texto continuo para búsquedas más amplias
        full_text = ' '.join(lines)
        
        for missing_q in missing_questions:
            found = False
            
            # Patrones más flexibles para preguntas problemáticas
            flexible_patterns = [
                rf'\b{missing_q}\s*[\.\)\:\-]*\s*([ABCDabcd])\b',  # Número con respuesta, más flexible
                rf'{missing_q}([ABCDabcd])',          # Pegado
                rf'{missing_q}\s*([ABCDabcd])',       # Con espacio
                rf'(\b{missing_q}\b).*?([ABCDabcd])',  # Número y respuesta en la misma línea
                # Patrones específicos para errores de OCR numéricos
                rf'{missing_q}\d+\s*([ABCDabcd])',    # "17" en "177 A"
                rf'{missing_q}\s*\d\s*([ABCDabcd])',  # "17" en "17 2A"
            ]
            
            # Buscar en líneas individuales
            for line in lines:
                if found:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                for pattern in flexible_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            answer = match.group(2).lower()
                        else:
                            answer = match.group(1).lower()
                            
                        if answer in ['a', 'b', 'c', 'd']:
                            recovered[missing_q] = answer
                            print(f"   🔧 Recuperada pregunta {missing_q}: {answer.upper()} (línea: {line[:50]}...)")
                            found = True
                            break
                    
                    if found:
                        break
            
            # Si no se encontró, buscar en el texto completo
            if not found:
                for pattern in flexible_patterns:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            answer = match.group(2).lower()
                        else:
                            answer = match.group(1).lower()
                            
                        if answer in ['a', 'b', 'c', 'd']:
                            recovered[missing_q] = answer
                            print(f"   🔧 Recuperada pregunta {missing_q}: {answer.upper()} (texto completo)")
                            found = True
                            break
                    
                    if found:
                        break
            
            # Si aún no se encuentra, buscar patrones de OCR problemáticos
            if not found:
                # Buscar números que puedan ser esta pregunta con errores
                ocr_error_patterns = [
                    rf'\b{missing_q}[0-9]\s*([ABCDabcd])\b',  # Número con dígito extra
                    rf'\b[0-9]{missing_q}\s*([ABCDabcd])\b',  # Número con dígito antes
                ]
                
                for pattern in ocr_error_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        answer = match.group(1).lower()
                        if answer in ['a', 'b', 'c', 'd']:
                            recovered[missing_q] = answer
                            print(f"   🔧 Recuperada pregunta {missing_q}: {answer.upper()} (patrón OCR corregido)")
                            found = True
                            break
            
            # Buscar números incompletos que podrían ser la pregunta faltante
            if not found and missing_q >= 10:  # Solo para números de 2 dígitos
                # Buscar el primer dígito como número independiente
                first_digit = str(missing_q)[0]  # Para 41 → "4"
                
                # Buscar patrones donde aparece solo el primer dígito seguido de una respuesta
                # y verificar el contexto para confirmar que es la pregunta faltante
                incomplete_patterns = [
                    rf'\b{first_digit}\s+([ABCDabcd])\b',     # "4 A"
                    rf'\b{first_digit}([ABCDabcd])\b',        # "4A"
                    rf'^{first_digit}\s*([ABCDabcd])$',       # "4 A" como línea completa
                    rf'{first_digit}\s*([ABCDabcd])',         # "4 A" flexible
                ]
                
                # Patrones específicos para números problemáticos
                if missing_q == 41:
                    incomplete_patterns.extend([
                        r'\b4\s*1\s*([ABCDabcd])\b',           # "4 1 A" (41 separado)
                        r'\b44\s*([ABCDabcd])\b',              # "44 A" puede ser 41
                        r'\b4.*?([ABCDabcd])\b',               # "4..." cualquier cosa y respuesta
                    ])
                
                for line in lines:
                    if found:
                        break
                    line = line.strip()
                    
                    for pattern in incomplete_patterns:
                        match = re.match(pattern, line, re.IGNORECASE)
                        if match:
                            answer = match.group(1).lower()
                            if answer in ['a', 'b', 'c', 'd']:
                                # Verificar contexto: debe estar entre preguntas cercanas
                                try:
                                    line_index = lines.index(line) if line in lines else -1
                                    if line_index >= 0:
                                        # Buscar preguntas anteriores y posteriores para confirmar contexto
                                        prev_q_num = self._extract_question_number_from_context(lines, line_index, -1)
                                        next_q_num = self._extract_question_number_from_context(lines, line_index, 1)
                                        
                                        # Si el contexto sugiere que debería ser missing_q
                                        if ((prev_q_num and prev_q_num == missing_q - 1) or 
                                            (next_q_num and next_q_num == missing_q + 1)):
                                            recovered[missing_q] = answer
                                            print(f"   🔧 Recuperada pregunta {missing_q}: {answer.upper()} (número incompleto '{first_digit}' corregido, contexto: prev={prev_q_num}, next={next_q_num})")
                                            found = True
                                            break
                                except (ValueError, AttributeError):
                                    # Si hay error en el contexto, saltar este intento
                                    continue
        
        print(f"   ✅ Preguntas recuperadas: {len(recovered)}")
        return recovered
    
    def _extract_question_number_from_context(self, lines: list, current_index: int, direction: int) -> Optional[int]:
        """
        Extrae el número de pregunta de las líneas vecinas para verificar contexto
        direction: -1 para líneas anteriores, 1 para líneas posteriores
        """
        search_range = 3  # Buscar en 3 líneas hacia la dirección especificada
        
        if direction == -1:  # Buscar hacia atrás
            search_lines = lines[max(0, current_index - search_range):current_index]
            search_lines.reverse()  # Buscar desde la más cercana
        else:  # Buscar hacia adelante
            search_lines = lines[current_index + 1:min(len(lines), current_index + search_range + 1)]
        
        for line in search_lines:
            line = line.strip()
            # Buscar patrón de pregunta estándar
            match = re.match(r'^(\d{1,2})\s*[\.\)\:\-]*\s*[ABCDabcd]', line)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None

    def process_all_pages(self) -> Dict:
        """
        Procesa todas las páginas del PDF y organiza las respuestas por examen
        """
        print("🚀 Iniciando extracción de respuestas...")
        
        # Mostrar filtros activos
        if self.target_exam_type or self.target_test_model:
            print("🎯 Filtros activos:")
            if self.target_exam_type:
                print(f"   📂 Tipo de examen: {self.target_exam_type}")
            if self.target_test_model:
                print(f"   🔖 Modelo de test: {self.target_test_model}")
        
        try:
            # Extraer texto de todas las páginas
            page_texts = self.extract_text_from_pdf()
            
            all_exams = {}
            
            # Procesar cada página
            for i, text in enumerate(page_texts):
                page_num = i + 1
                print(f"\\n📖 Analizando página {page_num}...")
                
                try:
                    # Detectar tipo de examen y modelo
                    exam_type, test_model = self.detect_exam_info(text)
                    
                    if exam_type:
                        print(f"   📂 Tipo: {exam_type}")
                        if test_model:
                            print(f"   🔖 Modelo: {test_model}")
                        
                        # Aplicar filtros si están especificados
                        if self.target_exam_type and exam_type != self.target_exam_type:
                            print(f"   ⏭️  Omitiendo: no coincide con el tipo objetivo ({self.target_exam_type})")
                            continue
                        
                        if self.target_test_model and test_model != self.target_test_model:
                            print(f"   ⏭️  Omitiendo: no coincide con el modelo objetivo ({self.target_test_model})")
                            continue
                        
                        # Extraer respuestas
                        answers = self.extract_answers_from_text(text)
                        print(f"   📝 Respuestas iniciales encontradas: {len(answers)}")
                        
                        # Validar y corregir respuestas
                        if exam_type == 'PER':  # Para exámenes PER esperamos 45 preguntas
                            validated_answers = self._validate_and_fix_answers(answers, expected_count=45)
                            
                            # Si faltan preguntas, intentar recuperarlas
                            if len(validated_answers) < 45:
                                missing_questions = set(range(1, 46)) - set(validated_answers.keys())
                                recovered = self._attempt_recovery_of_missing_answers(text, missing_questions)
                                validated_answers.update(recovered)
                                print(f"   🔄 Después de recuperación: {len(validated_answers)} respuestas")
                                
                                # Reordenar respuestas después de la recuperación
                                validated_answers = dict(sorted(validated_answers.items(), key=lambda x: int(x[0])))
                            
                            answers = validated_answers
                        else:
                            # Para otros tipos de examen, usar validación básica
                            answers = self._validate_and_fix_answers(answers, expected_count=len(answers))
                        
                        print(f"   ✅ Respuestas finales: {len(answers)}")
                        
                        if answers:
                            # Organizar por tipo de examen y modelo
                            if exam_type not in all_exams:
                                all_exams[exam_type] = {}
                            
                            exam_key = test_model or "DEFAULT"
                            
                            # Si ya existe este examen, combinar respuestas
                            if exam_key in all_exams[exam_type]:
                                print(f"   🔄 Combinando con respuestas existentes de {exam_type} {exam_key}")
                                existing_answers = all_exams[exam_type][exam_key]['answers']
                                
                                # Combinar respuestas, priorizando las nuevas si hay conflicto
                                combined_answers = existing_answers.copy()
                                combined_answers.update(answers)
                                
                                # Mostrar estadísticas de combinación
                                new_count = len(answers)
                                existing_count = len(existing_answers)
                                combined_count = len(combined_answers)
                                print(f"   📊 Antes: {existing_count}, Nuevas: {new_count}, Combinadas: {combined_count}")
                                
                                all_exams[exam_type][exam_key] = {
                                    'page': f"{all_exams[exam_type][exam_key]['page']},{page_num}",  # Múltiples páginas
                                    'total_answers': len(combined_answers),
                                    'answers': combined_answers
                                }
                            else:
                                # Primera vez que encontramos este examen
                                all_exams[exam_type][exam_key] = {
                                    'page': page_num,
                                    'total_answers': len(answers),
                                    'answers': answers
                                }
                            
                            # Mostrar muestra de respuestas
                            sample_answers = list(answers.items())[:5]
                            print(f"   📋 Muestra: {sample_answers}")
                            print(f"   ✅ Página procesada correctamente")
                    else:
                        print(f"   ⚠️  No se detectó tipo de examen")
                        
                except Exception as e:
                    print(f"   ❌ Error procesando página {page_num}: {e}")
                    continue
            
            return all_exams
            
        except Exception as e:
            print(f"❌ Error en process_all_pages: {e}")
            return {}
    
    def save_results(self, all_exams: Dict):
        """
        Guarda los resultados en archivos JSON
        """
        print("\\n💾 Guardando resultados...")
        
        # Si hay filtros activos, generar archivo específico
        if self.target_exam_type or self.target_test_model:
            target_exam = self.target_exam_type or 'ALL'
            target_model = self.target_test_model or 'ALL'
            
            # Buscar los datos específicos
            found_data = None
            for exam_type, models in all_exams.items():
                if self.target_exam_type and exam_type != self.target_exam_type:
                    continue
                    
                for model, data in models.items():
                    if self.target_test_model and model != self.target_test_model:
                        continue
                    
                    found_data = {
                        'exam_type': exam_type,
                        'test_model': model,
                        'page': data['page'],
                        'total_answers': data['total_answers'],
                        'answers': data['answers']
                    }
                    break
                
                if found_data:
                    break
            
            if found_data:
                # Generar nombre de archivo específico usando el formato correcto
                exam_type_clean = found_data['exam_type'].lower()
                test_model_clean = found_data['test_model'].lower()
                
                # Generar nombre usando el patrón nuevo
                if exam_type_clean == 'per':
                    new_filename = self._generate_output_filename(found_data['exam_type'], found_data['test_model'])
                    specific_file_new = self.output_dir / new_filename
                    
                    # También generar el archivo de compatibilidad
                    legacy_filename = f"{exam_type_clean}_{test_model_clean}_answers.json"
                    specific_file_legacy = self.output_dir / legacy_filename
                    
                    # Estructura de datos completa con respuestas ordenadas
                    ordered_answers = dict(sorted(found_data['answers'].items(), key=lambda x: int(x[0])))
                    # Filtrar solo respuestas en rango 1-45 para PER
                    filtered_answers = {k: v for k, v in ordered_answers.items() if 1 <= int(k) <= 45}
                    actual_total = len(filtered_answers)
                    
                    complete_data = {
                        'exam_type': found_data['exam_type'],
                        'test_model': found_data['test_model'],
                        'total_answers': actual_total,
                        'answers': filtered_answers,
                        'source_pdf': self.pdf_path.name,
                        'generated_at': None,
                        'pdf_info': self.pdf_info
                    }
                    
                    # Actualizar found_data para compatibilidad
                    found_data['answers'] = filtered_answers
                    found_data['total_answers'] = actual_total
                    
                    # Guardar archivo con nuevo formato
                    with open(specific_file_new, 'w', encoding='utf-8') as f:
                        json.dump(complete_data, f, indent=2, ensure_ascii=False)
                    print(f"🎯 Archivo específico (nuevo formato): {specific_file_new}")
                    
                    # Guardar archivo legacy para compatibilidad
                    with open(specific_file_legacy, 'w', encoding='utf-8') as f:
                        json.dump(found_data, f, indent=2, ensure_ascii=False)
                    print(f"🎯 Archivo específico (compatibilidad): {specific_file_legacy}")
                else:
                    # Para otros tipos de examen, usar formato básico
                    legacy_filename = f"{exam_type_clean}_{test_model_clean}_answers.json"
                    specific_file = self.output_dir / legacy_filename
                    
                    with open(specific_file, 'w', encoding='utf-8') as f:
                        json.dump(found_data, f, indent=2, ensure_ascii=False)
                    print(f"🎯 Archivo específico: {specific_file}")
                
                print(f"   📊 {found_data['total_answers']} respuestas extraídas")
            else:
                print("⚠️  No se encontraron datos que coincidan con los filtros especificados")
        
        # Archivo completo con todos los exámenes encontrados (siempre se genera)
        if all_exams:
            complete_file = self.output_dir / "exam_answers_complete.json"
            with open(complete_file, 'w', encoding='utf-8') as f:
                json.dump(all_exams, f, indent=2, ensure_ascii=False)
            print(f"📄 Archivo completo: {complete_file}")
            
            # Solo generar archivos específicos automáticamente si NO hay filtros activos
            # (evita duplicar archivos cuando se usan filtros específicos)
            if not (self.target_exam_type or self.target_test_model):
                print("🔧 Generando archivos individuales para todos los exámenes encontrados...")
                
                # Generar archivos para TODOS los exámenes encontrados
                for exam_type, models in all_exams.items():
                    for model, exam_data in models.items():
                        print(f"   📝 Generando archivo para {exam_type} {model}...")
                        
                        # Preparar datos del examen
                        ordered_answers = dict(sorted(exam_data['answers'].items(), key=lambda x: int(x[0])))
                        
                        # Para PER, filtrar solo respuestas en rango 1-45
                        if exam_type == 'PER':
                            filtered_answers = {k: v for k, v in ordered_answers.items() if 1 <= int(k) <= 45}
                            actual_total = len(filtered_answers)
                        else:
                            filtered_answers = ordered_answers
                            actual_total = len(filtered_answers)
                        
                        # Generar nombres de archivo
                        if exam_type == 'PER':
                            # Usar nuevo formato para PER
                            new_filename = self._generate_output_filename(exam_type, model)
                            exam_file_new = self.output_dir / new_filename
                            
                            # Archivo de compatibilidad
                            legacy_filename = f"{exam_type.lower()}_{model.lower()}_answers.json"
                            exam_file_legacy = self.output_dir / legacy_filename
                            
                            complete_data = {
                                'exam_type': exam_type,
                                'test_model': model,
                                'total_answers': actual_total,
                                'answers': filtered_answers,
                                'source_pdf': self.pdf_path.name,
                                'generated_at': exam_data.get('generated_at'),
                                'pdf_info': self.pdf_info
                            }
                            
                            # Guardar con nuevo formato
                            with open(exam_file_new, 'w', encoding='utf-8') as f:
                                json.dump(complete_data, f, indent=2, ensure_ascii=False)
                            print(f"   ✅ {exam_file_new}")
                            
                            # Guardar con formato legacy
                            legacy_data = {
                                'exam_type': exam_type,
                                'test_model': model,
                                'page': exam_data['page'],
                                'total_answers': actual_total,
                                'answers': filtered_answers
                            }
                            with open(exam_file_legacy, 'w', encoding='utf-8') as f:
                                json.dump(legacy_data, f, indent=2, ensure_ascii=False)
                            print(f"   ✅ {exam_file_legacy} (compatibilidad)")
                            
                        else:
                            # Para otros tipos de examen, usar formato completo con metadatos
                            new_filename = self._generate_output_filename(exam_type, model)
                            exam_file_new = self.output_dir / new_filename
                            
                            complete_data = {
                                'exam_type': exam_type,
                                'test_model': model,
                                'total_answers': actual_total,
                                'answers': filtered_answers,
                                'source_pdf': self.pdf_path.name,
                                'generated_at': exam_data.get('generated_at'),
                                'pdf_info': self.pdf_info
                            }
                            
                            with open(exam_file_new, 'w', encoding='utf-8') as f:
                                json.dump(complete_data, f, indent=2, ensure_ascii=False)
                            print(f"   ✅ {exam_file_new}")
                        
                        print(f"      📊 {actual_total} respuestas")
            
            # Resumen general
            summary_file = self.output_dir / "exam_summary.json"
            summary = {}
            for exam_type, models in all_exams.items():
                summary[exam_type] = {}
                for model, data in models.items():
                    summary[exam_type][model] = {
                        'page': data['page'],
                        'total_answers': data['total_answers']
                    }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📊 Resumen: {summary_file}")
    
    def print_summary(self, all_exams: Dict):
        """
        Imprime un resumen de los resultados
        """
        print("\\n" + "="*60)
        print("📊 RESUMEN DE EXTRACCIÓN")
        print("="*60)
        
        if not all_exams:
            print("⚠️  No se encontraron exámenes que coincidan con los filtros")
            if self.target_exam_type:
                print(f"   📂 Tipo objetivo: {self.target_exam_type}")
            if self.target_test_model:
                print(f"   🔖 Modelo objetivo: {self.target_test_model}")
            return
        
        total_answers = 0
        for exam_type, models in all_exams.items():
            print(f"\\n🎯 {exam_type}:")
            for model, data in models.items():
                count = data['total_answers']
                total_answers += count
                print(f"   📝 {model}: {count} respuestas (página {data['page']})")
        
        print(f"\\n📈 TOTAL RESPUESTAS EXTRAÍDAS: {total_answers}")
        
        # Información específica sobre filtros aplicados
        if self.target_exam_type or self.target_test_model:
            print("\\n🎯 FILTROS APLICADOS:")
            if self.target_exam_type:
                print(f"   📂 Tipo de examen: {self.target_exam_type}")
            if self.target_test_model:
                print(f"   🔖 Modelo de test: {self.target_test_model}")
            
            # Mostrar archivo específico generado
            for exam_type, models in all_exams.items():
                for model, data in models.items():
                    exam_clean = exam_type.lower().replace('_', '-')
                    model_clean = model.lower().replace('test', 'test')
                    filename = f"{exam_clean}_{model_clean}_answers.json"
                    print(f"   📄 Archivo generado: extracted_answers/{filename}")
        
        # Información específica sobre PER Test 01 (si existe)
        if 'PER' in all_exams and 'TEST01' in all_exams['PER']:
            print("\\n🎯 PER TEST 01 DETECTADO:")
            per_data = all_exams['PER']['TEST01']
            print(f"   ✅ {per_data['total_answers']} respuestas extraídas")
            print(f"   📄 Archivos generados:")
            print(f"      - extracted_answers/{self._generate_output_filename('PER', 'TEST01')}")
            print(f"      - extracted_answers/per_test01_answers.json (compatibilidad)")
        
        print("\\n💡 ARCHIVOS GENERADOS:")
        print("   📄 exam_answers_complete.json - Todas las respuestas")
        print("   📊 exam_summary.json - Resumen de exámenes")
        if self.target_exam_type or self.target_test_model:
            print("   🎯 [exam]_[model]_answers.json - Respuestas específicas")
        

    def _detect_sequential_patterns(self, text: str, answers: Dict[int, str]) -> Dict[int, str]:
        """
        Detecta patrones secuenciales para identificar números mal reconocidos por OCR
        usando el contexto de la secuencia esperada (1, 2, 3, ..., 45)
        """
        print(f"   🔍 Analizando patrones secuenciales...")
        
        # Identificar huecos en la secuencia
        expected_questions = set(range(1, 46))
        found_questions = set(answers.keys())
        missing_questions = sorted(expected_questions - found_questions)
        
        if not missing_questions:
            print(f"   ✅ Secuencia completa, no necesita correcciones")
            return answers
        
        print(f"   📋 Preguntas faltantes: {missing_questions}")
        
        lines = text.split('\n')
        recovered = {}
        
        # Analizar líneas para encontrar patrones problemáticos específicos
        line_analysis = self._analyze_lines_for_sequence_errors(lines, found_questions)
        
        # Para cada pregunta faltante, intentar detectarla usando múltiples estrategias
        for missing_q in missing_questions:
            print(f"   🔍 Buscando pregunta {missing_q}...")
            
            # Estrategia 1: Buscar números incompletos que podrían ser esta pregunta
            incomplete_candidates = self._find_incomplete_number_patterns(lines, missing_q, found_questions)
            
            # Estrategia 2: Buscar números con dígitos extra que podrían ser esta pregunta
            extra_digit_candidates = self._find_extra_digit_patterns(lines, missing_q, found_questions)
            
            # Estrategia 3: Buscar en posición secuencial esperada
            position_candidates = self._find_by_sequential_position(lines, missing_q, found_questions)
            
            # Combinar todos los candidatos
            all_candidates = incomplete_candidates + extra_digit_candidates + position_candidates
            
            if all_candidates:
                # Evaluar cada candidato usando contexto secuencial mejorado
                best_candidate = self._evaluate_candidates_by_context_advanced(all_candidates, missing_q, found_questions, line_analysis)
                
                if best_candidate:
                    line_text, answer, confidence, strategy = best_candidate
                    recovered[missing_q] = answer
                    found_questions.add(missing_q)  # Actualizar conjunto para próximas búsquedas
                    print(f"   ✅ Pregunta {missing_q}: {answer.upper()} (confianza: {confidence:.2f}, estrategia: {strategy}, línea: {line_text[:50]}...)")
        
        # Añadir preguntas recuperadas
        answers.update(recovered)
        
        print(f"   📊 Preguntas recuperadas: {len(recovered)}")
        return answers
    
    def _analyze_lines_for_sequence_errors(self, lines: List[str], found_questions: set) -> Dict:
        """
        Analiza las líneas para identificar patrones comunes de errores secuenciales
        """
        analysis = {
            'line_to_question': {},
            'question_to_line': {},
            'suspicious_patterns': []
        }
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Buscar números de pregunta conocidos
            for q_num in found_questions:
                if re.search(rf'\b{q_num}\b', line):
                    analysis['line_to_question'][line_idx] = q_num
                    analysis['question_to_line'][q_num] = line_idx
            
            # Identificar patrones sospechosos
            if re.search(r'\d{3,}', line):  # Números de 3+ dígitos
                analysis['suspicious_patterns'].append(('extra_digits', line_idx, line))
            
            if re.search(r'^\d\s+[ABCDabcd]', line):  # Un solo dígito seguido de respuesta
                analysis['suspicious_patterns'].append(('single_digit', line_idx, line))
        
        return analysis
    
    def _find_incomplete_number_patterns(self, lines: List[str], target_question: int, found_questions: set) -> List[Tuple[str, str, float, str]]:
        """
        Busca números incompletos que podrían ser la pregunta objetivo (ej: "4" en lugar de "41")
        """
        candidates = []
        target_str = str(target_question)
        
        if len(target_str) < 2:
            return candidates
        
        # Buscar patrones donde falta el primer dígito
        first_digit = target_str[0]
        second_digit = target_str[1]
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Patrón: segundo dígito seguido de respuesta (ej: "1 A" para pregunta 41)
            pattern = rf'^{second_digit}\s+([ABCDabcd])\b'
            match = re.match(pattern, line)
            if match:
                answer = match.group(1).lower()
                if answer in ['a', 'b', 'c', 'd']:
                    # Verificar contexto: debe estar cerca de preguntas similares
                    context_score = self._calculate_context_score_for_incomplete(line_idx, target_question, found_questions, lines)
                    candidates.append((line, answer, context_score, 'incomplete_number'))
            
            # Patrón: primer dígito seguido de punto y respuesta (ej: "4. A" para pregunta 44)
            pattern2 = rf'^{second_digit}\.?\s*([ABCDabcd])\b'
            match2 = re.match(pattern2, line)
            if match2:
                answer = match2.group(1).lower()
                if answer in ['a', 'b', 'c', 'd']:
                    context_score = self._calculate_context_score_for_incomplete(line_idx, target_question, found_questions, lines)
                    candidates.append((line, answer, context_score, 'incomplete_with_dot'))
        
        return candidates
    
    def _find_extra_digit_patterns(self, lines: List[str], target_question: int, found_questions: set) -> List[Tuple[str, str, float, str]]:
        """
        Busca números con dígitos extra que podrían ser la pregunta objetivo (ej: "358" en lugar de "35")
        """
        candidates = []
        target_str = str(target_question)
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Buscar números que empiecen con los dígitos objetivo
            pattern = rf'^({target_str}\d+)\s*([ABCDabcd])\b'
            match = re.match(pattern, line)
            if match:
                full_number = match.group(1)
                answer = match.group(2).lower()
                
                if answer in ['a', 'b', 'c', 'd'] and len(full_number) > len(target_str):
                    context_score = self._calculate_context_score_for_extra_digits(line_idx, target_question, found_questions, lines)
                    candidates.append((line, answer, context_score, 'extra_digits'))
        
        return candidates
    
    def _find_by_sequential_position(self, lines: List[str], target_question: int, found_questions: set) -> List[Tuple[str, str, float, str]]:
        """
        Busca respuestas basándose en la posición secuencial esperada
        """
        candidates = []
        
        # Encontrar la posición esperada basándose en preguntas cercanas conocidas
        expected_line_range = self._estimate_line_position(target_question, found_questions, lines)
        
        if expected_line_range:
            start_line, end_line = expected_line_range
            
            for line_idx in range(max(0, start_line), min(len(lines), end_line + 1)):
                line = lines[line_idx].strip()
                if not line:
                    continue
                
                # Buscar líneas que tengan respuesta pero número problemático
                answer_match = re.search(r'([ABCDabcd])\b', line)
                if answer_match:
                    answer = answer_match.group(1).lower()
                    if answer in ['a', 'b', 'c', 'd']:
                        # Verificar que no sea una pregunta ya asignada
                        existing_q = None
                        for q in found_questions:
                            if re.search(rf'\b{q}\b', line):
                                existing_q = q
                                break
                        
                        if not existing_q:
                            context_score = self._calculate_positional_context_score(line_idx, target_question, found_questions, lines)
                            candidates.append((line, answer, context_score, 'sequential_position'))
        
        return candidates
    
    def _calculate_context_score_for_incomplete(self, line_idx: int, target_question: int, found_questions: set, lines: List[str]) -> float:
        """
        Calcula puntuación de contexto para números incompletos
        """
        score = 0.0
        
        # Buscar preguntas cercanas conocidas
        nearby_questions = []
        for offset in [-3, -2, -1, 1, 2, 3]:
            check_idx = line_idx + offset
            if 0 <= check_idx < len(lines):
                for q in found_questions:
                    if re.search(rf'\b{q}\b', lines[check_idx]):
                        nearby_questions.append(q)
        
        if nearby_questions:
            min_distance = min(abs(q - target_question) for q in nearby_questions)
            score += 0.8 / (min_distance + 1)
        
        # Bonificación si está en la zona esperada (preguntas 35-45 al final)
        if target_question >= 35:
            total_lines = len([l for l in lines if l.strip()])
            relative_position = line_idx / total_lines if total_lines > 0 else 0
            if relative_position > 0.7:  # En el último 30% del texto
                score += 0.3
        
        return score
    
    def _calculate_context_score_for_extra_digits(self, line_idx: int, target_question: int, found_questions: set, lines: List[str]) -> float:
        """
        Calcula puntuación de contexto para números con dígitos extra
        """
        score = 0.5  # Puntuación base alta porque es un patrón común
        
        # Verificar secuencia local
        prev_line = lines[line_idx - 1] if line_idx > 0 else ""
        next_line = lines[line_idx + 1] if line_idx < len(lines) - 1 else ""
        
        # Buscar pregunta anterior
        for q in range(target_question - 3, target_question):
            if q in found_questions and re.search(rf'\b{q}\b', prev_line):
                score += 0.4
                break
        
        # Buscar pregunta posterior
        for q in range(target_question + 1, target_question + 4):
            if q in found_questions and re.search(rf'\b{q}\b', next_line):
                score += 0.4
                break
        
        return score
    
    def _calculate_positional_context_score(self, line_idx: int, target_question: int, found_questions: set, lines: List[str]) -> float:
        """
        Calcula puntuación de contexto basada en posición secuencial
        """
        score = 0.2  # Puntuación base baja, requiere evidencia fuerte
        
        # Verificar que esté en la posición secuencial correcta
        expected_position = self._estimate_exact_line_position(target_question, found_questions, lines)
        if expected_position and abs(line_idx - expected_position) <= 2:
            score += 0.6
        
        return score
    
    def _estimate_line_position(self, target_question: int, found_questions: set, lines: List[str]) -> Optional[Tuple[int, int]]:
        """
        Estima el rango de líneas donde debería estar la pregunta objetivo
        """
        question_positions = []
        
        for q in found_questions:
            for line_idx, line in enumerate(lines):
                if re.search(rf'\b{q}\b', line):
                    question_positions.append((q, line_idx))
        
        if len(question_positions) < 2:
            return None
        
        # Ordenar por número de pregunta
        question_positions.sort()
        
        # Interpolar posición esperada
        for i in range(len(question_positions) - 1):
            q1, line1 = question_positions[i]
            q2, line2 = question_positions[i + 1]
            
            if q1 < target_question < q2:
                # Interpolación lineal
                ratio = (target_question - q1) / (q2 - q1)
                estimated_line = int(line1 + ratio * (line2 - line1))
                return (estimated_line - 2, estimated_line + 2)
        
        return None
    
    def _estimate_exact_line_position(self, target_question: int, found_questions: set, lines: List[str]) -> Optional[int]:
        """
        Estima la línea exacta donde debería estar la pregunta objetivo
        """
        range_result = self._estimate_line_position(target_question, found_questions, lines)
        if range_result:
            start_line, end_line = range_result
            return (start_line + end_line) // 2
        return None
    
    def _evaluate_candidates_by_context_advanced(self, candidates: List[Tuple[str, str, float, str]], 
                                               target_question: int, found_questions: set, line_analysis: Dict) -> Optional[Tuple[str, str, float, str]]:
        """
        Evalúa candidatos usando contexto secuencial avanzado
        """
        if not candidates:
            return None
        
        best_candidate = None
        best_confidence = 0.0
        
        for line_text, answer, base_score, strategy in candidates:
            confidence = base_score
            
            # Factor 1: Calidad de la respuesta
            if answer in ['a', 'b', 'c', 'd']:
                confidence += 0.2
            
            # Factor 2: Estrategia específica
            strategy_bonus = {
                'incomplete_number': 0.3,
                'incomplete_with_dot': 0.25,
                'extra_digits': 0.4,
                'sequential_position': 0.1
            }
            confidence += strategy_bonus.get(strategy, 0.0)
            
            # Factor 3: Ausencia de ambigüedad
            other_numbers = re.findall(r'\d+', line_text)
            if len(other_numbers) <= 1:
                confidence += 0.15
            
            # Factor 4: Patrón específico para finales de secuencia (35-45)
            if target_question >= 35:
                confidence += 0.1
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_candidate = (line_text, answer, confidence, strategy)
        
        # Solo devolver si la confianza es suficiente
        if best_confidence > 0.4:  # Umbral más alto para mayor precisión
            return best_candidate
        
        return None
    
    def _find_number_candidates(self, lines: List[str], target_question: int) -> List[Tuple[str, str, List[int]]]:
        """
        Encuentra candidatos de números en el texto que podrían ser la pregunta objetivo
        """
        candidates = []
        target_str = str(target_question)
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Buscar todos los números en la línea
            number_matches = re.finditer(r'\d+', line)
            
            for match in number_matches:
                number_str = match.group()
                possible_numbers = self._generate_possible_corrections(number_str, target_question)
                
                if target_question in possible_numbers:
                    # Buscar respuesta en la misma línea
                    answer_match = re.search(r'([ABCDabcd])', line)
                    if answer_match:
                        answer = answer_match.group(1).lower()
                        if answer in ['a', 'b', 'c', 'd']:
                            candidates.append((line, answer, [line_idx]))
        
        return candidates
    
    def _generate_possible_corrections(self, ocr_number: str, target: int) -> List[int]:
        """
        Genera posibles correcciones para un número mal reconocido por OCR
        """
        corrections = []
        target_str = str(target)
        
        try:
            # 1. El número tal como está
            if ocr_number.isdigit():
                corrections.append(int(ocr_number))
            
            # 2. Si el OCR tiene dígitos extra, probar subconjuntos
            if len(ocr_number) > len(target_str):
                # Probar eliminar dígitos del final
                for i in range(1, len(ocr_number)):
                    truncated = ocr_number[:-i]
                    if truncated.isdigit() and len(truncated) <= 2:
                        corrections.append(int(truncated))
                
                # Probar eliminar dígitos del inicio
                for i in range(1, len(ocr_number)):
                    truncated = ocr_number[i:]
                    if truncated.isdigit() and len(truncated) <= 2:
                        corrections.append(int(truncated))
            
            # 3. Si falta un dígito (ej: "1" en lugar de "11")
            if len(ocr_number) == 1 and target >= 10:
                first_digit = target_str[0]
                if ocr_number == first_digit:
                    corrections.append(target)
                
                # Probar también el segundo dígito
                if len(target_str) > 1:
                    second_digit = target_str[1]
                    if ocr_number == second_digit:
                        corrections.append(target)
            
            # 4. Correcciones específicas de OCR común
            ocr_digit_map = {
                '0': ['0', 'O', 'o'],
                '1': ['1', 'l', 'I', '|'],
                '2': ['2', 'Z'],
                '3': ['3'],
                '4': ['4'],
                '5': ['5', 'S'],
                '6': ['6'],
                '7': ['7'],
                '8': ['8', 'B'],
                '9': ['9', 'g']
            }
            
            # Intentar correcciones de dígitos individuales
            if len(ocr_number) == len(target_str):
                corrected = ""
                for i, char in enumerate(ocr_number):
                    target_digit = target_str[i]
                    if char in ocr_digit_map.get(target_digit, []):
                        corrected += target_digit
                    else:
                        corrected += char
                
                if corrected.isdigit():
                    corrections.append(int(corrected))
        
        except (ValueError, IndexError):
            pass
        
        return list(set(corrections))  # Eliminar duplicados
    
    def _evaluate_candidates_by_context(self, candidates: List[Tuple[str, str, List[int]]], 
                                      target_question: int, found_questions: set) -> Optional[Tuple[str, str, float]]:
        """
        Evalúa candidatos usando contexto secuencial para determinar el más probable
        """
        if not candidates:
            return None
        
        best_candidate = None
        best_confidence = 0.0
        
        for line_text, answer, line_indices in candidates:
            confidence = 0.0
            
            # Factor 1: Posición secuencial esperada
            for line_idx in line_indices:
                # Verificar si hay preguntas consecutivas cerca
                nearby_questions = []
                
                # Buscar preguntas anteriores y posteriores en líneas cercanas
                for offset in [-3, -2, -1, 1, 2, 3]:
                    check_idx = line_idx + offset
                    if 0 <= check_idx < len(line_indices):
                        # Buscar números de pregunta en esa línea
                        for found_q in found_questions:
                            if abs(found_q - target_question) <= 3:  # Preguntas cercanas
                                nearby_questions.append(found_q)
                
                # Si hay preguntas cercanas, aumentar confianza
                if nearby_questions:
                    min_distance = min(abs(q - target_question) for q in nearby_questions)
                    confidence += 0.5 / (min_distance + 1)
            
            # Factor 2: Calidad de la respuesta
            if answer in ['a', 'b', 'c', 'd']:
                confidence += 0.3
            
            # Factor 3: Claridad del patrón en la línea
            if re.search(rf'\b{target_question}\b.*[ABCDabcd]', line_text):
                confidence += 0.2
            
            # Factor 4: Ausencia de ambigüedad
            other_numbers = re.findall(r'\d+', line_text)
            if len(other_numbers) == 1:  # Solo un número en la línea
                confidence += 0.1
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_candidate = (line_text, answer, confidence)
        
        # Solo devolver si la confianza es suficiente
        if best_confidence > 0.3:
            return best_candidate
        
        return None
        

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(
        description="Extractor de respuestas de PDFs de exámenes oficiales usando OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EJEMPLOS DE USO:

  # Extraer respuestas de un examen específico
  python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2025-abril.pdf" --exam-type PER --test-model TEST02

  # Extraer todas las respuestas de todos los exámenes del PDF
  python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2024-noviembre.pdf"

  # Extraer respuestas de un tipo específico
  python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2025-abril.pdf" --exam-type PER

  # Especificar directorio de salida personalizado
  python madrid_extract_answers.py --pdf-path "data/raw/answers/madrid-2025-abril.pdf" --output-dir "mis_respuestas" --exam-type PER

IMPORTANTE:
  La ruta al archivo PDF (--pdf-path) es OBLIGATORIA. No hay autodescubrimiento automático.
  
  Del nombre del archivo se extrae automáticamente:
  - Comunidad, año y convocatoria (patrón: comunidad-año-convocatoria.pdf)
  - Ejemplo: madrid-2025-abril.pdf -> madrid, 2025, abril

TIPOS DE EXAMEN SOPORTADOS:
  - PER: Patrón de Embarcación de Recreo
  - PATRON_YATE: Patrón de Yate  
  - CAPITAN_YATE: Capitán de Yate
  - LICENCIA_NAVEGACION: Licencia de Navegación

MODELOS DE TEST COMUNES:
  - TEST01, TEST02, TEST03, etc.

EXCLUSIONES AUTOMÁTICAS:
  - Páginas con "PNB LIBERADO" son excluidas automáticamente (no son exámenes PER estándar)
        """
    )
    
    parser.add_argument(
        '--exam-type',
        type=str,
        choices=['PER', 'PATRON_YATE', 'CAPITAN_YATE', 'LICENCIA_NAVEGACION'],
        help='Tipo de examen a extraer (filtro opcional)'
    )
    
    parser.add_argument(
        '--test-model',
        type=str,
        help='Modelo específico del test a extraer (ej: TEST01, TEST02, etc.)'
    )
    
    parser.add_argument(
        '--pdf-path',
        type=str,
        required=True,
        help='Ruta al archivo PDF de respuestas (OBLIGATORIO). Ejemplo: data/raw/answers/madrid-2025-abril.pdf'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directorio de salida para los archivos JSON (default: usar configuración global)'
    )
    
    return parser.parse_args()


def main():
    """
    Función principal
    """
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Mostrar encabezado
        print("🚀 EXTRACTOR DE RESPUESTAS OCR - PDF OFICIAL")
        print("="*60)
        
        if args.exam_type:
            print(f"🎯 Filtro tipo examen: {args.exam_type}")
        if args.test_model:
            print(f"🔖 Filtro modelo test: {args.test_model}")
        
        if not args.exam_type and not args.test_model:
            print("📋 Modo: Extraer TODOS los exámenes del PDF")
        else:
            print("🎯 Modo: Extracción FILTRADA")
        
        print("="*60)
        
        # Crear extractor con los parámetros especificados
        extractor = PDFAnswerExtractor(
            pdf_path=args.pdf_path,  # Siempre obligatorio
            output_dir=args.output_dir if args.output_dir else None,  # None usa configuración global
            target_exam_type=args.exam_type,
            target_test_model=args.test_model
        )
        
        # Procesar páginas
        all_exams = extractor.process_all_pages()
        
        # Guardar resultados
        extractor.save_results(all_exams)
        
        # Mostrar resumen
        extractor.print_summary(all_exams)
        
        if all_exams:
            print("\\n🎉 ¡Extracción completada exitosamente!")
            
            # Sugerencias de próximos pasos
            print("\\n💡 PRÓXIMOS PASOS:")
            if args.exam_type == 'PER' and args.test_model == 'TEST01':
                print("   1. Revisar: extracted_answers/per_test01_answers.json")
                print("   2. Ejecutar: python madrid_merge_exam.py")
                print("   3. Reiniciar el servidor de la aplicación")
            else:
                print("   1. Revisar los archivos JSON generados en el directorio de salida")
                print("   2. Usar madrid_merge_exam.py para aplicar las respuestas al YAML correspondiente")
        else:
            print("\\n⚠️  No se encontraron exámenes que coincidan con los filtros especificados")
            print("\\n💡 SUGERENCIAS:")
            print("   - Verificar que el PDF contiene el tipo de examen especificado")
            print("   - Probar sin filtros para ver todos los exámenes disponibles:")
            print(f"     python madrid_extract_answers.py --pdf-path '{args.pdf_path}'")
            print("   - Verificar que el nombre del archivo sigue el patrón: comunidad-año-convocatoria.pdf")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        print("\\n❌ Proceso interrumpido por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
