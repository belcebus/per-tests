#!/usr/bin/env python3
"""
Script para mostrar todas las líneas completas que contienen "42"
"""

import fitz

def show_all_42_lines():
    print("🔍 ANALIZANDO TODAS LAS LÍNEAS CON '42' EN EL PDF DE RESPUESTAS")
    print("=" * 80)
    
    # Leer PDF de respuestas
    pdf_path = "/workspaces/per-tests/pdfs/madrid-2025-resp.pdf"
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    
    # Dividir en líneas
    all_lines = text.split('\n')
    
    # Buscar todas las líneas que contienen "42"
    lines_with_42 = []
    for i, line in enumerate(all_lines):
        if '42' in line:
            lines_with_42.append((i, line))
    
    print(f"📊 Total de líneas encontradas con '42': {len(lines_with_42)}")
    print("\n" + "=" * 80)
    
    # Mostrar cada línea completa
    for count, (line_num, line) in enumerate(lines_with_42, 1):
        print(f"\n🔍 LÍNEA {count} de {len(lines_with_42)} (Línea PDF #{line_num}):")
        print(f"Longitud: {len(line)} caracteres")
        print("=" * 40)
        print(f"CONTENIDO COMPLETO:")
        print(f"'{line}'")
        print("=" * 40)
        
        # Verificar si contiene "ANULADA"
        if 'anulada' in line.lower():
            print("⚠️  *** ESTA LÍNEA CONTIENE 'ANULADA' ***")
        
        # Mostrar análisis de caracteres
        if line.strip():
            words = line.split()
            print(f"Palabras en la línea: {len(words)}")
            print(f"Primeras 10 palabras: {words[:10]}")
            if len(words) > 10:
                print(f"Últimas 5 palabras: {words[-5:]}")
        
        print("-" * 80)
    
    print(f"\n✅ Análisis completado. {len(lines_with_42)} líneas analizadas.")

if __name__ == "__main__":
    show_all_42_lines()
