#!/usr/bin/env python3
"""
Demostración del sistema mejorado de extracción de exámenes PER
con metadatos completos y nomenclatura automática
"""

import yaml
import os
from pathlib import Path

def show_file_comparison():
    """Compara el archivo antiguo con el nuevo para mostrar las mejoras"""
    
    print("🔍 COMPARACIÓN DE ARCHIVOS GENERADOS")
    print("=" * 60)
    
    # Archivo antiguo
    old_file = "/workspaces/per-tests/data/per_test_01.yaml"
    new_file = "/workspaces/per-tests/data/per_madrid_2025_ordinaria_test01.yaml"
    
    if os.path.exists(old_file):
        with open(old_file, 'r', encoding='utf-8') as f:
            old_data = yaml.safe_load(f)
        
        print("📄 ARCHIVO ANTERIOR:")
        print(f"   Nombre: {os.path.basename(old_file)}")
        print(f"   Metadatos en exam_info:")
        old_info = old_data.get('exam_info', {})
        for key, value in old_info.items():
            print(f"     {key}: {value}")
    
    print()
    
    if os.path.exists(new_file):
        with open(new_file, 'r', encoding='utf-8') as f:
            new_data = yaml.safe_load(f)
        
        print("📄 ARCHIVO NUEVO:")
        print(f"   Nombre: {os.path.basename(new_file)}")
        print(f"   Metadatos en exam_info:")
        new_info = new_data.get('exam_info', {})
        for key, value in new_info.items():
            print(f"     {key}: {value}")

def show_naming_examples():
    """Muestra ejemplos de la nueva nomenclatura"""
    
    print("\n📝 EJEMPLOS DE NOMENCLATURA AUTOMÁTICA")
    print("=" * 60)
    
    examples = [
        {
            'community': 'Madrid',
            'year': 2025,
            'call': 'Ordinaria',
            'test_code': 'Test01',
            'filename': 'per_madrid_2025_ordinaria_test01.yaml'
        },
        {
            'community': 'Valencia',
            'year': 2024,
            'call': 'Junio',
            'test_code': 'Test02',
            'filename': 'per_valencia_2024_junio_test02.yaml'
        },
        {
            'community': 'Barcelona',
            'year': 2023,
            'call': 'Extraordinaria',
            'test_code': 'Test01',
            'filename': 'per_barcelona_2023_extraordinaria_test01.yaml'
        },
        {
            'community': 'Andalucía',
            'year': 2025,
            'call': 'Febrero',
            'test_code': 'Test03',
            'filename': 'per_andalucía_2025_febrero_test03.yaml'
        }
    ]
    
    for example in examples:
        print(f"🏛️  {example['community']} {example['year']} - {example['call']} - {example['test_code']}")
        print(f"   → {example['filename']}")
        print()

def show_advantages():
    """Muestra las ventajas del nuevo sistema"""
    
    print("✅ VENTAJAS DEL NUEVO SISTEMA")
    print("=" * 60)
    
    advantages = [
        "📂 Nomenclatura automática y consistente",
        "🏛️  Identificación clara de la comunidad autónoma",
        "📅 Año de realización del examen incluido",
        "📢 Convocatoria específica (Ordinaria, Extraordinaria, etc.)",
        "🔢 Código de test para diferenciar múltiples versiones",
        "🔍 Búsqueda y filtrado fácil por metadatos",
        "📊 Organización automática de archivos",
        "🔄 Reutilizable para cualquier examen oficial",
        "🛡️  Compatibilidad con archivos existentes",
        "⚡ Generación automática de nombres únicos"
    ]
    
    for advantage in advantages:
        print(f"   {advantage}")

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    
    print(f"\n🚀 INSTRUCCIONES DE USO")
    print("=" * 60)
    
    print("1. Para extraer un nuevo examen:")
    print("   ```python")
    print("   from parametric_exam_extractor import create_per_pattern, ParametricExamExtractor")
    print("   ")
    print("   # Crear patrón")
    print("   pattern = create_per_pattern('Madrid', 2025, 'Ordinaria', 'Test01')")
    print("   ")
    print("   # Extraer")
    print("   extractor = ParametricExamExtractor()")
    print("   exam_data = extractor.extract_exam(pdf_preguntas, pdf_respuestas, pattern)")
    print("   ")
    print("   # Guardar con nombre automático")
    print("   output_path = extractor.generate_filename(pattern)")
    print("   extractor.save_to_yaml(exam_data, output_path)")
    print("   ```")
    print()
    print("2. Estructura de directorios resultante:")
    print("   data/")
    print("   ├── per_madrid_2025_ordinaria_test01.yaml")
    print("   ├── per_valencia_2024_junio_test02.yaml")
    print("   ├── per_barcelona_2023_extraordinaria_test01.yaml")
    print("   └── ...")

if __name__ == "__main__":
    print("🚢 SISTEMA MEJORADO DE EXTRACCIÓN DE EXÁMENES PER")
    print("=" * 80)
    
    show_file_comparison()
    show_naming_examples()
    show_advantages()
    show_usage_instructions()
    
    print(f"\n🎉 El sistema está listo para extraer exámenes de cualquier")
    print(f"   comunidad autónoma con nomenclatura automática y metadatos completos!")
