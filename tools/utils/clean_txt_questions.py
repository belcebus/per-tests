# Script para limpiar y formatear el archivo TXT de preguntas
# Elimina líneas en blanco e inserta una línea en blanco antes de cada línea que empieza por número y espacio

import re
import argparse

parser = argparse.ArgumentParser(description="Limpia y formatea un archivo TXT de preguntas.")
parser.add_argument("input_path", help="Ruta al archivo de entrada")
parser.add_argument("output_path", help="Ruta al archivo de salida")
args = parser.parse_args()
input_path = args.input_path
output_path = args.output_path
with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
    prev_was_number = False
    for line in fin:
        stripped = line.rstrip("\n")
        if not stripped:
            continue  # Elimina líneas en blanco
        if re.match(r"^\d+ ", stripped):
            fout.write("\n")  # Inserta línea en blanco antes de pregunta
        fout.write(stripped + "\n")
