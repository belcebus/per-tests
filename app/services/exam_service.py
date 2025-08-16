"""
Servicio para generar y corregir exámenes

Este módulo maneja toda la lógica de:
1. Generar exámenes aleatorios según criterios
2. Almacenar exámenes temporalmente en memoria
3. Corregir exámenes cuando el usuario envía respuestas
4. Limpiar exámenes expirados de memoria
"""

import uuid
import random
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any

from app.models.schemas import (
    Question,
    QuestionForClient,
    ExamGenerationRequest,
    GeneratedExam,
    CachedExam,
    ExamSubmission,
    ExamResult,
    CategoryResult,
    QuestionResult,
)
from app.services.question_loader import question_loader
from config.settings import settings

# Constantes de configuración
EXAM_TYPES_WITH_CORRECT_ANSWERS = {"normal", "per"}
"""Tipos de examen que incluyen respuestas correctas para práctica"""


class ExamService:
    """
    Servicio principal para manejo de exámenes.

    Es como un "profesor" que:
    - Crea exámenes personalizados
    - Los guarda temporalmente
    - Los corrige cuando le traen las respuestas
    - Limpia exámenes antiguos
    """

    def __init__(self):
        """Inicializa el servicio de exámenes."""
        # Diccionario para guardar exámenes en memoria
        # Clave: exam_id, Valor: CachedExam
        self.active_exams: Dict[str, CachedExam] = {}

        # Tiempo de vida de un examen (configurable)
        self.exam_ttl = timedelta(hours=settings.exam_ttl_hours)

        # Servicio de carga de preguntas
        self.question_loader = question_loader

    def _get_question_content_hash(self, question: Question) -> str:
        """
        Genera un hash único basado en el contenido de la pregunta.

        Solo considera:
        - Texto del enunciado (limpio, sin espacios/saltos extra)
        - Textos de las respuestas ordenadas alfabéticamente (limpios)

        Ignora metadatos, IDs y orden original de respuestas para detectar
        preguntas idénticas que puedan venir de diferentes exámenes/modelos.

        Args:
            question: La pregunta de la que generar el hash

        Returns:
            Hash SHA-256 del contenido normalizado de la pregunta
        """
        # Limpiar el enunciado: quitar espacios extra, saltos de línea, etc.
        clean_enunciado = re.sub(r"\s+", " ", question.enunciado.strip())

        # Limpiar y ordenar alfabéticamente las opciones de respuesta
        clean_options = []
        for option_text in question.opciones.values():
            clean_option = re.sub(r"\s+", " ", option_text.strip())
            clean_options.append(clean_option)

        # Ordenar alfabéticamente para que el orden no importe
        clean_options.sort()

        # Crear string con el contenido normalizado
        content = f"{clean_enunciado}||{'||'.join(clean_options)}"

        # Generar hash SHA-256
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _select_unique_questions(
        self, available_questions: List[Question], num_needed: int
    ) -> List[Question]:
        """
        Selecciona preguntas aleatorias evitando duplicados de contenido.

        Usa un algoritmo eficiente O(n) que mantiene un set de hashes
        para detección rápida de duplicados.

        Args:
            available_questions: Lista de preguntas disponibles
            num_needed: Número de preguntas únicas necesarias

        Returns:
            Lista de preguntas seleccionadas sin duplicados de contenido

        Raises:
            ValueError: Si no hay suficientes preguntas únicas disponibles
        """
        if not available_questions:
            raise ValueError("No hay preguntas disponibles para seleccionar")

        # Mezclar las preguntas para selección aleatoria
        shuffled_questions = available_questions.copy()
        random.shuffle(shuffled_questions)

        selected_questions: List[Question] = []
        seen_hashes: Set[str] = set()
        duplicates_found = 0
        duplicate_details: List[Dict[str, Any]] = (
            []
        )  # Para rastrear detalles de duplicados

        for question in shuffled_questions:
            # Si ya tenemos suficientes preguntas, parar
            if len(selected_questions) >= num_needed:
                break

            # Generar hash del contenido de la pregunta
            content_hash = self._get_question_content_hash(question)

            # Si no hemos visto este contenido antes, añadirla
            if content_hash not in seen_hashes:
                selected_questions.append(question)
                seen_hashes.add(content_hash)
            else:
                duplicates_found += 1
                # Registrar detalles del duplicado
                duplicate_info = {
                    "hash": content_hash[:16],
                    "question_id": question.id,
                    "enunciado": (
                        question.enunciado[:80] + "..."
                        if len(question.enunciado) > 80
                        else question.enunciado
                    ),
                    "metadata": {
                        "community": getattr(question.metadata, "community", "N/A"),
                        "year": getattr(question.metadata, "year", "N/A"),
                        "test_code": getattr(question.metadata, "test_code", "N/A"),
                        "categoria": getattr(question.metadata, "categoria", "N/A"),
                    },
                }
                duplicate_details.append(duplicate_info)

        # Verificar que conseguimos suficientes preguntas únicas
        if len(selected_questions) < num_needed:
            unique_available = len(shuffled_questions) - duplicates_found
            raise ValueError(
                f"No hay suficientes preguntas únicas. "
                f"Necesarias: {num_needed}, "
                f"Únicas disponibles: {unique_available}, "
                f"Duplicados encontrados: {duplicates_found}"
            )

        if duplicates_found > 0:
            # Logging básico siempre se muestra (importante para operaciones)
            print(
                f"🔍 Duplicados evitados: {duplicates_found} preguntas con contenido idéntico"
            )

            # Logging detallado solo si está habilitado (desarrollo/debug)
            if settings.verbose_duplicate_logging:
                # Mostrar detalles de los duplicados si no son demasiados
                if duplicates_found <= settings.duplicate_details_threshold:
                    print("   📋 Detalles de duplicados evitados:")
                    for i, dup in enumerate(duplicate_details, 1):
                        metadata = dup["metadata"]
                        exam_info = f"{str(metadata['community'])}-{str(metadata['year'])}-{str(metadata['test_code'])}"
                        print(
                            f"      {i}. Hash:{dup['hash']}... - {exam_info} - Cat:{str(metadata['categoria'])}"
                        )
                        print(f"         Enunciado: {dup['enunciado']}")
                else:
                    print("   📊 Muchos duplicados detectados. Resumen por fuente:")
                    # Agrupar duplicados por fuente
                    by_community: Dict[str, int] = {}
                    by_year: Dict[str, int] = {}
                    for dup in duplicate_details:
                        metadata = dup["metadata"]
                        community = str(metadata["community"])
                        year = str(metadata["year"])

                        by_community[community] = by_community.get(community, 0) + 1
                        by_year[year] = by_year.get(year, 0) + 1

                    print(
                        f"      🏛️  Por comunidad: {dict(sorted(by_community.items(), key=lambda x: x[1], reverse=True))}"
                    )
                    print(
                        f"      📅 Por año: {dict(sorted(by_year.items(), key=lambda x: x[1], reverse=True))}"
                    )

        return selected_questions

    def generate_exam(self, request: ExamGenerationRequest) -> GeneratedExam:
        """
        Genera un nuevo examen según los criterios especificados.
        Previene preguntas duplicadas basándose en contenido.

        Args:
            request: Criterios para generar el examen

        Returns:
            Examen generado listo para enviar al cliente
        """
        print(f"🎯 Generando examen: {request.num_preguntas} preguntas")

        # 1. Obtener preguntas que cumplen los criterios
        available_questions = self.question_loader.get_questions_by_criteria(
            categorias=request.categorias or [],
            anios=request.anios or [],
            comunidades=request.comunidades or [],
            tipo_examen=request.tipo_examen,
        )

        if len(available_questions) < request.num_preguntas:
            raise ValueError(
                f"No hay suficientes preguntas. "
                f"Disponibles: {len(available_questions)}, "
                f"Solicitadas: {request.num_preguntas}"
            )

        # 2. Seleccionar preguntas aleatorias sin duplicados de contenido
        selected_questions = self._select_unique_questions(
            available_questions, request.num_preguntas
        )

        # 3. Crear ID único para el examen
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"

        # 4. Asignar IDs únicos temporales a las preguntas para evitar colisiones
        # Esto resuelve el problema de IDs duplicados entre diferentes tests
        questions_with_unique_ids = []
        for i, question in enumerate(selected_questions):
            # Crear una copia de la pregunta con ID único temporal
            unique_question = Question(
                id=f"{exam_id}_q{i + 1}",  # ID único: exam_abc123_q1, exam_abc123_q2, etc.
                enunciado=question.enunciado,
                opciones=question.opciones,
                respuesta_correcta=question.respuesta_correcta,
                metadata=question.metadata,
            )
            questions_with_unique_ids.append(unique_question)

        # 5. Guardar examen completo en memoria (con respuestas correctas)
        cached_exam = CachedExam(
            questions=questions_with_unique_ids,
            metadata=request,
            timestamp=datetime.now(),
        )
        self.active_exams[exam_id] = cached_exam

        # 6. Crear versión para cliente (con o sin respuestas correctas según el tipo)
        if request.tipo_examen in EXAM_TYPES_WITH_CORRECT_ANSWERS:
            # Para exámenes de práctica (normal y per), incluir respuestas correctas
            client_questions = [
                QuestionForClient(
                    id=q.id,
                    enunciado=q.enunciado,
                    opciones=q.opciones,
                    metadata=q.metadata,
                    respuesta_correcta=q.respuesta_correcta,
                )
                for q in questions_with_unique_ids
            ]
        else:
            # Para simulacros y otros tipos, no incluir respuestas correctas
            client_questions = [
                QuestionForClient(
                    id=q.id,
                    enunciado=q.enunciado,
                    opciones=q.opciones,
                    metadata=q.metadata,
                )
                for q in questions_with_unique_ids
            ]

        # 7. Limpiar exámenes expirados
        self._cleanup_expired_exams()

        print(f"✅ Examen generado con ID: {exam_id}")
        print(
            f"🔑 IDs únicos asignados: {[q.id for q in questions_with_unique_ids[:3]]}..."
        )

        return GeneratedExam(
            exam_id=exam_id, questions=client_questions, metadata=request
        )

    def correct_exam(self, submission: ExamSubmission) -> ExamResult:
        """
        Corrige un examen enviado por el cliente.

        Args:
            submission: Respuestas del examen

        Returns:
            Resultado detallado de la corrección
        """
        print(f"📝 Corrigiendo examen: {submission.exam_id}")

        # 1. Buscar el examen en memoria
        if submission.exam_id not in self.active_exams:
            raise ValueError(f"Examen {submission.exam_id} no encontrado o expirado")

        cached_exam = self.active_exams[submission.exam_id]

        # 2. Corregir cada pregunta
        question_results = []
        category_stats = {}

        for question in cached_exam.questions:
            # Obtener respuesta del usuario
            user_answer = submission.respuestas.get(question.id)

            # Verificar si es correcta (soporta múltiples respuestas correctas)
            is_correct = self._is_answer_correct(
                user_answer, question.respuesta_correcta
            )

            # Obtener textos de las opciones
            texto_respuesta_usuario = None
            if user_answer and user_answer in question.opciones:
                texto_respuesta_usuario = question.opciones[user_answer]

            # Obtener lista de respuestas correctas
            respuestas_correctas_lista = self._get_correct_answers_list(
                question.respuesta_correcta
            )
            es_anulada = question.respuesta_correcta.lower() == "anulada"

            # Texto de la primera respuesta correcta (para compatibilidad)
            primera_correcta = (
                respuestas_correctas_lista[0]
                if respuestas_correctas_lista
                else question.respuesta_correcta
            )
            texto_respuesta_correcta = question.opciones.get(
                primera_correcta, "Opción no encontrada"
            )

            # Textos de todas las respuestas correctas
            textos_respuestas_correctas = {}
            for respuesta in respuestas_correctas_lista:
                if respuesta in question.opciones:
                    textos_respuestas_correctas[respuesta] = question.opciones[
                        respuesta
                    ]

            # Crear resultado de la pregunta
            question_result = QuestionResult(
                question_id=question.id,
                respuesta_usuario=user_answer,
                respuesta_correcta=question.respuesta_correcta,
                respuestas_correctas_lista=respuestas_correctas_lista,
                texto_respuesta_usuario=texto_respuesta_usuario,
                texto_respuesta_correcta=texto_respuesta_correcta,
                textos_respuestas_correctas=textos_respuestas_correctas,
                es_correcta=is_correct,
                es_anulada=es_anulada,
                enunciado=question.enunciado,
                opciones=question.opciones,
                metadata=question.metadata,
            )
            question_results.append(question_result)

            # Actualizar estadísticas por categoría
            category = question.metadata.categoria
            if category not in category_stats:
                category_stats[category] = {"correctas": 0, "total": 0}

            category_stats[category]["total"] += 1
            if is_correct:
                category_stats[category]["correctas"] += 1

        # 3. Calcular resultados finales
        total_correct = sum(1 for qr in question_results if qr.es_correcta)
        total_questions = len(question_results)

        # Early return si no hay preguntas (evitar división por cero)
        if total_questions == 0:
            # Limpiar el examen de memoria (ya se "corrigió")
            del self.active_exams[submission.exam_id]
            print("✅ Examen corregido: 0/0 (0.0%)")
            return ExamResult(
                puntuacion_total="0/0",
                porcentaje=0.0,
                aprobado=False,
                desglose_por_categoria={},
                preguntas_detalle=[],
            )

        percentage = (total_correct / total_questions) * 100

        # 4. Crear resultados por categoría
        category_results = {}
        for category, stats in category_stats.items():
            cat_percentage = (stats["correctas"] / stats["total"]) * 100
            category_results[category] = CategoryResult(
                correctas=stats["correctas"],
                total=stats["total"],
                porcentaje=round(cat_percentage, 2),
            )

        # 5. Determinar si aprobó (65% mínimo)
        passed = percentage >= settings.passing_score_percentage

        # 6. Limpiar el examen de memoria (ya se corrigió)
        del self.active_exams[submission.exam_id]

        print(
            f"✅ Examen corregido: {total_correct}/{total_questions} ({percentage:.1f}%)"
        )

        # Asegurar que las claves sean str, nunca None
        clean_category_results = {
            str(k): v for k, v in category_results.items() if k is not None
        }
        return ExamResult(
            puntuacion_total=f"{total_correct}/{total_questions}",
            porcentaje=round(percentage, 2),
            aprobado=passed,
            desglose_por_categoria=clean_category_results,
            preguntas_detalle=question_results,
        )

    def _cleanup_expired_exams(self) -> None:
        """
        Limpia exámenes expirados de la memoria.

        Los exámenes que llevan más de 2 horas se eliminan automáticamente.
        """
        now = datetime.now()
        expired_exams = [
            exam_id
            for exam_id, exam in self.active_exams.items()
            if now - exam.timestamp > self.exam_ttl
        ]

        for exam_id in expired_exams:
            del self.active_exams[exam_id]

        if expired_exams:
            print(f"🧹 Limpiados {len(expired_exams)} exámenes expirados")

    def get_active_exams_count(self) -> int:
        """
        Devuelve el número de exámenes activos en memoria.

        Returns:
            Número de exámenes activos
        """
        self._cleanup_expired_exams()
        return len(self.active_exams)

    def get_service_stats(self) -> Dict:
        """
        Devuelve estadísticas del servicio.

        Returns:
            Diccionario con estadísticas
        """
        return {
            "examenes_activos": self.get_active_exams_count(),
            "ttl_examenes": f"{self.exam_ttl.total_seconds() / 3600} horas",
        }

    def generate_simulacro_exam(self, request: ExamGenerationRequest) -> GeneratedExam:
        """
        Genera un simulacro de examen con distribución fija por categoría.
        Ignora la selección de categorías del usuario, pero respeta años y comunidades.

        Las preguntas se organizan por categorías (como en un examen real):
        - Primero aparecen todas las preguntas de la categoría 1
        - Luego las de la categoría 2, etc.
        - Dentro de cada categoría, las preguntas están en orden aleatorio
        """
        print("🎯 Generando simulacro de examen: distribución fija por categorías")
        distribution = settings.simulacro_distribution

        # Filtrar preguntas por años y comunidades (si se especifican)
        available_questions = self.question_loader.get_questions_by_criteria(
            categorias=[],  # No filtrar por categorías en simulacro
            anios=request.anios or [],
            comunidades=request.comunidades or [],
            tipo_examen=request.tipo_examen,
        )

        # Agrupar preguntas por id de categoría (numérico)
        questions_by_cat: dict[int, list] = {}
        for q in available_questions:
            # El id de categoría es numérico en el banco, pero puede estar como str
            cat_id = None
            if hasattr(q.metadata, "categoria") and q.metadata.categoria:
                try:
                    cat_id = int(q.metadata.categoria)
                except (ValueError, TypeError):
                    continue
            if cat_id is not None:
                questions_by_cat.setdefault(cat_id, []).append(q)

        # Seleccionar preguntas según la distribución, agrupadas por categoría
        selected_questions = []

        # Procesar las categorías en orden numérico para mantener estructura del examen real
        for cat_id in sorted(distribution.keys()):  # pylint: disable=no-member
            num_questions = distribution[cat_id]
            cat_questions = questions_by_cat.get(cat_id, [])

            if len(cat_questions) < num_questions:
                raise ValueError(
                    f"No hay suficientes preguntas en la categoría {cat_id} "
                    f"para el simulacro"
                )

            # Seleccionar preguntas únicas aleatorias de esta categoría
            selected_category_questions = self._select_unique_questions(
                cat_questions, num_questions
            )

            # Mezclar el orden dentro de la categoría
            random.shuffle(selected_category_questions)

            # Añadir las preguntas de esta categoría al final del examen
            selected_questions.extend(selected_category_questions)

        # NO mezclamos el orden final para mantener agrupación por categorías
        # Las preguntas ya están aleatorias dentro de cada categoría

        exam_id = f"simulacro_{uuid.uuid4().hex[:8]}"
        cached_exam = CachedExam(
            questions=selected_questions, metadata=request, timestamp=datetime.now()
        )
        self.active_exams[exam_id] = cached_exam

        client_questions = [
            QuestionForClient(
                id=q.id, enunciado=q.enunciado, opciones=q.opciones, metadata=q.metadata
            )
            for q in selected_questions
        ]

        self._cleanup_expired_exams()
        print(
            f"✅ Simulacro generado con ID: {exam_id} "
            f"(preguntas agrupadas por categorías)"
        )
        return GeneratedExam(
            exam_id=exam_id, questions=client_questions, metadata=request
        )

    def generate_specific_exam(self, exam_identifier: str) -> GeneratedExam:
        """
        Genera un examen específico basado en el identificador del examen.

        Args:
            exam_identifier: Identificador único del examen (ej: 'madrid_2024_abril_test01')

        Returns:
            Examen específico generado listo para enviar al cliente

        Raises:
            ValueError: Si no se encuentra el examen especificado
        """
        print(f"🎯 Generando examen específico: {exam_identifier}")

        # 1. Obtener todas las preguntas del examen específico
        specific_questions = self.question_loader.get_questions_for_specific_exam(
            exam_identifier
        )

        if not specific_questions:
            raise ValueError(
                f"No se encontraron preguntas para el examen: {exam_identifier}"
            )

        # 2. Crear ID único para esta instancia del examen
        exam_id = f"specific_{uuid.uuid4().hex[:8]}"

        # 3. Asignar IDs únicos temporales a las preguntas para evitar colisiones
        questions_with_unique_ids = []
        for i, question in enumerate(specific_questions):
            # Crear una copia de la pregunta con ID único temporal
            unique_question = Question(
                id=f"{exam_id}_q{i + 1}",  # ID único: specific_abc123_q1, specific_abc123_q2, etc.
                enunciado=question.enunciado,
                opciones=question.opciones,
                respuesta_correcta=question.respuesta_correcta,
                metadata=question.metadata,
            )
            questions_with_unique_ids.append(unique_question)

        # 4. Crear metadata de request para compatibilidad
        request_metadata = ExamGenerationRequest(
            num_preguntas=len(questions_with_unique_ids),
            categorias=None,  # No aplica para exámenes específicos
            anios=[specific_questions[0].metadata.year],
            comunidades=[specific_questions[0].metadata.community],
            tipo_examen="especifico",
        )

        # 5. Guardar examen completo en memoria (con respuestas correctas)
        cached_exam = CachedExam(
            questions=questions_with_unique_ids,
            metadata=request_metadata,
            timestamp=datetime.now(),
        )
        self.active_exams[exam_id] = cached_exam

        # 6. Crear versión para cliente (sin respuestas correctas)
        client_questions = [
            QuestionForClient(
                id=q.id, enunciado=q.enunciado, opciones=q.opciones, metadata=q.metadata
            )
            for q in questions_with_unique_ids
        ]

        # 7. Limpiar exámenes expirados
        self._cleanup_expired_exams()

        print(f"✅ Examen específico generado con ID: {exam_id}")
        print(
            f"📝 Examen original: {exam_identifier} con {len(questions_with_unique_ids)} preguntas"
        )

        return GeneratedExam(
            exam_id=exam_id, questions=client_questions, metadata=request_metadata
        )

    def _is_answer_correct(
        self, user_answer: Optional[str], correct_answer: str
    ) -> bool:
        """
        Verifica si la respuesta del usuario es correcta.
        Soporta múltiples respuestas correctas y preguntas anuladas.

        Args:
            user_answer: Respuesta del usuario (ej: 'a', 'b', etc.)
            correct_answer: Respuesta(s) correcta(s) (ej: 'a', 'a,b', 'anulada')

        Returns:
            True si la respuesta es correcta, False en caso contrario
        """
        if not user_answer:
            return False

        # Normalizar respuestas a minúsculas
        user_answer = user_answer.lower()
        correct_answer = correct_answer.lower()

        # Caso especial: pregunta anulada - cualquier respuesta es válida
        if correct_answer == "anulada":
            return True

        # Si hay múltiples respuestas correctas separadas por comas
        if "," in correct_answer:
            valid_answers = [answer.strip() for answer in correct_answer.split(",")]
            return user_answer in valid_answers

        # Caso simple: una sola respuesta correcta
        return user_answer == correct_answer

    def _get_correct_answers_list(self, correct_answer: str) -> List[str]:
        """
        Obtiene la lista de respuestas correctas desde el string de respuesta.

        Args:
            correct_answer: Respuesta(s) correcta(s) (ej: 'a', 'a,b', 'anulada')

        Returns:
            Lista de respuestas correctas válidas
        """
        correct_answer = correct_answer.lower()

        # Caso especial: pregunta anulada
        if correct_answer == "anulada":
            return ["a", "b", "c", "d"]  # Todas las opciones son válidas

        # Si hay múltiples respuestas separadas por comas
        if "," in correct_answer:
            return [answer.strip() for answer in correct_answer.split(",")]

        # Caso simple: una sola respuesta
        return [correct_answer]


# Instancia global del servicio de exámenes
exam_service = ExamService()
