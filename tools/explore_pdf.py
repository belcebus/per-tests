#!/usr/bin/env python3
"""
Script para explorar el contenido del PDF y encontrar los patrones correctos.
"""

import fitz  # PyMuPDF
import re

def explore_pdf_content(pdf_path: str):
    """Explora el contenido del PDF para entender su estructura."""
    print(f"Explorando contenido de {pdf_path}")
    doc = fitz.open(pdf_path)
    
    for page_num in range(min(10, len(doc))):  # Primeras 10 páginas
        page = doc.load_page(page_num)
        text = page.get_text()
        
        print(f"\n=== PÁGINA {page_num + 1} ===")
        # Buscar menciones de PER, patrón, embarcación
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['per', 'patrón', 'embarcación', 'recreo', 'modelo']):
                # Mostrar contexto (línea anterior, actual, siguiente)
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context_lines = lines[start:end]
                print(f"Línea {i}: {' | '.join(context_lines)}")
    
    doc.close()

def main():
    pdf_path = "/workspaces/per-tests/pdfs/madrid-2025.pdf"
    explore_pdf_content(pdf_path)

if __name__ == "__main__":
    main()
