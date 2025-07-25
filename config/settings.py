"""
Configuración centralizada de la aplicación PER Tests

Este módulo proporciona configuración centralizada para:
- Rutas de archivos y directorios
- Configuración del servidor web
- Configuración de exámenes
- Configuración de herramientas de procesamiento
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    
    Utiliza variables de entorno con prefijo PER_
    o valores por defecto si no están definidas.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # ==========================================
    # CONFIGURACIÓN DE RUTAS Y DIRECTORIOS
    # ==========================================
    
    # Directorio base del proyecto
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent,
        description="Directorio raíz del proyecto"
    )
    
    # Directorios de datos
    data_dir: str = Field(
        default="data",
        alias="PER_DATA_DIR",
        description="Directorio base de datos"
    )
    
    exams_dir: str = Field(
        default="data/exams",
        alias="PER_EXAMS_DIR", 
        description="Directorio de archivos YAML de exámenes"
    )
    
    raw_questions_dir: str = Field(
        default="data/raw/questions",
        alias="PER_RAW_QUESTIONS_DIR",
        description="Directorio de PDFs de preguntas originales"
    )
    
    raw_answers_dir: str = Field(
        default="data/raw/answers", 
        alias="PER_RAW_ANSWERS_DIR",
        description="Directorio de PDFs de respuestas originales"
    )
    
    backups_dir: str = Field(
        default="data/backups",
        alias="PER_BACKUPS_DIR",
        description="Directorio de backups de archivos YAML"
    )
    
    extracted_dir: str = Field(
        default="extracted_answers",
        alias="PER_EXTRACTED_DIR",
        description="Directorio de archivos extraídos temporalmente"
    )
    
    static_dir: str = Field(
        default="static",
        alias="PER_STATIC_DIR",
        description="Directorio de archivos estáticos del frontend"
    )
    
    # ==========================================
    # CONFIGURACIÓN DEL SERVIDOR WEB
    # ==========================================
    
    # Configuración de uvicorn
    host: str = Field(
        default="0.0.0.0",
        alias="PER_HOST",
        description="Host del servidor"
    )
    
    port: int = Field(
        default=8002,
        alias="PER_PORT",
        description="Puerto del servidor"
    )
    
    reload: bool = Field(
        default=True,
        alias="PER_RELOAD",
        description="Recarga automática en desarrollo"
    )
    
    log_level: str = Field(
        default="info",
        alias="PER_LOG_LEVEL",
        description="Nivel de logging"
    )
    
    # ==========================================
    # CONFIGURACIÓN DE LA APLICACIÓN
    # ==========================================
    
    # Información de la API
    api_title: str = Field(
        default="PER Tests API",
        alias="PER_API_TITLE",
        description="Título de la API"
    )
    
    api_description: str = Field(
        default="API para generar y corregir exámenes aleatorios de PER España",
        alias="PER_API_DESCRIPTION",
        description="Descripción de la API"
    )
    
    api_version: str = Field(
        default="1.0.0",
        alias="PER_API_VERSION",
        description="Versión de la API"
    )
    
    # ==========================================
    # CONFIGURACIÓN DE EXÁMENES
    # ==========================================
    
    # Configuración de exámenes por defecto
    default_num_questions: int = Field(
        default=45,
        alias="PER_DEFAULT_NUM_QUESTIONS",
        description="Número de preguntas por defecto en exámenes"
    )
    
    exam_ttl_hours: int = Field(
        default=2,
        alias="PER_EXAM_TTL_HOURS",
        description="Tiempo de vida de exámenes en memoria (horas)"
    )
    
    # Configuración de simulacro de examen
    simulacro_distribution: dict = Field(
        default={
            1: 4,   # Nomenclatura náutica
            2: 2,   # Elementos de amarre y fondeo
            3: 4,   # Seguridad
            4: 2,   # Legislación
            5: 5,   # Balizamiento
            6: 10,  # Reglamento (RIPA)
            7: 2,   # Maniobra y navegación
            8: 3,   # Emergencias en la mar
            9: 4,   # Meteorología
            10: 5,  # Teoría de la navegación
            11: 4   # Carta de navegación
        },
        description="Distribución fija de preguntas por categoría para el simulacro (por id de categoría)"
    )
    simulacro_max_time_minutes: int = Field(
        default=90,
        description="Tiempo máximo (minutos) para el simulacro de examen"
    )
    
    # Configuración de corrección de exámenes
    passing_score_percentage: float = Field(
        default=65.0,
        alias="PER_PASSING_SCORE",
        description="Porcentaje mínimo para aprobar un examen"
    )
    
    # ==========================================
    # CONFIGURACIÓN DE PROCESAMIENTO
    # ==========================================
    
    # Configuración de OCR
    ocr_confidence_threshold: float = Field(
        default=0.7,
        alias="PER_OCR_CONFIDENCE_THRESHOLD",
        description="Umbral de confianza para OCR"
    )
    
    # Configuración de procesamiento de PDFs
    pdf_dpi: int = Field(
        default=300,
        alias="PER_PDF_DPI",
        description="DPI para conversión de PDFs a imágenes"
    )
    
    # ==========================================
    # CONFIGURACIÓN DE DESARROLLO
    # ==========================================
    
    debug: bool = Field(
        default=False,
        alias="PER_DEBUG",
        description="Modo debug"
    )
    
    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """
        Obtiene la ruta absoluta basada en el directorio del proyecto.
        
        Args:
            relative_path: Ruta relativa desde el directorio del proyecto
            
        Returns:
            Path: Ruta absoluta
        """
        if os.path.isabs(relative_path):
            return Path(relative_path)
        return self.project_root / relative_path
    
    def get_exams_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de exámenes."""
        return self.get_absolute_path(self.exams_dir)
    
    def get_raw_questions_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de preguntas originales."""
        return self.get_absolute_path(self.raw_questions_dir)
    
    def get_raw_answers_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de respuestas originales."""
        return self.get_absolute_path(self.raw_answers_dir)
    
    def get_backups_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de backups."""
        return self.get_absolute_path(self.backups_dir)
    
    def get_extracted_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de extracción temporal."""
        return self.get_absolute_path(self.extracted_dir)
    
    def get_static_path(self) -> Path:
        """Obtiene la ruta absoluta del directorio de archivos estáticos."""
        return self.get_absolute_path(self.static_dir)


# Instancia global de configuración
settings = Settings()
