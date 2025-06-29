#!/usr/bin/env python3
"""
Explorador simple de PDFs para entender la estructura exacta
"""

import fitz  # PyMuPDF
import re

def explore_pdf_content():
    """Explora el contenido real de los PDFs para entender su estructura"""
    
    # Analizar archivo de preguntas
    print("🔍 ANALIZANDO ARCHIVO DE PREGUNTAS")
    print("="*50)
    
    with fitz.open("pdfs/madrid-2025.pdf") as doc:
        print(f"Total páginas: {len(doc)}")
        
        # Analizar primeras páginas más a fondo
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            
            print(f"\n--- PÁGINA {page_num + 1} ---")
            print(f"Caracteres: {len(text)}")
            
            # Mostrar todo el texto de las primeras páginas
            if page_num < 3:
                print("CONTENIDO COMPLETO:")
                print(repr(text))  # usar repr para ver caracteres especiales
                print("\n" + "="*50)
    
    print("\n🔍 ANALIZANDO ARCHIVO DE RESPUESTAS")
    print("="*50)
    
    with fitz.open("pdfs/madrid-2025-resp.pdf") as doc:
        print(f"Total páginas: {len(doc)}")
        
        # Mostrar primera página completa
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            print("PÁGINA 1 - CONTENIDO COMPLETO:")
            print(repr(text))

if __name__ == "__main__":
    explore_pdf_content()
