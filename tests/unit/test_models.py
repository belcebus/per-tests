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
            año=2023,
            comunidad_autonoma="madrid",
            numero_pregunta=1
        )
        
        assert metadata.categoria == "navegacion"
        assert metadata.convocatoria == "abril"
        assert metadata.año == 2023
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
        assert request.años is None
        assert request.comunidades is None
        assert request.tipo_examen == "per"  # Valor por defecto
    
    def test_custom_values(self):
        """Test con valores personalizados."""
        request = ExamGenerationRequest(
            num_preguntas=30,
            categorias=["navegacion", "seguridad"],
            años=[2023, 2024],
            comunidades=["madrid", "barcelona"],
            tipo_examen="per"
        )
        
        assert request.num_preguntas == 30
        assert request.categorias == ["navegacion", "seguridad"]
        assert request.años == [2023, 2024]
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
