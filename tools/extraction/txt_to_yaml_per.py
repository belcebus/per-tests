#!/usr/bin/env python3
"""
Convierte un fichero TXT de exámenes PER en uno o varios ficheros YAML con la estructura oficial.

Uso:
  txt_to_yaml_per.py --input-file extracted-answers/madrid-2019-diciembre.txt --output-dir data/exams/questions/madrid/2019/

Requiere PyYAML: pip install pyyaml
"""
import os
import re
import argparse
from pathlib import Path

# Literales de categorías (orden y nombre exacto)
CATEGORIES = [
    "Nomenclatura náutica",
    "Elementos de amarre y fondeo",
    "Seguridad",
    "Legislación",
    "Balizamiento",
    "Reglamento (RIPA)",
    "Maniobra y navegación",
    "Emergencias en la mar",
    "Meteorología",
    "Teoría de la navegación",
    "Carta de navegación",
]

CATEGORY_MAP = {c.lower().replace('.', '').replace(',', ''): i + 1 for i, c in enumerate(CATEGORIES)}

# Utilidad para limpiar y normalizar literales de categoría


def normalize_category(line):
    return line.strip().lower().replace('.', '').replace(',', '')

# Utilidad para extraer la parte "madrid-2029-diciembre" del nombre del txt


def extract_exam_id(txt_path):
    stem = Path(txt_path).stem
    # Busca madrid-2029-diciembre
    m = re.search(r'(madrid-\d{4}-[a-z]+)', stem)
    return m.group(1) if m else stem

# Utilidad para extraer el número de test


def extract_test_code(line):
    m = re.search(r'c[oó]digo de test\s*(\d+)', line, re.IGNORECASE)
    return m.group(1) if m else None

# Parseo principal


def parse_txt_to_yaml(input_file, output_dir):

    from collections import OrderedDict
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.rstrip() for line in f]

    exams = []
    i = 0
    while i < len(lines):
        if lines[i].strip().upper().startswith("EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"):
            # Buscar código de test
            j = i + 1
            while j < len(lines) and not extract_test_code(lines[j]):
                j += 1
            test_code = extract_test_code(lines[j])
            exam_start = j + 1
            # Buscar siguiente examen o EOF
            exam_end = len(lines)
            for k in range(j + 1, len(lines)):
                if lines[k].strip().upper().startswith("EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"):
                    exam_end = k
                    break
            exams.append((test_code, lines[exam_start:exam_end]))
            i = exam_end
        else:
            i += 1

    exam_id = extract_exam_id(input_file)
    for test_code, exam_lines in exams:
        categories = OrderedDict()
        current_cat_idx = 0
        current_cat = CATEGORIES[current_cat_idx]
        current_cat_id = CATEGORY_MAP.get(current_cat.lower().replace('.', '').replace(',', ''))
        current_questions = []
        question_buffer = []
        question_id = 1  # Global para todo el examen
        option_re = re.compile(r'^[abcd]\)', re.IGNORECASE)
        # Número oficial de preguntas por categoría PER (orden CATEGORIES)
        QUESTIONS_PER_CATEGORY = [4, 2, 4, 2, 5, 10, 2, 3, 4, 5, 4]
        cat_question_count = 0
        for line in exam_lines:
            # Detectar inicio de pregunta
            is_question_start = re.match(r'^(\d{1,2}) ', line)
            # Ignorar líneas de categoría intercaladas (no afectan a la segmentación)
            cat_line_norm = line.strip().lower().replace('.', '').replace(',', '')
            is_cat_line = cat_line_norm in [c.lower().replace('.', '').replace(',', '') for c in CATEGORIES]
            if is_cat_line:
                continue
            if is_question_start:
                if question_buffer and any(q_line.strip() for q_line in question_buffer):
                    q = parse_question_block(question_buffer, current_cat_id, current_cat, question_id, option_re)
                    if q['question'] or q['options']:
                        current_questions.append(q)
                        question_id += 1
                        cat_question_count += 1
                        # Forzar cambio de categoría si se alcanza el número oficial
                        if current_cat_idx < len(QUESTIONS_PER_CATEGORY) and cat_question_count >= QUESTIONS_PER_CATEGORY[current_cat_idx]:
                            categories[current_cat_id] = {
                                'name': current_cat,
                                'questions': current_questions
                            }
                            current_cat_idx += 1
                            if current_cat_idx < len(CATEGORIES):
                                current_cat = CATEGORIES[current_cat_idx]
                                current_cat_id = CATEGORY_MAP.get(current_cat.lower().replace('.', '').replace(',', ''))
                                current_questions = []
                                cat_question_count = 0
                question_buffer = []
            if question_buffer or line.strip():
                question_buffer.append(line)
        # Última pregunta
        if question_buffer and any(q_line.strip() for q_line in question_buffer):
            q = parse_question_block(question_buffer, current_cat_id, current_cat, question_id, option_re)
            if q['question'] or q['options']:
                current_questions.append(q)
        # Añadir última categoría
        if current_cat is not None and current_questions:
            categories[current_cat_id] = {
                'name': current_cat,
                'questions': current_questions
            }
        # Construir exam_info
        # Extraer info del nombre y cabecera
        import yaml

        class OrderedDumper(yaml.SafeDumper):
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_dict(data.items())
        OrderedDumper.add_representer(OrderedDict, _dict_representer)

        # --- Añadir representador para forzar comillas dobles SOLO en las opciones ---
        class DoubleQuotedStr(str):
            pass

        def double_quoted_str_representer(dumper, data):
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
        OrderedDumper.add_representer(DoubleQuotedStr, double_quoted_str_representer)

        def quote_options_only(obj):
            # Recursivo: solo aplica DoubleQuotedStr a los valores de 'options' en cada pregunta
            if isinstance(obj, dict):
                new_obj = {}
                for k, v in obj.items():
                    if k == 'options' and isinstance(v, dict):
                        # Solo los valores de las opciones, quitando espacios finales
                        new_obj[k] = {ok: DoubleQuotedStr(ov.rstrip()) for ok, ov in v.items()}
                    else:
                        new_obj[k] = quote_options_only(v)
                return new_obj
            elif isinstance(obj, list):
                return [quote_options_only(i) for i in obj]
            else:
                return obj

        # Inferir campos básicos
        comunidad = 'Madrid'
        year = None
        call = None
        test_code = test_code.lower() if test_code else ''
        title = 'EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO'
        subtitle = f'Código de Test {test_code.zfill(2)}' if test_code else ''
        total_questions = sum(len(cat['questions']) for cat in categories.values())
        expected_questions = 45
        categories_count = len(categories)
        # Buscar año y convocatoria en el nombre del archivo
        m = re.search(r'(\d{4})-([a-z]+)', exam_id)
        if m:
            year = int(m.group(1))
            call = m.group(2)
        # exam_info ordenado
        exam_info = OrderedDict([
            ('call', call),
            ('categories', categories_count),
            ('community', comunidad),
            ('expected_questions', expected_questions),
            ('questions_with_answers', 0),
            ('subtitle', subtitle),
            ('test_code', test_code),
            ('title', title),
            ('total_questions', total_questions),
            ('year', year),
        ])
        # Construir estructura YAML
        yaml_data = OrderedDict([
            ('categories', categories),
            ('exam_info', exam_info),
        ])
        out_name = f"per-test{test_code}-{exam_id}.yaml"
        out_path = os.path.join(output_dir, out_name)
        yaml_data_quoted = quote_options_only(yaml_data)
        with open(out_path, 'w', encoding='utf-8') as fout:
            yaml.dump(yaml_data_quoted, fout, allow_unicode=True, sort_keys=False, Dumper=OrderedDumper)
        print(f"✅ Generado: {out_path}")


def parse_question_block(lines, cat_id, cat_name, qid, option_re):
    # lines: bloque de líneas de una pregunta
    # Devuelve dict con estructura YAML
    from collections import OrderedDict
    question_lines = []
    options = {}
    current_opt = None
    for line in lines:
        m = re.match(r'^(\d{1,2})\s+(.*)', line)
        if m:
            question_lines.append(m.group(2))
            continue
        m2 = option_re.match(line)
        if m2:
            current_opt = line[:2].lower()[0]
            options[current_opt] = line[2:].strip()
            continue
        if current_opt:
            options[current_opt] += ' ' + line.strip()
        else:
            question_lines.append(line.strip())
    # Orden alfabético de campos, igual que los ejemplos de referencia
    campos = [
        ('category', cat_id),
        ('category_name', cat_name),
        ('correct_answer', None),
        ('id', qid),
        ('options', options),
        ('question', ' '.join(question_lines).strip()),
    ]
    # Ordenar exactamente como: category, category_name, correct_answer, id, options, question
    orden = ['category', 'category_name', 'correct_answer', 'id', 'options', 'question']
    campos_ordenados = sorted(campos, key=lambda x: orden.index(x[0]))
    return OrderedDict(campos_ordenados)


def main():
    parser = argparse.ArgumentParser(description="Convierte un TXT de exámenes PER en YAMLs oficiales.")
    parser.add_argument('--input-file', required=True, help='Fichero TXT de entrada')
    parser.add_argument('--output-dir', required=True, help='Directorio de salida para los YAML')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    parse_txt_to_yaml(args.input_file, args.output_dir)


if __name__ == "__main__":
    main()
