
"""
Extrae texto de todas las imágenes PNG de un directorio y lo vuelca en un único fichero de texto.

Uso:
  images_to_single_text.py --input-dir directorio_imagenes --output nombre_salida.txt

- Procesa todos los archivos .png del directorio indicado.
- El texto de todas las imágenes se guarda en un único archivo de salida.

Requiere pytesseract y Pillow:
  pip install pytesseract pillow
Además, requiere tener instalado Tesseract OCR en el sistema.
"""
import os
import argparse
from PIL import Image
import pytesseract


def extract_text_to_single_file(input_dir, output_file):

    import re

    def page_number(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else float('inf')

    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    files = sorted(files, key=page_number)
    if not files:
        print(f"No se encontraron imágenes PNG en {input_dir}")
        return
    with open(output_file, 'w', encoding='utf-8') as fout:
        for filename in files:
            img_path = os.path.join(input_dir, filename)
            print(f"Procesando {filename} ...", end=' ')
            try:
                image = Image.open(img_path)
                text = pytesseract.image_to_string(image, lang='spa')
                fout.write(text.strip())
                fout.write("\n\n")
                print("✅")
            except Exception as e:
                print(f"❌ Error: {e}")
    print(f"\n💾 Texto de todas las imágenes guardado en {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extrae texto de imágenes PNG en un directorio y lo guarda en un único archivo .txt.",
        epilog="""
Ejemplo de uso:
  images_to_single_text.py --input-dir imagenes/ --output examen.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directorio con las imágenes PNG a procesar"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Nombre del archivo de salida (ej: examen.txt)"
    )
    args = parser.parse_args()
    extract_text_to_single_file(args.input_dir, args.output)


if __name__ == "__main__":
    main()
