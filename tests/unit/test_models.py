"""
Pruebas unitarias para los modelos Pydantic.
"""
import pytest
from pydantic import ValidationError
from app.models.schemas import QuestionMetadata, Question, ExamGenerationRequest


class TestQuestionMetadata:
    """Pruebas para el modelo QuestionMetadata."""
    
    def test_valid_metadata(self):
        """Test de metadatos válidos."""
        metadata = QuestionMetadata(
            title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
            subtitle="Código de Test 01",
            total_questions=45,
            community="Madrid",
            year=2023,
            call="abril",
            test_code="01"
        )
        
        assert metadata.title == "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"
        assert metadata.subtitle == "Código de Test 01"
        assert metadata.total_questions == 45
        assert metadata.community == "Madrid"
        assert metadata.year == 2023
        assert metadata.call == "abril"
        assert metadata.test_code == "01"
    
    def test_metadata_with_optional_fields(self):
        """Test de metadatos con campos opcionales."""
        metadata = QuestionMetadata(
            title="EXAMEN DE PATRÓN",
            subtitle="Test 01",
            total_questions=45,
            community="Madrid",
            year=2023,
            call="abril",
            test_code="01",
            # Campos opcionales de compatibilidad
            categoria="navegacion",
            convocatoria="abril",
            anio=2023,
            comunidad_autonoma="madrid",
            numero_pregunta=1
        )
        
        assert metadata.categoria == "navegacion"
        assert metadata.convocatoria == "abril"
        assert metadata.anio == 2023
        assert metadata.comunidad_autonoma == "madrid"
        assert metadata.numero_pregunta == 1
    
    def test_required_fields_missing(self):
        """Test que falla cuando faltan campos requeridos."""
        with pytest.raises(ValidationError):
            QuestionMetadata()  # Sin campos requeridos


class TestQuestion:
    """Pruebas para el modelo Question."""
    
    def test_valid_question(self):
        """Test de pregunta válida."""
        metadata = QuestionMetadata(
            title="EXAMEN DE PATRÓN",
            subtitle="Test 01",
            total_questions=45,
            community="Madrid",
            year=2023,
            call="abril",
            test_code="01"
        )
        
        question = Question(
            id="per_nom_001_2023_madrid_p001",
            enunciado="¿Cuál es la capital de España?",
            opciones={"a": "Madrid", "b": "Barcelona", "c": "Valencia", "d": "Sevilla"},
            respuesta_correcta="a",
            metadata=metadata
        )
        
        assert question.id == "per_nom_001_2023_madrid_p001"
        assert question.enunciado == "¿Cuál es la capital de España?"
        assert len(question.opciones) == 4
        assert question.opciones["a"] == "Madrid"
        assert question.respuesta_correcta == "a"
        assert question.metadata.community == "Madrid"
    
    def test_question_with_empty_options(self):
        """Test de pregunta con opciones vacías."""
        metadata = QuestionMetadata(
            title="EXAMEN DE PATRÓN",
            subtitle="Test 01",
            total_questions=45,
            community="Madrid",
            year=2023,
            call="abril",
            test_code="01"
        )
        
        question = Question(
            id="per_nom_001_2023_madrid_p002",
            enunciado="Pregunta sin opciones múltiples",
            opciones={},
            respuesta_correcta="verdadero",
            metadata=metadata
        )
        
        assert question.opciones == {}
        assert question.respuesta_correcta == "verdadero"


class TestExamGenerationRequest:
    """Pruebas para el modelo ExamGenerationRequest."""
    
    def test_default_values(self):
        """Test con valores por defecto."""
        request = ExamGenerationRequest()
        
        assert request.num_preguntas == 45  # Valor por defecto
        assert request.categorias is None
        assert request.anios is None
        assert request.comunidades is None
        assert request.tipo_examen == "per"  # Valor por defecto

    def test_custom_values(self):
        """Test con valores personalizados."""
        request = ExamGenerationRequest(
            num_preguntas=30,
            categorias=["navegacion", "seguridad"],
            anios=[2023, 2024],
            comunidades=["madrid", "barcelona"],
            tipo_examen="per"
        )
        
        assert request.num_preguntas == 30
        assert request.categorias == ["navegacion", "seguridad"]
        assert request.anios == [2023, 2024]
        assert request.comunidades == ["madrid", "barcelona"]
        assert request.tipo_examen == "per"
    
    def test_invalid_num_preguntas_too_low(self):
        """Test con número de preguntas demasiado bajo."""
        with pytest.raises(ValidationError):
            ExamGenerationRequest(num_preguntas=0)  # Debe ser >= 1
    
    def test_invalid_num_preguntas_too_high(self):
        """Test con número de preguntas demasiado alto."""
        with pytest.raises(ValidationError):
            ExamGenerationRequest(num_preguntas=150)  # Debe ser <= 100


class TestQuestionForClient:
    """Pruebas para el modelo QuestionForClient."""
    
    def test_question_for_client_without_answer(self):
        """Test de pregunta para cliente sin respuesta correcta (simulacro)."""
        from app.models.schemas import QuestionForClient, QuestionMetadata
        
        question = QuestionForClient(
            id="test_q1",
            enunciado="¿Cuál es la respuesta correcta?",
            opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
            metadata=QuestionMetadata(
                title="Test Exam",
                subtitle="Test 01",
                total_questions=45,
                community="Madrid",
                year=2024,
                call="abril",
                test_code="test01",
                categoria="1",
                numero_pregunta=1
            )
        )
        
        assert question.id == "test_q1"
        assert question.enunciado == "¿Cuál es la respuesta correcta?"
        assert len(question.opciones) == 4
        assert question.respuesta_correcta is None  # Campo opcional no incluido
    
    def test_question_for_client_with_answer(self):
        """Test de pregunta para cliente con respuesta correcta (examen normal)."""
        from app.models.schemas import QuestionForClient, QuestionMetadata
        
        question = QuestionForClient(
            id="test_q1",
            enunciado="¿Cuál es la respuesta correcta?",
            opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
            respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test Exam",
                subtitle="Test 01", 
                total_questions=45,
                community="Madrid",
                year=2024,
                call="abril",
                test_code="test01",
                categoria="1",
                numero_pregunta=1
            )
        )
        
        assert question.id == "test_q1"
        assert question.enunciado == "¿Cuál es la respuesta correcta?"
        assert len(question.opciones) == 4
        assert question.respuesta_correcta == "a"  # Campo opcional incluido
    
    def test_question_for_client_with_anulada_answer(self):
        """Test de pregunta para cliente con respuesta anulada (examen normal)."""
        from app.models.schemas import QuestionForClient, QuestionMetadata
        
        question = QuestionForClient(
            id="test_q_anulada",
            enunciado="¿Pregunta anulada?",
            opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
            respuesta_correcta="anulada",
            metadata=QuestionMetadata(
                title="Test Exam",
                subtitle="Test 01", 
                total_questions=45,
                community="Madrid",
                year=2024,
                call="abril",
                test_code="test01",
                categoria="1",
                numero_pregunta=1
            )
        )
        
        assert question.id == "test_q_anulada"
        assert question.enunciado == "¿Pregunta anulada?"
        assert len(question.opciones) == 4
        assert question.respuesta_correcta == "anulada"  # Valor especial para preguntas anuladas
