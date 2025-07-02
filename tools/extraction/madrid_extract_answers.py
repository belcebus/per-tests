#!/usr/bin/env python3
"""
Script para extraer respuestas del PDF de respuestas oficiales usando OCR

PROPÓSITO:
Este script procesa el PDF de respuestas oficiales (madrid-2025-resp.pdf) y extrae
las respuestas correctas usando OCR (Reconocimiento Óptico de Caracteres).

ESTRUCTURA DEL PDF:
- Cada página contiene respuestas de un tipo de examen específico
- Al inicio de cada página se indica el tipo de examen y modelo
- Las respuestas están numeradas consecutivamente (1, 2, 3, ...)
- Los valores válidos son: a, b, c, d, o "ANULADA"

TIPOS DE EXAMEN SOPORTADOS:
- PER: Patrón de Embarcación de Recreo
- PATRON_YATE: Patrón de Yate  
- CAPITAN_YATE: Capitán de Yate
- LICENCIA_NAVEGACION: Licencia de Nave            # Sugerencias de próximos pasos
            print("\n💡 PRÓXIMOS PASOS:")
            if args.exam_type == 'PER' and args.test_model == 'TEST01':
                new_filename = extractor._generate_output_filename('PER', 'TEST01')
                print(f"   1. Revisar: extracted_answers/{new_filename}")
                print(f"   2. Archivo de compatibilidad: extracted_answers/per_test01_answers.json")
                print("   3. Ejecutar: python madrid_merge_exam.py")
                print("   4. Reiniciar el servidor de la aplicación")
            else:
                print("   1. Revisar los archivos JSON generados en el directorio de salida")
                print("   2. Usar apply_ocr_answers.py para aplicar las respuestas al YAML correspondiente")SO:
# Extraer todas las respuestas de todos los exámenes
python madrid_extract_answers.py

# Extraer respuestas de un tipo específico de examen
python madrid_extract_answers.py --exam-type PER

# Extraer respuestas de un modelo específico
python madrid_extract_answers.py --exam-type PER --test-model TEST01

# Especificar archivo PDF personalizado
python madrid_extract_answers.py --pdf-path "pdfs/otro-examen.pdf" --exam-type PATRON_YATE

PARÁMETROS:
--exam-type: Tipo de examen a extraer (PER, PATRON_YATE, CAPITAN_YATE, LICENCIA_NAVEGACION)
--test-model: Modelo específico del test (TEST01, TEST02, etc.)
--pdf-path: Ruta al archivo PDF (por defecto: pdfs/madrid-2025-resp.pdf)
--output-dir: Directorio de salida (por defecto: extracted_answers)

SALIDA:
- extracted_answers/: Directorio con archivos de texto por página
- extracted_answers/[exam_type]_[test_model]_answers.json: Respuestas específicas
- extracted_answers/exam_answers_complete.json: Todas las respuestas extraídas
"""

from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
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
    
    def __init__(self, pdf_path: str = None, output_dir: str = None, 
                 target_exam_type: Optional[str] = None, target_test_model: Optional[str] = None):
        # Usar configuración global si no se especifica ruta
        if pdf_path is None:
            # Buscar el archivo PDF de respuestas en el directorio de respuestas configurado
            answers_dir = settings.get_raw_answers_path()
            
            # Intentar encontrar el archivo PDF siguiendo el patrón: comunidad-año-convocatoria.pdf
            # Buscar archivos PDF en el directorio
            pdf_files = list(answers_dir.glob("*.pdf"))
            
            if pdf_files:
                # Usar el primer archivo PDF encontrado
                pdf_path = pdf_files[0]
                print(f"📄 Auto-detectado archivo PDF: {pdf_path.name}")
            else:
                # Fallback al nombre por defecto
                pdf_path = answers_dir / "madrid-2025-abril.pdf"
                print(f"📄 Usando archivo por defecto: {pdf_path.name}")
        else:
            pdf_path = Path(pdf_path)
            
        if output_dir is None:
            # Usar directorio configurado para archivos extraídos
            output_dir = settings.get_extracted_path()
        else:
            output_dir = Path(output_dir)
            
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Filtros específicos
        self.target_exam_type = target_exam_type
        self.target_test_model = target_test_model
        
        # Extraer información del PDF para generar nombres de archivo
        self.pdf_info = self._extract_pdf_info_from_name()
        
        # Patrones para detectar tipos de examen
        self.exam_patterns = {
            'PER': [
                r'PATRÓN DE EMBARCACIONES DE RECREO',
                r'PATRON DE EMBARCACIONES DE RECREO',
                r'EMBARCACIONES DE RECREO',
                r'PER'
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
        
        # Patrones para detectar modelos de test
        self.test_patterns = [
            r'CÓDIGO DE TEST\s*(\d+)',
            r'CODIGO DE TEST\s*(\d+)',
            r'TEST\s*(\d+)',
            r'Cdd(\d+)'  # Patrón específico que aparece en el OCR
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
        Mejora la imagen para obtener mejor precisión en el OCR
        """
        # Convertir a escala de grises si no lo está
        if image.mode != 'L':
            image = image.convert('L')
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        # Reducir ruido
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def extract_text_from_pdf(self) -> List[str]:
        """
        Convierte cada página del PDF en imagen y extrae el texto con OCR
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {self.pdf_path}")
        
        print(f"📄 Procesando PDF: {self.pdf_path}")
        print("🔄 Convirtiendo páginas a imágenes...")
        
        # Convertir PDF a imágenes (DPI alto para mejor calidad)
        images = convert_from_path(str(self.pdf_path), dpi=300)
        print(f"✅ {len(images)} páginas convertidas")
        
        extracted_texts = []
        
        for i, image in enumerate(images):
            print(f"🔍 Procesando página {i+1}/{len(images)}...")
            
            # Mejorar imagen para OCR
            enhanced_image = self.enhance_image_for_ocr(image)
            
            # Aplicar OCR con configuración optimizada para texto en español
            try:
                text = pytesseract.image_to_string(
                    enhanced_image,
                    lang='spa+eng',
                    config='--oem 3 --psm 6'
                )
                
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
        
        # Detectar tipo de examen
        exam_type = None
        for exam, patterns in self.exam_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    exam_type = exam
                    break
            if exam_type:
                break
        
        # Detectar modelo de test
        test_model = None
        for pattern in self.test_patterns:
            match = re.search(pattern, text_upper)
            if match:
                test_model = f"TEST{match.group(1).zfill(2)}"
                break
        
        return exam_type, test_model
    
    def extract_answers_from_text(self, text: str) -> Dict[int, str]:
        """
        Extrae las respuestas numeradas del texto de una página
        """
        answers = {}
        lines = text.split('\n')
        
        # Patrones para detectar respuestas numeradas
        answer_patterns = [
            r'^(\d+)\s*([ABCDabcd])(?:\s|$)',  # "1 A", "2 B"
            r'^(\d+)[.\s]*([ABCDabcd])(?:\s|$)',  # "1. A", "2. B"
            r'^(\d+)([ABCDabcd])(?:\s|$)',  # "1A", "2B"
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Buscar respuestas con patrones básicos
            for pattern in answer_patterns:
                match = re.match(pattern, line)
                if match:
                    try:
                        question_num = int(match.group(1))
                        answer = match.group(2).lower()
                        
                        # Validar que es una respuesta válida
                        if answer in ['a', 'b', 'c', 'd'] and 1 <= question_num <= 100:
                            answers[question_num] = answer
                    except (ValueError, IndexError):
                        continue
            
            # Patrón especial para "Cc" -> "c", etc. (errores comunes de OCR)
            cc_pattern = r'^(\d+)\s*(Cc|Aa|Bb|Dd)(?:\s|$)'
            cc_match = re.match(cc_pattern, line)
            if cc_match:
                try:
                    question_num = int(cc_match.group(1))
                    ocr_answer = cc_match.group(2)
                    
                    # Convertir errores de OCR comunes
                    if ocr_answer == 'Cc':
                        answer = 'c'
                    elif ocr_answer == 'Aa':
                        answer = 'a'
                    elif ocr_answer == 'Bb':
                        answer = 'b'
                    elif ocr_answer == 'Dd':
                        answer = 'd'
                    else:
                        continue
                    
                    if 1 <= question_num <= 100:
                        answers[question_num] = answer
                except (ValueError, IndexError):
                    continue
            
            # Patrón especial para errores como "177 2A" -> "17 A"
            error_pattern = r'^(\d{2,3})\s*(\d)([ABCDabcd])(?:\s|$)'
            error_match = re.match(error_pattern, line)
            if error_match:
                try:
                    # Extraer el número correcto: "177" -> "17", "2" -> usar el dígito simple
                    full_num = error_match.group(1)
                    single_digit = int(error_match.group(2))
                    answer = error_match.group(3).lower()
                    
                    # Si el número completo es de 3 dígitos, tomar los primeros 2
                    if len(full_num) == 3:
                        question_num = int(full_num[:2])
                    else:
                        question_num = single_digit
                    
                    if answer in ['a', 'b', 'c', 'd'] and 1 <= question_num <= 100:
                        answers[question_num] = answer
                except (ValueError, IndexError):
                    continue
            
            # Buscar respuestas anuladas
            if re.search(r'anulada|nula', line, re.IGNORECASE):
                # Buscar número de pregunta cerca
                num_match = re.search(r'(\d+)', line)
                if num_match:
                    try:
                        question_num = int(num_match.group(1))
                        if 1 <= question_num <= 100:
                            answers[question_num] = "ANULADA"
                    except ValueError:
                        continue
        
        return answers
    
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
        
        # Extraer texto de todas las páginas
        page_texts = self.extract_text_from_pdf()
        
        all_exams = {}
        
        # Procesar cada página
        for i, text in enumerate(page_texts):
            page_num = i + 1
            print(f"\\n📖 Analizando página {page_num}...")
            
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
                print(f"   📝 Respuestas encontradas: {len(answers)}")
                
                if answers:
                    # Organizar por tipo de examen y modelo
                    if exam_type not in all_exams:
                        all_exams[exam_type] = {}
                    
                    exam_key = test_model or "DEFAULT"
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
        
        return all_exams
    
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
                # Generar nombre de archivo específico
                exam_clean = target_exam.lower().replace('_', '-')
                model_clean = target_model.lower().replace('test', 'test')
                specific_file = self.output_dir / f"{exam_clean}_{model_clean}_answers.json"
                
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
            
            # Archivo específico para PER Test 01 con nuevo patrón de nomenclatura
            if 'PER' in all_exams and 'TEST01' in all_exams['PER']:
                per_test01 = all_exams['PER']['TEST01']
                
                # Generar nombre de archivo siguiendo el nuevo patrón
                new_filename = self._generate_output_filename('PER', 'TEST01')
                per_file_new = self.output_dir / new_filename
                
                # Mantener archivo de compatibilidad con nombre anterior
                per_file_legacy = self.output_dir / "per_test01_answers.json"
                
                per_data = {
                    'exam_type': 'PER',
                    'test_model': 'TEST01',
                    'total_answers': per_test01['total_answers'],
                    'answers': per_test01['answers'],
                    'source_pdf': self.pdf_path.name,
                    'generated_at': per_test01.get('generated_at'),
                    'pdf_info': self.pdf_info
                }
                
                # Guardar con nuevo nombre
                with open(per_file_new, 'w', encoding='utf-8') as f:
                    json.dump(per_data, f, indent=2, ensure_ascii=False)
                print(f"🎯 PER Test 01 (nuevo formato): {per_file_new}")
                
                # Guardar también con nombre legacy para compatibilidad
                with open(per_file_legacy, 'w', encoding='utf-8') as f:
                    json.dump(per_data, f, indent=2, ensure_ascii=False)
                print(f"🎯 PER Test 01 (compatibilidad): {per_file_legacy}")
            
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


def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(
        description="Extractor de respuestas de PDFs de exámenes oficiales usando OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EJEMPLOS DE USO:

  # Extraer todas las respuestas de todos los exámenes
  python madrid_extract_answers.py

  # Extraer respuestas de un tipo específico de examen
  python madrid_extract_answers.py --exam-type PER

  # Extraer respuestas de un modelo específico
  python madrid_extract_answers.py --exam-type PER --test-model TEST01

  # Especificar archivo PDF personalizado
  python madrid_extract_answers.py --pdf-path "pdfs/otro-examen.pdf" --exam-type PATRON_YATE

  # Especificar directorio de salida personalizado
  python madrid_extract_answers.py --output-dir "mis_respuestas" --exam-type PER

TIPOS DE EXAMEN SOPORTADOS:
  - PER: Patrón de Embarcación de Recreo
  - PATRON_YATE: Patrón de Yate  
  - CAPITAN_YATE: Capitán de Yate
  - LICENCIA_NAVEGACION: Licencia de Navegación

MODELOS DE TEST COMUNES:
  - TEST01, TEST02, TEST03, etc.
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
        help='Ruta al archivo PDF de respuestas (default: usar configuración global)'
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
    
    try:
        # Crear extractor con los parámetros especificados (o rutas por defecto)
        extractor = PDFAnswerExtractor(
            pdf_path=args.pdf_path if args.pdf_path else None,  # None usa configuración global
            output_dir=args.output_dir if args.output_dir else None,  # None usa configuración global
            target_exam_type=args.exam_type,
            target_test_model=args.test_model
        )
        
        # Verificar que el archivo PDF existe
        if not extractor.pdf_path.exists():
            print(f"❌ Error: El archivo PDF no existe: {extractor.pdf_path}")
            print("💡 Verifica la ruta del archivo PDF")
            print(f"💡 Directorio esperado: {settings.get_raw_answers_path()}")
            print(f"💡 Patrón de nombre esperado: comunidad-año-convocatoria.pdf (ej: madrid-2025-abril.pdf)")
            return 1
        
        print(f"📄 Usando archivo PDF: {extractor.pdf_path}")
        print(f"📁 Directorio salida: {extractor.output_dir}")
        
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
            return 1
            
        return 0
        
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
