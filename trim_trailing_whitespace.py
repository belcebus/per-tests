import sys

if len(sys.argv) != 2:
    print("Uso: python trim_trailing_whitespace.py <ruta_al_fichero>")
    sys.exit(1)

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(file_path, 'w', encoding='utf-8') as f:
    for line in lines:
        f.write(line.rstrip() + '\n')