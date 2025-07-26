"""
Endpoints para gestión de exámenes

Este módulo define las rutas de la API que el cliente puede llamar:
- POST /api/exams/generate: Generar un nuevo examen
- POST /api/exams/correct: Corregir un examen
- GET /api/exams/info: Obtener información sobre preguntas disponibles
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.models.schemas import (
    ExamGenerationRequest, GeneratedExam,
    ExamSubmission, ExamResult
)
from app.services.exam_service import exam_service
from app.services.question_loader import question_loader

# Crear el router para las rutas de exámenes
# Un router es como una "sección" de la API
router = APIRouter(prefix="/api/exams", tags=["exams"])


def _validate_communities(comunidades: list) -> None:
    """
    Valida que las comunidades especificadas existan en los datos disponibles.

    Args:
        comunidades: Lista de comunidades a validar
    Raises:
        ValueError: Si alguna comunidad no existe
    """
    available_communities = question_loader.get_available_communities()

    for comunidad in comunidades:
        if comunidad not in available_communities:
            available_str = ", ".join(sorted(available_communities))
            raise ValueError(
                f"La comunidad '{comunidad}' no está disponible. "
                f"Comunidades disponibles: {available_str}"
            )


@router.post("/generate", response_model=GeneratedExam)
async def generate_exam(request: ExamGenerationRequest) -> GeneratedExam:
    """
    Genera un nuevo examen aleatorio o simulacro.
    Si request.tipo_examen == 'simulacro', usa la distribución fija.

    **Cómo funciona:**
    1. El cliente envía criterios (número de preguntas, categorías, etc.)
    2. El servidor busca preguntas que cumplen los criterios
    3. Selecciona preguntas aleatorias
    4. Guarda el examen completo en memoria
    5. Envía al cliente solo las preguntas (sin respuestas correctas)

    **Ejemplo de uso:**
    ```
    POST /api/exams/generate
    {
        "num_preguntas": 20,
        "categorias": ["nomenclatura_nautica", "seguridad"],
        "años": [2022, 2023]
    }
    ```

    Args:
        request: Criterios para generar el examen
    Returns:
        Examen generado con ID único y preguntas
    Raises:
        HTTPException: Si no hay suficientes preguntas o hay error
    """
    try:
        # Validar comunidades antes de generar el examen
        if request.comunidades:
            _validate_communities(request.comunidades)

        if hasattr(request, 'tipo_examen') and request.tipo_examen == 'simulacro':
            exam = exam_service.generate_simulacro_exam(request)
        else:
            exam = exam_service.generate_exam(request)
        return exam
    except ValueError as e:
        # Si no hay suficientes preguntas, devolver error 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Para cualquier otro error, devolver error 500
        raise HTTPException(status_code=500,
                            detail=f"Error generando examen: {str(e)}")


@router.post("/correct", response_model=ExamResult)
async def correct_exam(submission: ExamSubmission) -> ExamResult:
    """
    Corrige un examen enviado por el cliente.

    **Cómo funciona:**
    1. El cliente envía el ID del examen y sus respuestas
    2. El servidor busca el examen original en memoria
    3. Compara cada respuesta con la correcta
    4. Calcula estadísticas generales y por categoría
    5. Elimina el examen de memoria (ya no es necesario)
    6. Devuelve resultados detallados

    **Ejemplo de uso:**
    ```
    POST /api/exams/correct
    {
        "exam_id": "exam_abc12345",
        "respuestas": {
            "per_nom_001_2023_madrid_p27": "b",
            "per_seg_015_2023_valencia_p12": "a"
        }
    }
    ```

    Args:
        submission: ID del examen y respuestas del usuario

    Returns:
        Resultado detallado con puntuación, desglose y explicaciones

    Raises:
        HTTPException: Si el examen no existe o hay error
    """
    try:
        result = exam_service.correct_exam(submission)
        return result
    except ValueError as e:
        # Si el examen no existe o expiró, devolver error 404
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Para cualquier otro error, devolver error 500
        raise HTTPException(status_code=500, detail=f"Error corrigiendo examen: {str(e)}")


@router.get("/info")
async def get_exam_info() -> Dict[str, Any]:
    """
    Obtiene información sobre las preguntas disponibles.

    **Útil para:**
    - Mostrar al usuario qué categorías hay disponibles
    - Mostrar años disponibles
    - Mostrar estadísticas generales
    - Verificar el estado del servicio

    **Ejemplo de respuesta:**
    ```json
    {
        "preguntas": {
            "total_preguntas": 1250,
            "categorias": 10,
            "años_disponibles": [2020, 2021, 2022, 2023],
            "comunidades_disponibles": ["madrid", "valencia", "barcelona"],
            "preguntas_por_categoria": {
                "nomenclatura_nautica": 125,
                "seguridad": 98
            }
        },
        "servicio": {
            "examenes_activos": 3,
            "ttl_examenes": "2.0 horas"
        }
    }
    ```

    Returns:
        Información completa sobre preguntas y estado del servicio
    """
    try:
        return {
            "preguntas": question_loader.get_stats(),
            "servicio": exam_service.get_service_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo información: {str(e)}")


@router.get("/categories")
async def get_categories() -> Dict[str, list]:
    """
    Obtiene todas las categorías disponibles.

    **Útil para:** Crear listas desplegables en el frontend.

    Returns:
        Lista de categorías disponibles (cada una con id y nombre)
    """
    try:
        # Usar el método del question_loader que ya devuelve el formato correcto
        return {
            "categorias": question_loader.get_available_categories(),
            "años": question_loader.get_available_years(),
            "comunidades": question_loader.get_available_communities()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo categorías: {str(e)}")
