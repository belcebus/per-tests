#!/usr/bin/env python3
# pylint: disable=no-member
"""
Extrae respuestas de exámenes tipo test desde PDF escaneado usando OCR.
Salida: un JSON por modelo en extracted-answers/ con la estructura de ejemplo.
"""

import re
import json
from pathlib import Path
from typing import Dict
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import pytesseract
import argparse

# --- Configuración de tipos de examen ---
EXAM_TYPES = {
    "CAPITÁN DE YATE": {"key": "capitan-yate", "num_questions": 40, "range": range(1, 41)},
    "PATRÓN DE YATE": {"key": "patron-yate", "num_questions": 40, "range": range(1, 41)},
    "PATRÓN DE EMBARCACIONES DE RECREO": {"key": "per", "num_questions": 45, "range": range(1, 46)},
    "(CON PNB LIBERADO)": {"key": "per-pnb", "num_questions": 18, "range": range(28, 46)},
}


# --- Utilidades de imagen ---
def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    # Configuración 2: Contraste 1.5, Nitidez 1.5, binarización simple (la mejor)
    if image.mode != 'L':
        image = image.convert('L')
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    try:
        import numpy as np
        import cv2
        img_array = np.array(image)
        _, img_bin = cv2.threshold(img_array, 180, 255, cv2.THRESH_BINARY)
        image = Image.fromarray(img_bin)
    except Exception:
        pass
    return image


# --- OCR de PDF ---
def extract_text_from_pdf(pdf_path: str):
    images = convert_from_path(pdf_path, dpi=800)
    texts_full = []
    texts_left = []
    output_dir = Path('extracted-answers')
    output_dir.mkdir(exist_ok=True)
    for i, img in enumerate(images):
        img_proc = enhance_image_for_ocr(img)
        img_proc_path = output_dir / f"pagina_{i+1}_procesada.png"
        img_proc.save(img_proc_path)
        text_full = pytesseract.image_to_string(img_proc, lang='spa')
        texts_full.append(text_full)
        txt_path = output_dir / f"ocr_pagina_{i+1}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_full)
        # --- Segunda pasada: solo zona izquierda para respuestas (Tesseract) ---
        w, h = img_proc.size
        left_crop = img_proc.crop((0, 0, int(w * 0.22), h))  # noqa: E226
        left_crop_path = output_dir / f"pagina_{i+1}_izquierda.png"
        left_crop.save(left_crop_path)
        config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDabcd'
        text_left = pytesseract.image_to_string(left_crop, lang='spa', config=config)
        texts_left.append(text_left)
        txt_left_path = output_dir / f"ocr_pagina_{i+1}_izquierda.txt"
        with open(txt_left_path, 'w', encoding='utf-8') as f:
            f.write(text_left)
    return texts_full, texts_left


# --- Nuevo parseo dual: usa OCR completo para cabecera/modelo y OCR recortado para respuestas ---
def parse_exam_pages_dual(texts_full: list, texts_left: list, pdf_name: str) -> list:
    exams = []
    for page_num, (page_text, page_left) in enumerate(zip(texts_full, texts_left), 1):
        # Buscar tipo de examen con distinción PER vs PER-PNB
        exam_type, exam_key = None, None
        lines = [line.strip().upper() for line in page_text.splitlines()]
        for idx, line in enumerate(lines):
            # PER y PER-PNB
            if re.search(r"PATR[ÓO]N\s+DE\s+EMBARCACIONES?\s+DE\s+RECREO", line):
                next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
                if re.search(r"PNB\s*LIBERADO", next_line):
                    exam_type = "(CON PNB LIBERADO)"
                else:
                    exam_type = "PATRÓN DE EMBARCACIONES DE RECREO"
                exam_key = EXAM_TYPES[exam_type]["key"]
                break
            elif re.search(r"PATR[ÓO]N\s+DE\s+YATE", line):
                exam_type = "PATRÓN DE YATE"
                exam_key = EXAM_TYPES[exam_type]["key"]
                break
            elif re.search(r"CAPIT[ÁA]N\s+DE\s+YATE", line):
                exam_type = "CAPITÁN DE YATE"
                exam_key = EXAM_TYPES[exam_type]["key"]
                break
            elif line in EXAM_TYPES:
                exam_type = line
                exam_key = EXAM_TYPES[line]["key"]
                break
        if not exam_type:
            print(f"[WARN] No se detectó tipo de examen en página {page_num}")
            continue
        # Buscar modelo
        model_match = re.search(r"C[ÓO]DIGO DE TEST\s*(\d{2})", page_text, re.IGNORECASE)
        test_model = f"TEST{model_match.group(1)}" if model_match else "UNKNOWN"

        # --- Mejorado: Parseo robusto de respuestas ---
        valid_answers = {"a", "b", "c", "d", "anulada"}
        valid_range = [str(n) for n in EXAM_TYPES[exam_type]["range"]]
        expected_num = int(valid_range[0])
        final_answers = {}
        used_numbers = set()
        for answer_line in page_left.splitlines():
            # Limpiar línea y buscar patrón flexible
            answer_line = answer_line.strip()
            # Buscar ANULADA explícito
            if re.search(r"anul[ao]da", answer_line, re.IGNORECASE):
                final_answers[str(expected_num)] = "anulada"
                used_numbers.add(expected_num)
                expected_num += 1
                continue
            # Buscar patrón: número (1-3 cifras) + letra (a-d)
            m = re.match(r"^(\d{1,3})\s*([ABCDabcd])$", answer_line)
            if m:
                num, ans = m.group(1), m.group(2).lower()
                num_int = int(num)
                # Comprobar si el número es el esperado
                if num_int != expected_num:
                    print(f"[WARN] Número no consecutivo detectado en línea '{answer_line}'. Esperado: {expected_num}, Detectado: {num_int}. Se usará el esperado.")
                    num_int = expected_num
                if ans not in valid_answers:
                    print(f"[WARN] Respuesta no válida '{ans}' en línea '{answer_line}'. Se marcará como 'anulada'.")
                    ans = "anulada"
                final_answers[str(num_int)] = ans
                used_numbers.add(num_int)
                expected_num += 1
                continue
            # Buscar patrón: número pegado a letra, pero con errores de OCR (ej: 146B, 353A, 410A, 465B)
            m2 = re.match(r"^(\d{2,})([ABCDabcd])$", answer_line)
            if m2:
                num, ans = m2.group(1), m2.group(2).lower()
                # Intentar extraer el número correcto (últimos dos dígitos suelen ser el número de pregunta)
                num_int = int(num[-2:])
                if num_int != expected_num:
                    print(f"[WARN] Número OCR dudoso '{num}' en línea '{answer_line}'. Esperado: {expected_num}, Usando: {expected_num}.")
                    num_int = expected_num
                if ans not in valid_answers:
                    print(f"[WARN] Respuesta no válida '{ans}' en línea '{answer_line}'. Se marcará como 'anulada'.")
                    ans = "anulada"
                final_answers[str(num_int)] = ans
                used_numbers.add(num_int)
                expected_num += 1
                continue
            # Buscar patrón: solo letra (puede ser respuesta suelta)
            m3 = re.match(r"^([ABCDabcd])$", answer_line)
            if m3:
                ans = m3.group(1).lower()
                if ans not in valid_answers:
                    print(f"[WARN] Respuesta no válida '{ans}' en línea '{answer_line}'. Se marcará como 'anulada'.")
                    ans = "anulada"
                final_answers[str(expected_num)] = ans
                used_numbers.add(expected_num)
                expected_num += 1
                continue
            # Buscar patrón: número solo (puede ser error, ignorar)
            m4 = re.match(r"^(\d{1,3})$", answer_line)
            if m4:
                print(f"[WARN] Línea con solo número '{answer_line}', ignorada.")
                continue
            # Si no coincide nada, ignorar o marcar como anulada
            if answer_line:
                print(f"[WARN] Línea no reconocida: '{answer_line}'. Se marcará como 'anulada'.")
                final_answers[str(expected_num)] = "anulada"
                used_numbers.add(expected_num)
                expected_num += 1

        # Completar las que falten
        for num in valid_range:
            if int(num) not in used_numbers:
                final_answers[num] = "anulada"

        # Estructura de salida
        exams.append({
            "exam_type": exam_key.upper() if exam_key else exam_type,
            "test_model": test_model,
            "total_answers": len(final_answers),
            "answers": final_answers,
            "source_pdf": pdf_name,
            "generated_at": None,
            "pdf_info": extract_pdf_info_from_name(pdf_name)
        })
    return exams


def extract_pdf_info_from_name(pdf_name: str) -> Dict:
    # Ejemplo: madrid-2024-junio.pdf
    stem = Path(pdf_name).stem
    parts = stem.split('-')
    return {
        "comunidad": parts[0] if len(parts) > 0 else "",
        "año": parts[1] if len(parts) > 1 else "",
        "convocatoria": parts[2] if len(parts) > 2 else ""
    }


def save_exam_json(exam: Dict, output_dir: Path):
    # Nombre: per-test01-madrid-2024-junio.json
    exam_type = exam["exam_type"].lower().replace('_', '-')
    test_model = exam["test_model"].lower()
    pdf_info = exam["pdf_info"]
    filename = f"{exam_type}-{test_model}-{pdf_info['comunidad']}-{pdf_info['año']}-{pdf_info['convocatoria']}.json"
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exam, f, indent=2, ensure_ascii=False)
    print(f"[OK] Guardado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="🚢 Extrae respuestas oficiales de un PDF usando OCR")

    # Argumentos estandarizados
    parser.add_argument('--input-file', required=True, help='Archivo PDF de respuestas oficiales')
    parser.add_argument('--output-dir', default='extracted-answers', help='Directorio de salida (default: extracted-answers)')
    parser.add_argument('--verbose', action='store_true', help='Mostrar información detallada del procesamiento')

    args = parser.parse_args()

    # Usar nombres estandarizados
    pdf_path = Path(args.input_file)
    if not pdf_path.exists():
        print(f"❌ ERROR: No existe el archivo: {pdf_path}")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if args.verbose:
        print("🚀 Iniciando extracción de respuestas...")
        print(f"📄 PDF de entrada: {pdf_path}")
        print(f"📁 Directorio de salida: {output_dir}")

    texts_full, texts_left = extract_text_from_pdf(str(pdf_path))
    exams = parse_exam_pages_dual(texts_full, texts_left, pdf_path.name)

    for exam in exams:
        save_exam_json(exam, output_dir)
        if args.verbose:
            print(f"✅ Guardado examen: {exam['exam_type']} - {exam['test_model']}")

    if args.verbose:
        print(f"🎉 Extracción completada. {len(exams)} exámenes procesados.")


if __name__ == "__main__":
    main()
