#!/usr/bin/env python3
"""
Script para aplicar respuestas extraídas por OCR a archivos YAML de preguntas de examen

PROPÓSITO:
Este script toma las respuestas extraídas por el extractor OCR y las aplica
a los archivos YAML que contienen las preguntas de examen, generando archivos
de examen completos con preguntas y respuestas.

CARACTERÍSTICAS:
- Aplicación automática de respuestas a preguntas
- Generación de backups automáticos antes de modificar
- Validación de consistencia entre preguntas y respuestas
- Manejo de respuestas anuladas
- Soporte para múltiples formatos de entrada
- Corrección automática de rutas y paths

ENTRADA:
- Archivos JSON con respuestas extraídas (extracted_answers/)
- Archivos YAML con preguntas de examen (data/exams/)

SALIDA:
- Archivos YAML actualizados con respuestas aplicadas
- Backups de los archivos originales

ESTRUCTURA DE ARCHIVOS ESPERADA:
extracted_answers/
├── per-test01-madrid-2024-noviembre.json
├── per-test02-madrid-2025-abril.json
└── ...

data/exams/
├── per-test01-madrid-2024-noviembre.yaml
├── per-test02-madrid-2025-abril.yaml
└── ...

EJEMPLO DE USO:
python tools/processing/madrid_merge_exam.py --answers-file extracted_answers/per-test01-madrid-2024-noviembre-final.json
python tools/processing/madrid_merge_exam.py --auto-discover
"""

import os
import json
import yaml
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MadridExamMerger:
    """Clase para aplicar respuestas extraídas a archivos YAML de examen"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.answers_dir = self.workspace_root / "extracted_answers"
        self.exams_dir = self.workspace_root / "data" / "exams"
        self.backups_dir = self.workspace_root / "backups"
        
        # Crear directorios si no existen
        self.backups_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Workspace root: {self.workspace_root}")
        logger.info(f"Respuestas: {self.answers_dir}")
        logger.info(f"Exámenes: {self.exams_dir}")
        logger.info(f"Backups: {self.backups_dir}")
    
    def find_matching_exam_file(self, answers_file: Path) -> Optional[Path]:
        """Buscar archivo YAML de examen que coincida con el archivo de respuestas"""
        
        # Extraer información del nombre del archivo de respuestas
        # Formato esperado: per-test01-madrid-2024-noviembre.json
        name_parts = answers_file.stem.split('-')
        
        if len(name_parts) < 5:
            logger.warning(f"Nombre de archivo de respuestas no reconocido: {answers_file.name}")
            return None
        
        # Construir nombre del archivo YAML correspondiente
        yaml_filename = answers_file.stem + ".yaml"
        yaml_path = self.exams_dir / yaml_filename
        
        if yaml_path.exists():
            return yaml_path
        
        # Buscar variantes del nombre
        for yaml_file in self.exams_dir.glob("*.yaml"):
            if yaml_file.stem == answers_file.stem:
                return yaml_file
        
        logger.warning(f"No se encontró archivo YAML para: {answers_file.name}")
        return None
    
    def create_backup(self, file_path: Path) -> Path:
        """Crear backup de un archivo antes de modificarlo"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{file_path.stem}_{timestamp}_backup{file_path.suffix}"
        backup_path = self.backups_dir / backup_filename
        
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        
        return backup_path
    
    def load_answers(self, answers_file: Path) -> Dict:
        """Cargar respuestas desde archivo JSON"""
        
        try:
            with open(answers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Respuestas cargadas: {len(data.get('answers', {}))} respuestas")
            return data
        
        except Exception as e:
            logger.error(f"Error cargando respuestas de {answers_file}: {e}")
            raise
    
    def load_exam(self, exam_file: Path) -> Dict:
        """Cargar examen desde archivo YAML"""
        
        try:
            with open(exam_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            logger.info(f"Examen cargado: {len(data.get('questions', []))} preguntas")
            return data
        
        except Exception as e:
            logger.error(f"Error cargando examen de {exam_file}: {e}")
            raise
    
    def apply_answers_to_exam(self, exam_data: Dict, answers_data: Dict) -> Tuple[Dict, int, List[str]]:
        """Aplicar respuestas al examen y retornar estadísticas"""
        
        answers = answers_data.get('answers', {})
        questions = exam_data.get('questions', [])
        
        applied_count = 0
        warnings = []
        
        # Aplicar respuestas a preguntas
        for i, question in enumerate(questions, 1):
            question_num = str(i)
            
            if question_num in answers:
                answer = answers[question_num]
                
                # Validar que la respuesta es válida
                valid_answers = ['a', 'b', 'c', 'd', 'ANULADA']
                if answer not in valid_answers:
                    warnings.append(f"Respuesta inválida para pregunta {question_num}: {answer}")
                    continue
                
                # Aplicar respuesta
                question['correct_answer'] = answer
                applied_count += 1
                
                logger.debug(f"Aplicada respuesta {question_num}: {answer}")
            
            else:
                warnings.append(f"No se encontró respuesta para pregunta {question_num}")
        
        # Actualizar metadatos del examen
        if 'metadata' not in exam_data:
            exam_data['metadata'] = {}
        
        exam_data['metadata']['answers_applied'] = True
        exam_data['metadata']['answers_applied_at'] = datetime.now().isoformat()
        exam_data['metadata']['answers_source'] = answers_data.get('source_pdf', 'unknown')
        exam_data['metadata']['total_answers_applied'] = applied_count
        
        return exam_data, applied_count, warnings
    
    def save_exam(self, exam_data: Dict, exam_file: Path):
        """Guardar examen actualizado a archivo YAML"""
        
        try:
            with open(exam_file, 'w', encoding='utf-8') as f:
                yaml.dump(exam_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Examen guardado: {exam_file}")
        
        except Exception as e:
            logger.error(f"Error guardando examen a {exam_file}: {e}")
            raise
    
    def merge_single_exam(self, answers_file: Path) -> bool:
        """Aplicar respuestas de un archivo específico a su examen correspondiente"""
        
        logger.info(f"🔄 Procesando: {answers_file.name}")
        
        # Buscar archivo YAML correspondiente
        exam_file = self.find_matching_exam_file(answers_file)
        if not exam_file:
            logger.error(f"❌ No se encontró archivo YAML para: {answers_file.name}")
            return False
        
        logger.info(f"📄 Archivo de examen encontrado: {exam_file.name}")
        
        try:
            # Crear backup
            backup_path = self.create_backup(exam_file)
            
            # Cargar datos
            answers_data = self.load_answers(answers_file)
            exam_data = self.load_exam(exam_file)
            
            # Aplicar respuestas
            updated_exam, applied_count, warnings = self.apply_answers_to_exam(exam_data, answers_data)
            
            # Mostrar warnings
            if warnings:
                logger.warning(f"⚠️  {len(warnings)} advertencias:")
                for warning in warnings[:5]:  # Mostrar solo las primeras 5
                    logger.warning(f"  - {warning}")
                if len(warnings) > 5:
                    logger.warning(f"  ... y {len(warnings) - 5} advertencias más")
            
            # Guardar examen actualizado
            self.save_exam(updated_exam, exam_file)
            
            logger.info(f"✅ Aplicadas {applied_count} respuestas a {exam_file.name}")
            logger.info(f"💾 Backup disponible: {backup_path.name}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error procesando {answers_file.name}: {e}")
            return False
    
    def auto_discover_and_merge(self) -> int:
        """Buscar automáticamente archivos de respuestas y aplicarlos"""
        
        logger.info("🔍 Búsqueda automática de archivos de respuestas...")
        
        if not self.answers_dir.exists():
            logger.error(f"❌ Directorio de respuestas no existe: {self.answers_dir}")
            return 0
        
        # Buscar archivos JSON de respuestas
        answer_files = list(self.answers_dir.glob("*.json"))
        
        if not answer_files:
            logger.warning("⚠️  No se encontraron archivos de respuestas")
            return 0
        
        logger.info(f"📁 Encontrados {len(answer_files)} archivos de respuestas")
        
        # Procesar cada archivo
        success_count = 0
        for answer_file in answer_files:
            # Filtrar archivos que no sean de respuestas de examen
            if any(skip in answer_file.name for skip in ['summary', 'complete', 'corrected']):
                # Priorizar archivos finales o completos
                if 'final' in answer_file.name or 'complete' in answer_file.name:
                    if self.merge_single_exam(answer_file):
                        success_count += 1
            else:
                if self.merge_single_exam(answer_file):
                    success_count += 1
        
        logger.info(f"✅ Procesados exitosamente: {success_count}/{len(answer_files)}")
        return success_count
    
    def list_available_answers(self):
        """Listar archivos de respuestas disponibles"""
        
        if not self.answers_dir.exists():
            print(f"❌ Directorio de respuestas no existe: {self.answers_dir}")
            return
        
        answer_files = list(self.answers_dir.glob("*.json"))
        
        if not answer_files:
            print("⚠️  No se encontraron archivos de respuestas")
            return
        
        print("📁 Archivos de respuestas disponibles:")
        print("=" * 50)
        
        for answer_file in sorted(answer_files):
            try:
                with open(answer_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                exam_type = data.get('exam_type', 'Unknown')
                test_model = data.get('test_model', 'Unknown')
                total_answers = data.get('total_answers', len(data.get('answers', {})))
                
                print(f"📄 {answer_file.name}")
                print(f"   Tipo: {exam_type}, Modelo: {test_model}")
                print(f"   Respuestas: {total_answers}")
                
                # Verificar si existe archivo YAML correspondiente
                exam_file = self.find_matching_exam_file(answer_file)
                if exam_file:
                    print(f"   ✅ YAML: {exam_file.name}")
                else:
                    print(f"   ❌ YAML: No encontrado")
                print()
            
            except Exception as e:
                print(f"❌ Error leyendo {answer_file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Aplicar respuestas extraídas por OCR a archivos YAML de examen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Aplicar respuestas de un archivo específico
  python madrid_merge_exam.py --answers-file extracted_answers/per-test01-madrid-2024-noviembre-final.json
  
  # Búsqueda automática y aplicación de todas las respuestas
  python madrid_merge_exam.py --auto-discover
  
  # Listar archivos de respuestas disponibles
  python madrid_merge_exam.py --list-answers
        """
    )
    
    parser.add_argument(
        "--answers-file",
        type=str,
        help="Archivo específico de respuestas a aplicar"
    )
    
    parser.add_argument(
        "--auto-discover",
        action="store_true",
        help="Buscar automáticamente y aplicar todas las respuestas disponibles"
    )
    
    parser.add_argument(
        "--list-answers",
        action="store_true",
        help="Listar archivos de respuestas disponibles"
    )
    
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Directorio raíz del workspace (por defecto: directorio actual)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Habilitar logging debug"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear merger
    merger = MadridExamMerger(args.workspace)
    
    try:
        if args.list_answers:
            merger.list_available_answers()
        
        elif args.answers_file:
            answers_path = Path(args.answers_file)
            if not answers_path.exists():
                logger.error(f"❌ Archivo de respuestas no existe: {answers_path}")
                return 1
            
            success = merger.merge_single_exam(answers_path)
            return 0 if success else 1
        
        elif args.auto_discover:
            success_count = merger.auto_discover_and_merge()
            return 0 if success_count > 0 else 1
        
        else:
            # Por defecto, mostrar ayuda y listar archivos disponibles
            parser.print_help()
            print("\n")
            merger.list_available_answers()
    
    except KeyboardInterrupt:
        logger.info("🛑 Operación cancelada por el usuario")
        return 1
    
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
