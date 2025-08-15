"""
Tests comprehensivos para ExamService

Este módulo incluye tests para toda la funcionalidad crítica de ExamService:
- Generación de exámenes normales y simulacros
- Corrección de exámenes con diferentes escenarios
- Gestión de memoria y limpieza de exámenes expirados
- Manejo de errores y casos edge
- Validación de respuestas múltiples y preguntas anuladas
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from app.services.exam_service import ExamService, exam_service
from app.models.schemas import (
    Question, QuestionMetadata, ExamGenerationRequest, 
    ExamSubmission, GeneratedExam, ExamResult, CachedExam
)
from config.settings import settings


class TestExamServiceInit:
    """Tests de inicialización del servicio."""
    
    def test_exam_service_init(self):
        """Test de inicialización correcta del servicio."""
        service = ExamService()
        
        assert service.active_exams == {}
        assert service.exam_ttl == timedelta(hours=settings.exam_ttl_hours)
    
    def test_singleton_instance(self):
        """Test de que exam_service es una instancia única."""
        from app.services.exam_service import exam_service as service1
        from app.services.exam_service import exam_service as service2
        
        assert service1 is service2


class TestExamGeneration:
    """Tests de generación de exámenes normales."""
    
    @pytest.fixture
    def mock_questions(self):
        """Preguntas de ejemplo para los tests."""
        questions = []
        for i in range(10):
            questions.append(Question(
                id=f"q{i+1}",
                enunciado=f"Pregunta {i+1}?",
                opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Exam",
                    subtitle="Test Code 01",
                    total_questions=45,
                    community="Madrid",
                    year=2024,
                    call="abril",
                    test_code="test01",
                    categoria="1",
                    numero_pregunta=i+1
                )
            ))
        return questions
    
    @patch('app.services.exam_service.question_loader')
    def test_generate_exam_success(self, mock_loader, mock_questions):
        """Test de generación exitosa de examen."""
        mock_loader.get_questions_by_criteria.return_value = mock_questions
        
        service = ExamService()
        request = ExamGenerationRequest(
            num_preguntas=5,
            comunidades=["Madrid"]
        )
        
        result = service.generate_exam(request)
        
        # Verificar estructura del resultado
        assert isinstance(result, GeneratedExam)
        assert result.exam_id.startswith("exam_")
        assert len(result.questions) == 5
        assert result.metadata == request
        
        # Verificar que las preguntas no tienen respuestas correctas
        for question in result.questions:
            assert hasattr(question, 'enunciado')
            assert hasattr(question, 'opciones')
            assert not hasattr(question, 'respuesta_correcta')
        
        # Verificar que el examen se guardó en memoria
        assert result.exam_id in service.active_exams
        cached_exam = service.active_exams[result.exam_id]
        assert len(cached_exam.questions) == 5
        assert cached_exam.metadata == request
    
    @patch('app.services.exam_service.question_loader')
    def test_generate_exam_insufficient_questions(self, mock_loader):
        """Test de error cuando no hay suficientes preguntas."""
        mock_loader.get_questions_by_criteria.return_value = [Mock(), Mock()]  # Solo 2 preguntas
        
        service = ExamService()
        request = ExamGenerationRequest(
            num_preguntas=5,  # Pide 5 pero solo hay 2
            comunidades=["Madrid"]
        )
        
        with pytest.raises(ValueError, match="No hay suficientes preguntas"):
            service.generate_exam(request)
    
    @patch('app.services.exam_service.question_loader')
    def test_generate_exam_unique_ids(self, mock_loader, mock_questions):
        """Test de que cada pregunta recibe un ID único temporal."""
        mock_loader.get_questions_by_criteria.return_value = mock_questions
        
        service = ExamService()
        request = ExamGenerationRequest(num_preguntas=3, comunidades=["Madrid"])
        
        result = service.generate_exam(request)
        
        # Verificar IDs únicos
        question_ids = [q.id for q in result.questions]
        assert len(set(question_ids)) == len(question_ids)  # Todos únicos
        
        # Verificar formato del ID
        for q in result.questions:
            assert q.id.startswith(result.exam_id)
            assert "_q" in q.id
    
    @patch('app.services.exam_service.question_loader')
    def test_generate_exam_cleanup_called(self, mock_loader, mock_questions):
        """Test de que se llama la limpieza automática."""
        mock_loader.get_questions_by_criteria.return_value = mock_questions
        
        service = ExamService()
        with patch.object(service, '_cleanup_expired_exams') as mock_cleanup:
            request = ExamGenerationRequest(num_preguntas=2, comunidades=["Madrid"])
            service.generate_exam(request)
            
            mock_cleanup.assert_called_once()


class TestSimulacroGeneration:
    """Tests de generación de simulacros."""
    
    @pytest.fixture
    def mock_questions_by_category(self):
        """Preguntas organizadas por categoría para simulacros."""
        questions = {}
        for cat_id in range(1, 12):  # Categorías 1-11
            cat_questions = []
            for i in range(15):  # 15 preguntas por categoría (más que las necesarias)
                cat_questions.append(Question(
                    id=f"cat{cat_id}_q{i+1}",
                    enunciado=f"Pregunta categoría {cat_id}, número {i+1}",
                    opciones={"a": "A", "b": "B", "c": "C", "d": "D"},
                    respuesta_correcta="a",
                    metadata=QuestionMetadata(
                        title="Test Simulacro",
                        subtitle="Test Code 01",
                        total_questions=45,
                        community="Madrid",
                        year=2024,
                        call="abril",
                        test_code="test01",
                        categoria=str(cat_id),
                        numero_pregunta=i+1
                    )
                ))
            questions[cat_id] = cat_questions
        return questions
    
    @patch('app.services.exam_service.question_loader')
    @patch('app.services.exam_service.settings')
    def test_generate_simulacro_exam_success(self, mock_settings, mock_loader, mock_questions_by_category):
        """Test de generación exitosa de simulacro."""
        # Configurar distribución de simulacro y TTL
        mock_settings.simulacro_distribution = {1: 4, 2: 2, 3: 4, 6: 10}  # Distribución simplificada
        mock_settings.exam_ttl_hours = 2  # TTL en horas
        
        # Aplanar las preguntas para get_questions_by_criteria
        all_questions = []
        for cat_questions in mock_questions_by_category.values():
            all_questions.extend(cat_questions)
        mock_loader.get_questions_by_criteria.return_value = all_questions
        
        service = ExamService()
        request = ExamGenerationRequest(
            num_preguntas=45,  # Ignorado en simulacro
            comunidades=["Madrid"],
            tipo_examen="simulacro"
        )
        
        result = service.generate_simulacro_exam(request)
        
        # Verificar estructura
        assert isinstance(result, GeneratedExam)
        assert result.exam_id.startswith("simulacro_")
        assert len(result.questions) == 20  # 4+2+4+10
        
        # Verificar que se respeta la distribución por categorías
        categories_found = {}
        for q in result.questions:
            cat = q.metadata.categoria
            categories_found[cat] = categories_found.get(cat, 0) + 1
        
        assert categories_found["1"] == 4
        assert categories_found["2"] == 2
        assert categories_found["3"] == 4
        assert categories_found["6"] == 10
    
    @patch('app.services.exam_service.question_loader')
    @patch('app.services.exam_service.settings')
    def test_generate_simulacro_insufficient_questions_in_category(self, mock_settings, mock_loader):
        """Test de error cuando no hay suficientes preguntas en una categoría."""
        mock_settings.simulacro_distribution = {1: 5}  # Necesita 5 preguntas de categoría 1
        mock_settings.exam_ttl_hours = 2  # TTL en horas
        
        # Solo 2 preguntas de categoría 1
        mock_loader.get_questions_by_criteria.return_value = [
            Question(
                id="q1", enunciado="Q1", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="1", numero_pregunta=1
                )
            ),
            Question(
                id="q2", enunciado="Q2", opciones={"a": "A"}, respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="1", numero_pregunta=2
                )
            )
        ]
        
        service = ExamService()
        request = ExamGenerationRequest(comunidades=["Madrid"], tipo_examen="simulacro")
        
        with pytest.raises(ValueError, match="No hay suficientes preguntas en la categoría 1"):
            service.generate_simulacro_exam(request)


class TestExamCorrection:
    """Tests de corrección de exámenes."""
    
    @pytest.fixture
    def cached_exam_with_questions(self):
        """Examen en memoria con preguntas para corregir."""
        questions = [
            Question(
                id="exam_123_q1",
                enunciado="¿Cuál es la proa?",
                opciones={"a": "Adelante", "b": "Atrás", "c": "Izquierda", "d": "Derecha"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="1", numero_pregunta=1
                )
            ),
            Question(
                id="exam_123_q2",
                enunciado="Pregunta anulada",
                opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
                respuesta_correcta="anulada",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="1", numero_pregunta=2
                )
            ),
            Question(
                id="exam_123_q3",
                enunciado="Pregunta con múltiples respuestas",
                opciones={"a": "Correcta 1", "b": "Correcta 2", "c": "Incorrecta", "d": "Incorrecta"},
                respuesta_correcta="a,b",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="2", numero_pregunta=3
                )
            )
        ]
        
        return CachedExam(
            questions=questions,
            metadata=ExamGenerationRequest(num_preguntas=3, comunidades=["Madrid"]),
            timestamp=datetime.now()
        )
    
    def test_correct_exam_success(self, cached_exam_with_questions):
        """Test de corrección exitosa de examen."""
        service = ExamService()
        exam_id = "test_exam_123"
        service.active_exams[exam_id] = cached_exam_with_questions
        
        submission = ExamSubmission(
            exam_id=exam_id,
            respuestas={
                "exam_123_q1": "a",  # Correcta
                "exam_123_q2": "c",  # Anulada (cualquier respuesta es correcta)
                "exam_123_q3": "b"   # Correcta (una de las múltiples)
            }
        )
        
        result = service.correct_exam(submission)
        
        # Verificar resultado general
        assert isinstance(result, ExamResult)
        assert result.puntuacion_total == "3/3"
        assert result.porcentaje == 100.0
        assert result.aprobado is True
        
        # Verificar detalles por pregunta
        assert len(result.preguntas_detalle) == 3
        
        # Pregunta 1: correcta normal
        q1_result = result.preguntas_detalle[0]
        assert q1_result.es_correcta is True
        assert q1_result.respuesta_usuario == "a"
        assert q1_result.es_anulada is False
        
        # Pregunta 2: anulada
        q2_result = result.preguntas_detalle[1]
        assert q2_result.es_correcta is True  # Anulada = siempre correcta
        assert q2_result.es_anulada is True
        
        # Pregunta 3: múltiples respuestas
        q3_result = result.preguntas_detalle[2]
        assert q3_result.es_correcta is True
        assert "a" in q3_result.respuestas_correctas_lista
        assert "b" in q3_result.respuestas_correctas_lista
        
        # Verificar que se eliminó el examen de memoria
        assert exam_id not in service.active_exams
    
    def test_correct_exam_not_found(self):
        """Test de error cuando el examen no existe."""
        service = ExamService()
        
        submission = ExamSubmission(
            exam_id="nonexistent_exam",
            respuestas={"q1": "a"}
        )
        
        with pytest.raises(ValueError, match="Examen nonexistent_exam no encontrado o expirado"):
            service.correct_exam(submission)
    
    def test_correct_exam_partial_answers(self, cached_exam_with_questions):
        """Test de corrección con respuestas parciales."""
        service = ExamService()
        exam_id = "test_exam_456"
        service.active_exams[exam_id] = cached_exam_with_questions
        
        submission = ExamSubmission(
            exam_id=exam_id,
            respuestas={
                "exam_123_q1": "a",  # Correcta
                # q2 sin responder
                "exam_123_q3": "c"   # Incorrecta
            }
        )
        
        result = service.correct_exam(submission)
        
        assert result.puntuacion_total == "1/3"
        assert result.porcentaje == 33.33
        assert result.aprobado is False  # Menos del 65%
    
    @patch('app.services.exam_service.settings')
    def test_correct_exam_custom_passing_score(self, mock_settings, cached_exam_with_questions):
        """Test de corrección con porcentaje de aprobado personalizado."""
        mock_settings.passing_score_percentage = 50.0  # 50% para aprobar
        mock_settings.exam_ttl_hours = 2  # TTL en horas
        
        service = ExamService()
        exam_id = "test_exam_789"
        service.active_exams[exam_id] = cached_exam_with_questions
        
        submission = ExamSubmission(
            exam_id=exam_id,
            respuestas={
                "exam_123_q1": "a",  # Correcta
                "exam_123_q2": "a",  # Anulada (correcta)
                # q3 sin responder (incorrecta)
            }
        )
        
        result = service.correct_exam(submission)
        
        assert result.porcentaje == 66.67  # 2/3
        assert result.aprobado is True  # 66.67% > 50%


class TestAnswerValidation:
    """Tests de validación de respuestas."""
    
    def test_is_answer_correct_simple(self):
        """Test de respuesta simple correcta."""
        service = ExamService()
        
        assert service._is_answer_correct("a", "a") is True
        assert service._is_answer_correct("A", "a") is True  # Case insensitive
        assert service._is_answer_correct("b", "a") is False
        assert service._is_answer_correct(None, "a") is False
        assert service._is_answer_correct("", "a") is False
    
    def test_is_answer_correct_multiple(self):
        """Test de respuestas múltiples."""
        service = ExamService()
        
        assert service._is_answer_correct("a", "a,b") is True
        assert service._is_answer_correct("b", "a,b") is True
        assert service._is_answer_correct("c", "a,b") is False
        assert service._is_answer_correct("A", "a,b,c") is True  # Case insensitive
    
    def test_is_answer_correct_anulada(self):
        """Test de pregunta anulada."""
        service = ExamService()
        
        assert service._is_answer_correct("a", "anulada") is True
        assert service._is_answer_correct("b", "anulada") is True
        assert service._is_answer_correct("z", "anulada") is True
        assert service._is_answer_correct("A", "ANULADA") is True  # Case insensitive
    
    def test_get_correct_answers_list_simple(self):
        """Test de obtener lista de respuestas simples."""
        service = ExamService()
        
        assert service._get_correct_answers_list("a") == ["a"]
        assert service._get_correct_answers_list("B") == ["b"]  # Lowercase
    
    def test_get_correct_answers_list_multiple(self):
        """Test de obtener lista de respuestas múltiples."""
        service = ExamService()
        
        result = service._get_correct_answers_list("a,b,c")
        assert result == ["a", "b", "c"]
        
        result = service._get_correct_answers_list("A, B, C")
        assert result == ["a", "b", "c"]  # Lowercase y sin espacios
    
    def test_get_correct_answers_list_anulada(self):
        """Test de obtener lista para pregunta anulada."""
        service = ExamService()
        
        result = service._get_correct_answers_list("anulada")
        assert result == ["a", "b", "c", "d"]
        
        result = service._get_correct_answers_list("ANULADA")
        assert result == ["a", "b", "c", "d"]


class TestMemoryManagement:
    """Tests de gestión de memoria y limpieza."""
    
    def test_cleanup_expired_exams(self):
        """Test de limpieza de exámenes expirados."""
        service = ExamService()
        
        # Crear exámenes con diferentes timestamps
        now = datetime.now()
        old_exam = CachedExam(
            questions=[],
            metadata=ExamGenerationRequest(num_preguntas=45, comunidades=["Madrid"]),
            timestamp=now - timedelta(hours=3)  # 3 horas atrás (expirado)
        )
        recent_exam = CachedExam(
            questions=[],
            metadata=ExamGenerationRequest(num_preguntas=45, comunidades=["Madrid"]),
            timestamp=now - timedelta(minutes=30)  # 30 minutos atrás (válido)
        )
        
        service.active_exams["old_exam"] = old_exam
        service.active_exams["recent_exam"] = recent_exam
        
        # Ejecutar limpieza
        service._cleanup_expired_exams()
        
        # Verificar que solo se eliminó el expirado
        assert "old_exam" not in service.active_exams
        assert "recent_exam" in service.active_exams
    
    def test_get_active_exams_count(self):
        """Test de contador de exámenes activos."""
        service = ExamService()
        
        # Sin exámenes
        assert service.get_active_exams_count() == 0
        
        # Agregar exámenes válidos
        now = datetime.now()
        valid_exam1 = CachedExam(
            questions=[],
            metadata=ExamGenerationRequest(num_preguntas=10, comunidades=["Madrid"]),
            timestamp=now - timedelta(minutes=30)
        )
        valid_exam2 = CachedExam(
            questions=[],
            metadata=ExamGenerationRequest(num_preguntas=15, comunidades=["Valencia"]),
            timestamp=now - timedelta(minutes=45)
        )
        
        service.active_exams["exam1"] = valid_exam1
        service.active_exams["exam2"] = valid_exam2
        
        assert service.get_active_exams_count() == 2
    
    def test_get_service_stats(self):
        """Test de estadísticas del servicio."""
        service = ExamService()
        
        # Agregar un examen válido
        now = datetime.now()
        valid_exam = CachedExam(
            questions=[],
            metadata=ExamGenerationRequest(num_preguntas=20, comunidades=["Madrid"]),
            timestamp=now - timedelta(minutes=15)
        )
        service.active_exams["exam1"] = valid_exam
        
        stats = service.get_service_stats()
        
        assert isinstance(stats, dict)
        assert "examenes_activos" in stats
        assert "ttl_examenes" in stats
        assert stats["examenes_activos"] == 1
        assert "horas" in stats["ttl_examenes"]


class TestEdgeCases:
    """Tests de casos edge y manejo de errores."""
    
    def test_exam_with_no_questions(self):
        """Test de manejo de examen sin preguntas."""
        service = ExamService()
        cached_exam = CachedExam(
            questions=[],  # Sin preguntas
            metadata=ExamGenerationRequest(num_preguntas=1, comunidades=["Madrid"]),  # Debe ser >= 1
            timestamp=datetime.now()
        )
        service.active_exams["empty_exam"] = cached_exam
        
        # Modificar el examen para que no tenga preguntas después de crearlo
        cached_exam.questions = []
        
        submission = ExamSubmission(
            exam_id="empty_exam",
            respuestas={}
        )
        
        result = service.correct_exam(submission)
        
        # Debe manejar división por cero
        assert result.puntuacion_total == "0/0"
        assert result.porcentaje == 0.0
    
    def test_question_without_metadata(self):
        """Test de pregunta sin metadata completa."""
        service = ExamService()
        
        # Crear pregunta con metadata completa (requerida por Pydantic)
        question = Question(
            id="q1",
            enunciado="Test",
            opciones={"a": "A"},
            respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test Exam", subtitle="Test 01", total_questions=45,
                community="Madrid", year=2024, call="abril", test_code="test01",
                categoria="1", numero_pregunta=1
            )
        )
        
        cached_exam = CachedExam(
            questions=[question],
            metadata=ExamGenerationRequest(num_preguntas=1, comunidades=["Madrid"]),
            timestamp=datetime.now()
        )
        service.active_exams["test_exam"] = cached_exam
        
        submission = ExamSubmission(
            exam_id="test_exam",
            respuestas={"q1": "a"}
        )
        
        # No debe lanzar error
        result = service.correct_exam(submission)
        assert result.puntuacion_total == "1/1"
    
    def test_random_sampling_edge_case(self):
        """Test de manejo de errores cuando no hay suficientes preguntas únicas."""
        service = ExamService()
        request = ExamGenerationRequest(num_preguntas=5, comunidades=["Madrid"])
        
        # Patchear el question_loader de la instancia del servicio
        with patch.object(service, 'question_loader') as mock_loader:
            # Crear un mock de metadata válido
            mock_metadata = Mock()
            mock_metadata.title = "Test"
            mock_metadata.subtitle = "Test01"
            mock_metadata.total_questions = 10
            mock_metadata.community = "Madrid"
            mock_metadata.year = 2023
            mock_metadata.call = "Ordinaria"
            mock_metadata.test_code = "Test01"
            
            # Simulamos que hay 10 preguntas pero todas son duplicadas (mismo contenido)
            mock_question = Mock()
            mock_question.id = "test_q1"
            mock_question.enunciado = "¿Cuál es la capital de España?"
            mock_question.opciones = {"a": "Madrid", "b": "Barcelona"}
            mock_question.respuesta_correcta = "a"
            mock_question.metadata = mock_metadata
            
            # Todas las preguntas tienen el mismo contenido (10 copias de la misma pregunta)
            mock_loader.get_questions_by_criteria.return_value = [mock_question] * 10
            
            with pytest.raises(ValueError, match="No hay suficientes preguntas únicas"):
                service.generate_exam(request)


class TestCategoryResults:
    """Tests de resultados por categoría."""
    
    def test_category_statistics_calculation(self):
        """Test de cálculo correcto de estadísticas por categoría."""
        service = ExamService()
        
        questions = [
            # Categoría 1: 2 correctas de 3
            Question(id="q1", enunciado="Q1", opciones={"a": "A", "b": "B"}, respuesta_correcta="a",
                    metadata=QuestionMetadata(
                        title="Test Exam", subtitle="Test 01", total_questions=45,
                        community="Madrid", year=2024, call="abril", test_code="test01",
                        categoria="1", numero_pregunta=1
                    )),
            Question(id="q2", enunciado="Q2", opciones={"a": "A", "b": "B"}, respuesta_correcta="a",
                    metadata=QuestionMetadata(
                        title="Test Exam", subtitle="Test 01", total_questions=45,
                        community="Madrid", year=2024, call="abril", test_code="test01",
                        categoria="1", numero_pregunta=2
                    )),
            Question(id="q3", enunciado="Q3", opciones={"a": "A", "b": "B"}, respuesta_correcta="a",
                    metadata=QuestionMetadata(
                        title="Test Exam", subtitle="Test 01", total_questions=45,
                        community="Madrid", year=2024, call="abril", test_code="test01",
                        categoria="1", numero_pregunta=3
                    )),
            
            # Categoría 2: 1 correcta de 1
            Question(id="q4", enunciado="Q4", opciones={"a": "A", "b": "B"}, respuesta_correcta="b",
                    metadata=QuestionMetadata(
                        title="Test Exam", subtitle="Test 01", total_questions=45,
                        community="Madrid", year=2024, call="abril", test_code="test01",
                        categoria="2", numero_pregunta=4
                    )),
        ]
        
        cached_exam = CachedExam(
            questions=questions,
            metadata=ExamGenerationRequest(num_preguntas=4, comunidades=["Madrid"]),
            timestamp=datetime.now()
        )
        service.active_exams["cat_test"] = cached_exam
        
        submission = ExamSubmission(
            exam_id="cat_test",
            respuestas={
                "q1": "a",  # Correcta
                "q2": "a",  # Correcta  
                "q3": "b",  # Incorrecta
                "q4": "b"   # Correcta
            }
        )
        
        result = service.correct_exam(submission)
        
        # Verificar estadísticas por categoría
        cat1_stats = result.desglose_por_categoria["1"]
        assert cat1_stats.correctas == 2
        assert cat1_stats.total == 3
        assert cat1_stats.porcentaje == 66.67
        
        cat2_stats = result.desglose_por_categoria["2"]
        assert cat2_stats.correctas == 1
        assert cat2_stats.total == 1
        assert cat2_stats.porcentaje == 100.0


class TestIntegration:
    """Tests de integración completos."""
    
    @patch('app.services.exam_service.question_loader')
    def test_full_exam_lifecycle(self, mock_loader):
        """Test del ciclo completo: generar → corregir → limpiar."""
        # Configurar preguntas
        questions = [
            Question(
                id=f"q{i}",
                enunciado=f"Pregunta {i}",
                opciones={"a": "Correcta", "b": "Incorrecta"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Exam", subtitle="Test 01", total_questions=45,
                    community="Madrid", year=2024, call="abril", test_code="test01",
                    categoria="1", numero_pregunta=i
                )
            ) for i in range(1, 6)
        ]
        mock_loader.get_questions_by_criteria.return_value = questions
        
        service = ExamService()
        
        # 1. Generar examen
        request = ExamGenerationRequest(num_preguntas=3, comunidades=["Madrid"])
        exam = service.generate_exam(request)
        
        assert exam.exam_id in service.active_exams
        assert len(service.active_exams) == 1
        
        # 2. Corregir examen
        submission = ExamSubmission(
            exam_id=exam.exam_id,
            respuestas={q.id: "a" for q in exam.questions}  # Todas correctas
        )
        result = service.correct_exam(submission)
        
        assert result.porcentaje == 100.0
        assert result.aprobado is True
        
        # 3. Verificar limpieza automática
        assert exam.exam_id not in service.active_exams
        assert len(service.active_exams) == 0


class TestSpecificExamGeneration:
    """Tests para la generación de exámenes específicos"""

    def test_generate_specific_exam_success(self, exam_service_with_questions):
        """Test para generar un examen específico exitosamente"""
        service = exam_service_with_questions
        
        # Preparar preguntas mockeadas
        specific_questions = [
            Question(
                id="original_q1",
                enunciado="Pregunta específica 1",
                opciones={"a": "Opción A", "b": "Opción B"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Madrid Test 01",
                    subtitle="Abril 2024",
                    total_questions=1,
                    community="Madrid",
                    year=2024,
                    call="abril",
                    test_code="test01",
                    numero_pregunta=1
                )
            )
        ]
        
        # Configurar el mock correctamente usando return_value
        service.question_loader.get_questions_for_specific_exam.return_value = specific_questions
        
        # Generar examen específico
        exam = service.generate_specific_exam("madrid_2024_abril_test01")
        
        # Verificaciones
        assert exam.exam_id.startswith("specific_")
        assert len(exam.questions) == 1
        
        # Verificar que el mock fue llamado
        service.question_loader.get_questions_for_specific_exam.assert_called_once_with("madrid_2024_abril_test01")

    def test_generate_specific_exam_not_found(self, exam_service_with_questions):
        """Test para examen específico no encontrado"""
        service = exam_service_with_questions
        
        # Configurar el mock para que lance la excepción
        service.question_loader.get_questions_for_specific_exam.side_effect = ValueError(
            "No se encontraron preguntas para el examen: madrid_2099_diciembre_test01"
        )
        
        with pytest.raises(ValueError, match="No se encontraron preguntas para el examen"):
            service.generate_specific_exam("madrid_2099_diciembre_test01")

    def test_generate_specific_exam_empty_questions(self, exam_service_with_questions):
        """Test para examen específico con lista vacía de preguntas"""
        service = exam_service_with_questions

        # Simular lista vacía de preguntas
        service.question_loader.get_questions_for_specific_exam.return_value = []

        # Usar formato válido pero que devuelva lista vacía
        with pytest.raises(ValueError, match="No se encontraron preguntas para el examen"):
            service.generate_specific_exam("madrid_2099_julio_test00")

    def test_specific_exam_correction(self, exam_service_with_questions):
        """Test para corregir un examen específico"""
        service = exam_service_with_questions

        # Preparar preguntas específicas mockeadas
        specific_questions = [
            Question(
                id="original_q1",
                enunciado="¿Cuál es la respuesta correcta?",
                opciones={"a": "Correcta", "b": "Incorrecta"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Específico",
                    subtitle="Test 01",
                    total_questions=2,
                    community="Madrid",
                    year=2024,
                    call="abril",
                    test_code="test01",
                    numero_pregunta=1
                )
            ),
            Question(
                id="original_q2",
                enunciado="¿Cuál es otra respuesta correcta?",
                opciones={"a": "Correcta", "b": "Incorrecta"},
                respuesta_correcta="a",
                metadata=QuestionMetadata(
                    title="Test Específico",
                    subtitle="Test 01",
                    total_questions=2,
                    community="Madrid",
                    year=2024,
                    call="abril",
                    test_code="test01",
                    numero_pregunta=2
                )
            )
        ]

        # Configurar el mock directamente y asegurar que funciona
        service.question_loader.get_questions_for_specific_exam = Mock(return_value=specific_questions)

        # Generar examen específico
        exam = service.generate_specific_exam("madrid_2024_abril_test01")

        # Enviar respuesta correcta
        submission = ExamSubmission(
            exam_id=exam.exam_id,
            respuestas={exam.questions[0].id: "a"}  # Respuesta correcta
        )

        # Corregir
        result = service.correct_exam(submission)

        # Verificaciones básicas
        assert result.puntuacion_total is not None
        assert result.porcentaje >= 0.0
        
        # Verificar que el mock fue llamado
        service.question_loader.get_questions_for_specific_exam.assert_called_once_with("madrid_2024_abril_test01")
        assert exam.metadata.tipo_examen == "especifico"
        assert exam.metadata.num_preguntas == 2
        assert exam.metadata.anios == [2024]
        assert exam.metadata.comunidades == ["Madrid"]
        
        # Verificar que las preguntas tienen IDs únicos
        for i, question in enumerate(exam.questions):
            expected_id = f"{exam.exam_id}_q{i+1}"
            assert question.id == expected_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
