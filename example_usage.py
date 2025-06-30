#!/usr/bin/env python3
"""
Script de ejemplo para extraer exámenes con diferentes configuraciones
Demuestra cómo usar el extractor parametrizable con metadatos completos
"""

import sys
import os
sys.path.append('/workspaces/per-tests/tools')

from parametric_exam_extractor import ParametricExamExtractor, create_per_pattern

def extract_madrid_2025_test01():
    """Extrae el examen de Madrid 2025 Test 01"""
    extractor = ParametricExamExtractor()
    
    # Crear patrón usando la función helper
    pattern = create_per_pattern("Madrid", 2025, "Ordinaria", "Test01")
    
    # Rutas de PDFs
    pdf_questions = "/workspaces/per-tests/pdfs/madrid-2025.pdf"
    pdf_answers = "/workspaces/per-tests/pdfs/madrid-2025-resp.pdf"
    
    # Extraer
    exam_data = extractor.extract_exam(pdf_questions, pdf_answers, pattern)
    
    if exam_data:
        # Generar nombre automático
        output_path = extractor.generate_filename(pattern, "/workspaces/per-tests/data")
        extractor.save_to_yaml(exam_data, output_path)
        print(f"✅ Examen extraído y guardado en: {output_path}")
        return output_path
    else:
        print("❌ Error al extraer el examen")
        return None

def extract_madrid_2025_test03():
    """Ejemplo para extraer el Test 03 (si estuviera disponible)"""
    extractor = ParametricExamExtractor()
    
    # Crear patrón para Test 03
    pattern = create_per_pattern("Madrid", 2025, "Ordinaria", "Test03")
    
    print(f"🔧 Patrón configurado para:")
    print(f"   Comunidad: {pattern.community}")
    print(f"   Año: {pattern.year}")
    print(f"   Convocatoria: {pattern.call}")
    print(f"   Test: {pattern.test_code}")
    print(f"   Archivo generado sería: {extractor.generate_filename(pattern)}")

def example_other_communities():
    """Ejemplos de configuraciones para otras comunidades"""
    extractor = ParametricExamExtractor()
    
    examples = [
        ("Valencia", 2024, "Junio", "Test02"),
        ("Barcelona", 2023, "Extraordinaria", "Test01"),
        ("Andalucía", 2025, "Febrero", "Test01"),
        ("Galicia", 2024, "Septiembre", "Test03")
    ]
    
    print("📋 Ejemplos de configuraciones para otras comunidades:")
    for community, year, call, test_code in examples:
        pattern = create_per_pattern(community, year, call, test_code)
        filename = extractor.generate_filename(pattern)
        print(f"   {community} {year} {call} {test_code} → {os.path.basename(filename)}")

if __name__ == "__main__":
    print("🚢 Ejemplos de uso del extractor parametrizable")
    print("=" * 60)
    
    # Extraer el examen actual
    print("\n1. Extrayendo examen de Madrid 2025:")
    extract_madrid_2025_test01()
    
    # Mostrar ejemplo de Test 03
    print("\n2. Ejemplo de configuración para Test 03:")
    extract_madrid_2025_test03()
    
    # Mostrar ejemplos para otras comunidades
    print("\n3. Ejemplos para otras comunidades:")
    example_other_communities()
    
    print(f"\n✅ Para extraer un nuevo examen:")
    print(f"   1. Crear patrón: pattern = create_per_pattern('Comunidad', año, 'Convocatoria', 'TestXX')")
    print(f"   2. Usar extractor: extractor.extract_exam(pdf_preguntas, pdf_respuestas, pattern)")
    print(f"   3. El archivo se guardará automáticamente con el nombre apropiado")
