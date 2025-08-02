#!/usr/bin/env python3
"""
Utilidad para extraer páginas de un PDF como imágenes individuales.

Uso:
  pdf_to_images.py --input-file archivo.pdf --output-dir directorio_salida [--pages 3-7]

- Si no se especifica --pages, se extraen todas las páginas.
- Si se especifica un único número (ej: 5), solo se extrae esa página.
- Si se especifica un rango (ej: 3-7), se extraen ambas inclusive.

Requiere PyMuPDF (fitz): pip install pymupdf
"""
import os
import argparse
import fitz  # PyMuPDF


def parse_page_range(pages_str, total_pages):
    """
    Parsea el argumento de rango de páginas y devuelve (inicio, fin) base 1.
    """
    if not pages_str:
        return 1, total_pages
    if '-' in pages_str:
        start, end = pages_str.split('-')
        start = int(start)
        end = int(end)
    else:
        start = int(pages_str)
        end = start
    # Limitar a rango válido
    start = max(1, start)
    end = min(total_pages, end)
    return start, end


def pdf_to_images(pdf_path, output_dir, page_range=None):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    start, end = parse_page_range(page_range, total_pages)
    if start > end:
        print(f"❌ Rango de páginas inválido: {start}-{end}. El PDF solo tiene {total_pages} páginas. No se extraerán imágenes.")
        doc.close()
        return
    print(f"Extrayendo páginas {start}-{end} de {pdf_path} ({total_pages} páginas)")

    os.makedirs(output_dir, exist_ok=True)
    for page_num in range(start, end + 1):
        page = doc[page_num - 1]  # fitz usa base 0
        pix = page.get_pixmap(dpi=200)
        img_path = os.path.join(output_dir, f"pagina-{page_num:02d}.png")
        pix.save(img_path)
        print(f"✅ Guardada página {page_num} en {img_path}")
    doc.close()
    print(f"\n💾 Imágenes guardadas en {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Extrae páginas de un PDF como imágenes individuales.",
        epilog="""
Ejemplos de uso:
  pdf_to_images.py --input-file examen.pdf --output-dir imagenes/
  pdf_to_images.py --input-file examen.pdf --output-dir imagenes/ --pages 3-7
  pdf_to_images.py --input-file examen.pdf --output-dir imagenes/ --pages 5
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input-file", required=True, help="Ruta al archivo PDF de entrada")
    parser.add_argument("--output-dir", required=True, help="Directorio donde guardar las imágenes")
    parser.add_argument("--pages", help="Rango de páginas a extraer (ej: 3-7 o 5)")
    args = parser.parse_args()

    pdf_to_images(args.input_file, args.output_dir, args.pages)


if __name__ == "__main__":
    main()
