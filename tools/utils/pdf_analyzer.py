#!/usr/bin/env python3
"""
Analizador de PDFs de exámenes PER

Este script analiza los PDFs oficiales de exámenes para entender su estructura
y preparar la extracción automatizada de preguntas y respuestas.
"""

import fitz  # PyMuPDF
import pdfplumber
import re
from pathlib import Path
from typing import Dict, List, Any

class PDFAnalyzer:
    """
    Analizador de PDFs de exámenes oficiales.
    
    Analiza la estructura y formato de los documentos para diseñar
    el pipeline de extracción más apropiado.
    """
    
    def __init__(self, pdf_questions_path: str, pdf_answers_path: str):
        """
        Inicializa el analizador con las rutas de los PDFs.
        
        Args:
            pdf_questions_path: Ruta al PDF con las preguntas
            pdf_answers_path: Ruta al PDF con las respuestas
        """
        self.pdf_questions_path = Path(pdf_questions_path)
        self.pdf_answers_path = Path(pdf_answers_path)
        
    def analyze_questions_pdf(self) -> Dict[str, Any]:
        """
        Analiza el PDF de preguntas para entender su estructura.
        
        Returns:
            Diccionario con información sobre la estructura del PDF
        """
        print("🔍 Analizando PDF de preguntas...")
        
        analysis = {
            "total_pages": 0,
            "sample_content": [],
            "page_structure": [],
            "detected_patterns": []
        }
        
        # Análisis con PyMuPDF
        with fitz.open(self.pdf_questions_path) as doc:
            analysis["total_pages"] = len(doc)
            
            # Analizar las primeras 3 páginas para entender la estructura
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                
                page_info = {
                    "page": page_num + 1,
                    "text_length": len(text),
                    "first_100_chars": text[:100],
                    "contains_exam_types": self._detect_exam_types(text),
                    "question_markers": self._detect_question_markers(text)
                }
                
                analysis["page_structure"].append(page_info)
                
                # Guardar muestra de contenido de la primera página
                if page_num == 0:
                    analysis["sample_content"] = text[:1000].split('\n')
        
        # Análisis con pdfplumber para mejor detección de estructura
        with pdfplumber.open(self.pdf_questions_path) as pdf:
            first_page = pdf.pages[0]
            
            # Intentar detectar tablas
            tables = first_page.extract_tables()
            if tables:
                analysis["detected_patterns"].append("tables_detected")
            
            # Obtener información de layout
            analysis["page_layout"] = {
                "width": first_page.width,
                "height": first_page.height,
                "chars_count": len(first_page.chars) if first_page.chars else 0
            }
        
        return analysis
    
    def analyze_answers_pdf(self) -> Dict[str, Any]:
        """
        Analiza el PDF de respuestas para entender su estructura.
        
        Returns:
            Diccionario con información sobre la estructura del PDF
        """
        print("🔍 Analizando PDF de respuestas...")
        
        analysis = {
            "total_pages": 0,
            "sample_content": [],
            "answer_patterns": []
        }
        
        with fitz.open(self.pdf_answers_path) as doc:
            analysis["total_pages"] = len(doc)
            
            # Analizar primera página
            if len(doc) > 0:
                page = doc[0]
                text = page.get_text()
                
                analysis["sample_content"] = text[:1000].split('\n')
                analysis["answer_patterns"] = self._detect_answer_patterns(text)
        
        return analysis
    
    def _detect_exam_types(self, text: str) -> List[str]:
        """Detecta tipos de examen mencionados en el texto."""
        exam_types = []
        
        patterns = {
            "PER": r"(?i)(PER|patrón.*embarcación.*recreo)",
            "PATRON_YATE": r"(?i)(patrón.*yate|PY)",
            "CAPITAN_YATE": r"(?i)(capitán.*yate|CY)"
        }
        
        for exam_type, pattern in patterns.items():
            if re.search(pattern, text):
                exam_types.append(exam_type)
        
        return exam_types
    
    def _detect_question_markers(self, text: str) -> List[str]:
        """Detecta marcadores de preguntas en el texto."""
        markers = []
        
        # Buscar patrones comunes de numeración de preguntas
        question_patterns = [
            r"\b\d+\.\s",  # "1. ", "2. ", etc.
            r"\b\d+\)\s",  # "1) ", "2) ", etc.
            r"Pregunta\s+\d+",  # "Pregunta 1", "Pregunta 2", etc.
            r"\d+\.-",  # "1.-", "2.-", etc.
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text)
            if matches:
                markers.append(f"Pattern '{pattern}': {len(matches)} matches")
        
        return markers
    
    def _detect_answer_patterns(self, text: str) -> List[str]:
        """Detecta patrones de respuestas en el texto."""
        patterns = []
        
        # Buscar patrones de respuestas
        answer_patterns = [
            r"[ABCD]",  # Respuestas tipo A, B, C, D
            r"\d+[.-]\s*[ABCD]",  # "1. A", "1- B", etc.
            r"Respuesta[s]?",  # "Respuesta" o "Respuestas"
        ]
        
        for pattern in answer_patterns:
            matches = re.findall(pattern, text)
            if matches:
                patterns.append(f"Pattern '{pattern}': {len(matches)} matches")
        
        return patterns
    
    def extract_sample_questions(self, num_questions: int = 3) -> List[Dict]:
        """
        Extrae algunas preguntas de muestra para análisis manual.
        
        Args:
            num_questions: Número de preguntas a extraer
            
        Returns:
            Lista de diccionarios con información de preguntas
        """
        print(f"📝 Extrayendo {num_questions} preguntas de muestra...")
        
        sample_questions = []
        
        with fitz.open(self.pdf_questions_path) as doc:
            full_text = ""
            
            # Extraer texto de todas las páginas
            for page in doc:
                full_text += page.get_text() + "\n"
            
            # Intentar extraer preguntas usando patrones
            # Este es un análisis inicial, luego refinamos según la estructura real
            question_pattern = r"(\d+\.\s*.+?)(?=\d+\.\s|$)"
            questions = re.findall(question_pattern, full_text, re.DOTALL)
            
            for i, question_text in enumerate(questions[:num_questions]):
                sample_questions.append({
                    "question_number": i + 1,
                    "raw_text": question_text.strip()[:500],  # Primeros 500 chars
                    "length": len(question_text)
                })
        
        return sample_questions
    
    def generate_analysis_report(self) -> str:
        """
        Genera un reporte completo del análisis de ambos PDFs.
        
        Returns:
            Reporte en formato de texto
        """
        print("📊 Generando reporte de análisis...")
        
        questions_analysis = self.analyze_questions_pdf()
        answers_analysis = self.analyze_answers_pdf()
        sample_questions = self.extract_sample_questions()
        
        report = f"""
# 📋 REPORTE DE ANÁLISIS DE PDFs DE EXÁMENES

## 📄 PDF de Preguntas: {self.pdf_questions_path.name}
- **Total de páginas**: {questions_analysis['total_pages']}
- **Tipos de examen detectados**: {', '.join(set(sum([page['contains_exam_types'] for page in questions_analysis['page_structure']], [])))}
- **Patrones detectados**: {', '.join(questions_analysis['detected_patterns'])}

### Estructura por página:
"""
        
        for page_info in questions_analysis['page_structure']:
            report += f"""
**Página {page_info['page']}:**
- Longitud de texto: {page_info['text_length']} caracteres
- Tipos de examen: {', '.join(page_info['contains_exam_types']) if page_info['contains_exam_types'] else 'Ninguno detectado'}
- Marcadores de preguntas: {len(page_info['question_markers'])} encontrados
- Primeros 100 caracteres: "{page_info['first_100_chars']}"
"""
        
        report += f"""

### Muestra de contenido (página 1):
```
{chr(10).join(questions_analysis['sample_content'][:10])}
```

## 📄 PDF de Respuestas: {self.pdf_answers_path.name}
- **Total de páginas**: {answers_analysis['total_pages']}
- **Patrones de respuestas detectados**: {len(answers_analysis['answer_patterns'])}

### Muestra de contenido:
```
{chr(10).join(answers_analysis['sample_content'][:10])}
```

## 🔍 Preguntas de Muestra Extraídas:
"""
        
        for i, question in enumerate(sample_questions):
            report += f"""
### Pregunta {question['question_number']}:
```
{question['raw_text']}
```
(Longitud total: {question['length']} caracteres)
"""
        
        report += """

## 🎯 Recomendaciones para el Pipeline:

1. **Estrategia de extracción**: Basado en el análisis, recomiendo usar [se determinará según los resultados]
2. **Patrones identificados**: [se determinará según los resultados]
3. **Puntos de atención**: [se determinará según los resultados]
"""
        
        return report


def main():
    """Función principal para ejecutar el análisis."""
    print("🚢 Analizador de PDFs de Exámenes PER")
    print("=" * 50)
    
    # Rutas de los PDFs
    questions_pdf = "/workspaces/per-tests/pdfs/madrid-2025.pdf"
    answers_pdf = "/workspaces/per-tests/pdfs/madrid-2025-resp.pdf"
    
    # Verificar que los archivos existen
    if not Path(questions_pdf).exists():
        print(f"❌ No se encontró el archivo: {questions_pdf}")
        return
    
    if not Path(answers_pdf).exists():
        print(f"❌ No se encontró el archivo: {answers_pdf}")
        return
    
    # Crear analizador y ejecutar análisis
    analyzer = PDFAnalyzer(questions_pdf, answers_pdf)
    
    try:
        report = analyzer.generate_analysis_report()
        
        # Guardar reporte
        report_path = "/workspaces/per-tests/pdf_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Análisis completado!")
        print(f"📋 Reporte guardado en: {report_path}")
        print("\n" + "=" * 50)
        print("RESUMEN DEL REPORTE:")
        print("=" * 50)
        print(report[:1500] + "..." if len(report) > 1500 else report)
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
