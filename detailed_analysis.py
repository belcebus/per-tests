#!/usr/bin/env python3
import fitz
import re

# Leer PDF
doc = fitz.open("/workspaces/per-tests/pdfs/madrid-2025-resp.pdf")
text = ""
for page in doc:
    text += page.get_text() + "\n"
doc.close()

print("🔍 ANÁLISIS DETALLADO DEL FORMATO DE RESPUESTAS")
print("=" * 60)

# Analizar específicamente el Test 01
pattern_01 = r"Respuestas\s+al\s+EXAMEN\s+DE\s+PATRÓN\s+DE\s+EMBARCACIONES\s+DE\s+RECREO\s*Código\s+de\s+Test\s+01"
match_01 = re.search(pattern_01, text, re.IGNORECASE | re.DOTALL)

if match_01:
    print("✅ Test 01 encontrado")
    start_pos = match_01.end()
    
    # Encontrar final del Test 01
    end_pattern = r"Respuestas\s+al\s+EXAMEN\s+DE\s+PATRÓN\s+DE\s+EMBARCACIONES\s+DE\s+RECREO\s*Código\s+de\s+Test\s+02"
    end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)
    
    if end_match:
        end_pos = start_pos + end_match.start()
        test_01_section = text[start_pos:end_pos]
    else:
        lines_after_start = text[start_pos:].split('\n')[:100]
        test_01_section = '\n'.join(lines_after_start)
    
    print(f"📊 Sección Test 01 completa:")
    print("-" * 40)
    lines = test_01_section.split('\n')
    
    # Mostrar líneas alrededor de la pregunta 42
    for i, line in enumerate(lines):
        if line.strip() and (i >= 35):  # Mostrar desde la línea 35 en adelante
            print(f"Línea {i:2d}: '{line}'")
            if i > 50:  # Limitar salida
                break
    
    print("-" * 40)
    
    # Buscar patrones de anulación
    print("\n🔍 Buscando patrones de anulación:")
    anulada_patterns = [
        r'(\d+)\s+ANULADA',
        r'ANULADA.*(\d+)',
        r'(\d+).*ANULADA',
        r'\d+\s*\n\s*ANULADA'
    ]
    
    for pattern in anulada_patterns:
        matches = re.findall(pattern, test_01_section, re.IGNORECASE | re.MULTILINE)
        if matches:
            print(f"  Patrón '{pattern}': {matches}")

print("\n" + "=" * 60)
print("🔍 ANÁLISIS GENERAL DE TODOS LOS TESTS")

# Buscar todas las apariciones de "ANULADA" en el PDF completo
anulada_matches = re.finditer(r'[^\n]*ANULADA[^\n]*', text, re.IGNORECASE)
print(f"\n📋 Todas las apariciones de 'ANULADA' en el PDF:")
for i, match in enumerate(anulada_matches):
    context_start = max(0, match.start() - 50)
    context_end = min(len(text), match.end() + 50)
    context = text[context_start:context_end].replace('\n', ' ')
    print(f"  {i+1}. '{context}'")

print(f"\n✅ Análisis detallado completado")
