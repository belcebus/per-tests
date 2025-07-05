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
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.schemas import (
    Question, QuestionForClient, ExamGenerationRequest, 
    GeneratedExam, CachedExam, ExamSubmission, ExamResult,
    CategoryResult, QuestionResult
)
from app.services.question_loader import question_loader
from config.settings import settings


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
    
    def generate_exam(self, request: ExamGenerationRequest) -> GeneratedExam:
        """
        Genera un nuevo examen según los criterios especificados.
        
        Args:
            request: Criterios para generar el examen
            
        Returns:
            Examen generado listo para enviar al cliente
        """
        print(f"🎯 Generando examen: {request.num_preguntas} preguntas")
        
        # 1. Obtener preguntas que cumplen los criterios
        available_questions = question_loader.get_questions_by_criteria(
            categorias=request.categorias,
            años=request.años,
            comunidades=request.comunidades,
            tipo_examen=request.tipo_examen
        )
        
        if len(available_questions) < request.num_preguntas:
            raise ValueError(
                f"No hay suficientes preguntas. "
                f"Disponibles: {len(available_questions)}, "
                f"Solicitadas: {request.num_preguntas}"
            )
        
        # 2. Seleccionar preguntas aleatorias
        selected_questions = random.sample(available_questions, request.num_preguntas)
        
        # 3. Crear ID único para el examen
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"
        
        # 4. Guardar examen completo en memoria (con respuestas correctas)
        cached_exam = CachedExam(
            questions=selected_questions,
            metadata=request,
            timestamp=datetime.now()
        )
        self.active_exams[exam_id] = cached_exam
        
        # 5. Crear versión para cliente (sin respuestas correctas)
        client_questions = [
            QuestionForClient(
                id=q.id,
                enunciado=q.enunciado,
                opciones=q.opciones,
                metadata=q.metadata
            )
            for q in selected_questions
        ]
        
        # 6. Limpiar exámenes expirados
        self._cleanup_expired_exams()
        
        print(f"✅ Examen generado con ID: {exam_id}")
        
        return GeneratedExam(
            exam_id=exam_id,
            questions=client_questions,
            metadata=request
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
            
            # Verificar si es correcta
            is_correct = user_answer == question.respuesta_correcta
            
            # Obtener textos de las opciones
            texto_respuesta_usuario = None
            if user_answer and user_answer in question.opciones:
                texto_respuesta_usuario = question.opciones[user_answer]
            
            texto_respuesta_correcta = question.opciones.get(question.respuesta_correcta, "Opción no encontrada")
            
            # Crear resultado de la pregunta
            question_result = QuestionResult(
                question_id=question.id,
                respuesta_usuario=user_answer,
                respuesta_correcta=question.respuesta_correcta,
                texto_respuesta_usuario=texto_respuesta_usuario,
                texto_respuesta_correcta=texto_respuesta_correcta,
                es_correcta=is_correct,
                enunciado=question.enunciado,
                opciones=question.opciones,
                metadata=question.metadata
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
        percentage = (total_correct / total_questions) * 100
        
        # 4. Crear resultados por categoría
        category_results = {}
        for category, stats in category_stats.items():
            cat_percentage = (stats["correctas"] / stats["total"]) * 100
            category_results[category] = CategoryResult(
                correctas=stats["correctas"],
                total=stats["total"],
                porcentaje=round(cat_percentage, 2)
            )
        
        # 5. Determinar si aprobó (65% mínimo)
        passed = percentage >= 65.0
        
        # 6. Limpiar el examen de memoria (ya se corrigió)
        del self.active_exams[submission.exam_id]
        
        print(f"✅ Examen corregido: {total_correct}/{total_questions} ({percentage:.1f}%)")
        
        return ExamResult(
            puntuacion_total=f"{total_correct}/{total_questions}",
            porcentaje=round(percentage, 2),
            aprobado=passed,
            desglose_por_categoria=category_results,
            preguntas_detalle=question_results
        )
    
    def _cleanup_expired_exams(self) -> None:
        """
        Limpia exámenes expirados de la memoria.
        
        Los exámenes que llevan más de 2 horas se eliminan automáticamente.
        """
        now = datetime.now()
        expired_exams = [
            exam_id for exam_id, exam in self.active_exams.items()
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
            "ttl_examenes": f"{self.exam_ttl.total_seconds() / 3600} horas"
        }
    
    def generate_simulacro_exam(self, request: ExamGenerationRequest) -> GeneratedExam:
        """
        Genera un simulacro de examen con distribución fija por categoría.
        Ignora la selección de categorías del usuario.
        """
        print(f"🎯 Generando simulacro de examen: distribución fija")
        distribution = settings.simulacro_distribution
        available_questions = question_loader.all_questions.copy()
        # Agrupar preguntas por id de categoría (numérico)
        questions_by_cat = {}
        for q in available_questions:
            # El id de categoría es numérico en el banco, pero puede estar como str
            cat_id = None
            if hasattr(q.metadata, 'categoria') and q.metadata.categoria:
                try:
                    cat_id = int(q.metadata.categoria)
                except Exception:
                    continue
            if cat_id is not None:
                questions_by_cat.setdefault(cat_id, []).append(q)
        # Seleccionar preguntas según la distribución
        selected_questions = []
        for cat_id, num in distribution.items():
            cat_questions = questions_by_cat.get(cat_id, [])
            if len(cat_questions) < num:
                raise ValueError(f"No hay suficientes preguntas en la categoría {cat_id} para el simulacro")
            selected_questions.extend(random.sample(cat_questions, num))
        # Mezclar el orden final
        random.shuffle(selected_questions)
        exam_id = f"simulacro_{uuid.uuid4().hex[:8]}"
        cached_exam = CachedExam(
            questions=selected_questions,
            metadata=request,
            timestamp=datetime.now()
        )
        self.active_exams[exam_id] = cached_exam
        client_questions = [
            QuestionForClient(
                id=q.id,
                enunciado=q.enunciado,
                opciones=q.opciones,
                metadata=q.metadata
            ) for q in selected_questions
        ]
        self._cleanup_expired_exams()
        print(f"✅ Simulacro generado con ID: {exam_id}")
        return GeneratedExam(
            exam_id=exam_id,
            questions=client_questions,
            metadata=request
        )


# Instancia global del servicio de exámenes
exam_service = ExamService()
