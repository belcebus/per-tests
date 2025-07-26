"""
Modelos Pydantic para la aplicación PER Tests

Pydantic es una librería que nos ayuda a:
1. Definir la estructura de nuestros datos
2. Validar automáticamente que los datos son correctos
3. Convertir entre formatos (JSON, diccionarios Python, etc.)

Estos modelos representan la estructura de nuestros datos principales.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ================================
# MODELOS PARA LAS PREGUNTAS
# ================================

class QuestionMetadata(BaseModel):
    """
    Información adicional sobre cada pregunta.

    Esta clase define qué información extra tendrá cada pregunta:
    - title: Título del examen (ej: "EXAMEN DE PATRÓN DE EMBARCACIONES\n"
      "DE RECREO")
    - subtitle: Subtítulo del examen (ej: "Código de Test 01")
    - total_questions: Número total de preguntas en el examen
    - community: Comunidad autónoma donde se realizó el examen (ej: "Madrid")
    - year: Año en que se realizó el examen (ej: 2025)
    - call: Convocatoria del examen (ej: "Ordinaria", "Extraordinaria")
    - test_code: Código del test (ej: "Test01", "Test03")

    Campos opcionales para compatibilidad con formato anterior:
    - categoria: A qué tema pertenece (mantenido por compatibilidad)
    - convocatoria: En qué convocatoria apareció (mantenido por compatibilidad)
    - año: En qué año apareció (mantenido por compatibilidad)
    - comunidad_autonoma: De qué comunidad autónoma era el examen\n"
      "(mantenido por compatibilidad)
    - numero_pregunta: Qué número tenía en el examen original\n"
      "(mantenido por compatibilidad)
    """
    # Nuevos campos principales
    title: str
    subtitle: str
    total_questions: int
    community: str
    year: int
    call: str
    test_code: str

    # Campos de compatibilidad (opcionales)
    categoria: Optional[str] = None
    categoria_nombre: Optional[str] = None
    convocatoria: Optional[str] = None
    año: Optional[int] = None
    comunidad_autonoma: Optional[str] = None
    numero_pregunta: Optional[int] = None


class Question(BaseModel):
    """
    Modelo que representa una pregunta completa.

    Cada pregunta tiene:
    - id: Identificador único (ej: "per_nom_001_2023_madrid_p27")
    - enunciado: El texto de la pregunta
    - opciones: Diccionario con las opciones {"a": "texto1", "b": "texto2"}
    - respuesta_correcta: La letra de la opción correcta ("a", "b", etc.)
    - metadata: Información adicional sobre la pregunta
    """
    id: str
    enunciado: str
    opciones: Dict[str, str]  # {"a": "opción 1", "b": "opción 2"}
    respuesta_correcta: str   # "a", "b", "c", "d"
    metadata: QuestionMetadata


class QuestionForClient(BaseModel):
    """
    Versión de la pregunta que se envía al cliente.

    Es igual que Question pero SIN la respuesta correcta.
    Esto garantiza que el cliente no puede ver la respuesta correcta.
    """
    id: str
    enunciado: str
    opciones: Dict[str, str]
    metadata: QuestionMetadata


# ================================
# MODELOS PARA ARCHIVOS YAML
# ================================

class FileMetadata(BaseModel):
    """
    Metadatos que van al principio de cada archivo YAML.

    Nos dice:
    - exam_type: Tipo de examen ("per", "patron_yate", etc.)
    - category: Categoría de las preguntas en este archivo
    - version: Versión del archivo
    """
    exam_type: str
    category: str
    version: str


class QuestionFile(BaseModel):
    """
    Estructura completa de un archivo YAML de preguntas.

    Cada archivo YAML tendrá:
    - metadata: Información sobre el archivo
    - preguntas: Lista de todas las preguntas
    """
    metadata: FileMetadata
    preguntas: List[Question]


# ================================
# MODELOS PARA GENERACIÓN DE EXÁMENES
# ================================

class ExamGenerationRequest(BaseModel):
    """
    Petición para generar un nuevo examen.

    El usuario puede especificar:
    - num_preguntas: Cuántas preguntas quiere (por defecto 45)
    - categorias: Lista de categorías específicas (None = todas)
    - años: Lista de años específicos (None = todos)
    - comunidades: Lista de comunidades específicas (None = todas)
    - tipo_examen: Tipo de examen (por defecto "per")
    """
    num_preguntas: int = Field(
        default=45,
        ge=1,
        le=100,
        description="Número de preguntas del examen (entre 1 y 100)"
    )
    categorias: Optional[List[str]] = None
    años: Optional[List[int]] = None
    comunidades: Optional[List[str]] = None
    tipo_examen: str = "per"


class GeneratedExam(BaseModel):
    """
    Examen generado que se envía al cliente.

    Contiene:
    - exam_id: Identificador único del examen
    - questions: Lista de preguntas (sin respuestas correctas)
    - metadata: Información sobre cómo se generó el examen
    """
    exam_id: str
    questions: List[QuestionForClient]
    metadata: ExamGenerationRequest


# ================================
# MODELOS PARA CORRECCIÓN
# ================================

class ExamSubmission(BaseModel):
    """
    Respuestas del examen enviadas por el cliente.

    Contiene:
    - exam_id: ID del examen que se está corrigiendo
    - respuestas: Diccionario con las respuestas {"pregunta_id": "letra"}
    """
    exam_id: str
    respuestas: Dict[str, str]  # {"per_nom_001_2023_madrid_p27": "b"}


class CategoryResult(BaseModel):
    """
    Resultado por categoría.

    Para cada categoría muestra:
    - correctas: Número de respuestas correctas
    - total: Número total de preguntas de esa categoría
    - porcentaje: Porcentaje de acierto
    """
    correctas: int
    total: int
    porcentaje: float


class QuestionResult(BaseModel):
    """
    Resultado detallado de una pregunta específica.

    Muestra:
    - question_id: ID de la pregunta
    - respuesta_usuario: Lo que respondió el usuario (letra)
    - respuesta_correcta: La respuesta correcta original (letra o múltiples)
    - respuestas_correctas_lista: Lista de todas las respuestas válidas
    - texto_respuesta_usuario: Texto de la opción que eligió el usuario
    - texto_respuesta_correcta: Texto de la opción correcta (o primera válida)
    - textos_respuestas_correctas: Textos de todas las opciones correctas
    - es_correcta: Si acertó o no
    - es_anulada: Si la pregunta fue anulada
    - enunciado: El texto de la pregunta (para referencia)
    - opciones: Todas las opciones disponibles
    - metadata: Metadatos de la pregunta (comunidad, año, convocatoria,\n
      modelo, etc.)
    """
    question_id: str
    respuesta_usuario: Optional[str]
    respuesta_correcta: str
    respuestas_correctas_lista: List[
        str
    ]  # Nueva: lista de todas las respuestas válidas
    texto_respuesta_usuario: Optional[str]
    texto_respuesta_correcta: str
    textos_respuestas_correctas: Dict[
        str, str
    ]  # Nueva: textos de todas las respuestas válidas
    es_correcta: bool
    es_anulada: bool  # Nueva: indica si la pregunta fue anulada
    enunciado: str
    opciones: Dict[str, str]
    metadata: QuestionMetadata


class ExamResult(BaseModel):
    """
    Resultado completo del examen corregido.

    Incluye:
    - puntuacion_total: "correctas/total" (ej: "38/45")
    - porcentaje: Porcentaje de acierto
    - aprobado: Si aprobó o no (>=65%)
    - desglose_por_categoria: Resultados por cada categoría
    - preguntas_detalle: Detalle de cada pregunta
    """
    puntuacion_total: str
    porcentaje: float
    aprobado: bool
    desglose_por_categoria: Dict[str, CategoryResult]
    preguntas_detalle: List[QuestionResult]


# ================================
# MODELOS PARA CACHÉ EN MEMORIA
# ================================

class CachedExam(BaseModel):
    """
    Examen almacenado en memoria del servidor.

    Guarda:
    - questions: Las preguntas completas (CON respuestas correctas)
    - metadata: Información sobre el examen
    - timestamp: Cuándo se creó (para limpieza automática)
    """
    questions: List[Question]
    metadata: ExamGenerationRequest
    timestamp: datetime
