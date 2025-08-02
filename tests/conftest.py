

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

from starlette.testclient import TestClient  # Importación directa para evitar conflictos de versiones
from httpx import AsyncClient

from app.main import app
from config.settings import settings

@pytest.fixture
def client() -> TestClient:
    """
    Cliente de test síncrono para FastAPI.
    Usar starlette.testclient.TestClient directamente para evitar conflictos con httpx >=0.27.0.
    """
    return TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Crear un event loop para toda la sesión de tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()




@pytest.fixture
async def async_client():
    """Cliente de test asíncrono para FastAPI compatible con httpx >=0.28.0 y starlette >=0.36.3."""
    from asgi_lifespan import LifespanManager
    from httpx import AsyncClient, ASGITransport
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Directorio temporal para tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_exam_data() -> Dict[str, Any]:
    """
    Datos de ejemplo para un examen completo.
    Los valores se calculan dinámicamente para mantener consistencia.
    """
    # Definir las categorías y preguntas primero
    categorias_data = {
        1: {
            "nombre": "Nomenclatura náutica",
            "preguntas": [
                {
                    "numero": 1,
                    "pregunta": "¿Cuál es la parte delantera de una embarcación?",
                    "opciones": ["Popa", "Proa", "Babor", "Estribor"],
                    "respuesta": "b"
                }
            ]
        },
        6: {
            "nombre": "Reglamento (RIPA)",
            "preguntas": [
                {
                    "numero": 2,
                    "pregunta": "¿Cuál es la embarcación que debe maniobrar?",
                    "opciones": ["La mayor", "La menor", "La que viene por estribor", "La que viene por babor"],
                    "respuesta": "c"
                }
            ]
        }
    }
    
    # Calcular valores dinámicamente basándose en los datos reales
    total_questions = sum(len(cat["preguntas"]) for cat in categorias_data.values())
    num_categories = len(categorias_data)
    
    return {
        "exam_info": {
            "title": "Examen Test Madrid 2025",
            "subtitle": "Test 01",
            "community": "Madrid",
            "year": 2025,
            "call": "abril",
            "total_questions": total_questions,  # Calculado dinámicamente: 2
            "expected_questions": total_questions,  # Calculado dinámicamente: 2
            "categories": num_categories,  # Calculado dinámicamente: 2
            "questions_with_answers": total_questions  # Calculado dinámicamente: 2
        },
        "categorias": categorias_data
    }


@pytest.fixture
def mock_settings():
    """Mock de configuración para tests."""
    with patch('config.settings.settings') as mock:
        # Configurar valores de test
        mock.get_data_path.return_value = Path("/tmp/test_data")
        mock.get_exams_path.return_value = Path("/tmp/test_data/exams")
        mock.get_static_path.return_value = Path("/tmp/test_data/static")
        mock.simulacro_distribution = {
            1: 4, 2: 2, 3: 4, 4: 2, 5: 5, 6: 10,
            7: 2, 8: 3, 9: 4, 10: 5, 11: 4
        }
        mock.default_num_questions = 45
        mock.exam_ttl_hours = 2
        yield mock


@pytest.fixture
def mock_question_loader():
    """Mock del question loader para tests."""
    from app.services.question_loader import QuestionLoader
    
    with patch('app.services.question_loader.question_loader') as mock:
        # Configurar datos de test
        mock.all_questions = []
        mock.questions_by_community = {}
        mock.questions_by_category = {}
        mock.get_stats.return_value = {
            "total_questions": 0,
            "communities": [],
            "categories": {},
            "files_loaded": 0
        }
        yield mock


@pytest.fixture
def mock_exam_service():
    """Mock del exam service para tests."""
    from app.services.exam_service import ExamService
    
    with patch('app.services.exam_service.exam_service') as mock:
        mock.get_service_stats.return_value = {
            "active_exams": 0,
            "total_generated": 0,
            "total_corrected": 0
        }
        yield mock


@pytest.fixture(scope="function")
def isolated_app():
    """
    Aplicación aislada para tests que necesitan estado limpio.
    """
    # Crear una nueva instancia de la app para este test
    from app.main import create_app
    return create_app()


# Fixtures para archivos de test
@pytest.fixture
def sample_yaml_exam(temp_dir: Path) -> Path:
    """Crear un archivo YAML de examen de muestra."""
    # Leer el contenido del archivo de fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    source_file = fixtures_dir / "sample_exam.yaml"
    
    if not source_file.exists():
        raise FileNotFoundError(f"Archivo de fixture no encontrado: {source_file}")
    
    # Copiar el archivo a la carpeta temporal de test
    exam_file = temp_dir / "test_exam.yaml"
    exam_file.write_text(source_file.read_text(encoding='utf-8'))
    return exam_file


@pytest.fixture
def sample_json_answers(temp_dir: Path) -> Path:
    """Crear un archivo JSON de respuestas de muestra."""
    # Leer el contenido del archivo de fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    source_file = fixtures_dir / "sample_answers.json"
    
    if not source_file.exists():
        raise FileNotFoundError(f"Archivo de fixture no encontrado: {source_file}")
    
    # Copiar el archivo a la carpeta temporal de test
    answers_file = temp_dir / "test_answers.json"
    answers_file.write_text(source_file.read_text(encoding='utf-8'))
    return answers_file


@pytest.fixture
def question_loader_with_questions():
    """QuestionLoader con preguntas de ejemplo para tests."""
    from app.services.question_loader import QuestionLoader
    from app.models.schemas import Question, QuestionMetadata
    
    loader = QuestionLoader()
    
    # Crear preguntas de ejemplo
    sample_questions = [
        Question(
            id="test_q1",
            enunciado="¿Cuál es la respuesta correcta?",
            opciones={"a": "Correcta", "b": "Incorrecta", "c": "También incorrecta"},
            respuesta_correcta="a",
            metadata=QuestionMetadata(
                title="Test Examen",
                subtitle="Test 01",
                total_questions=3,
                community="Madrid",
                year=2024,
                call="abril",
                test_code="Test01",
                numero_pregunta=1,
                categoria="1"
            )
        ),
        Question(
            id="test_q2",
            enunciado="¿Cuál es la segunda pregunta?",
            opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C"},
            respuesta_correcta="b",
            metadata=QuestionMetadata(
                title="Test Examen",
                subtitle="Test 01",
                total_questions=3,
                community="Madrid",
                year=2024,
                call="abril",
                test_code="Test01",
                numero_pregunta=2,
                categoria="2"
            )
        ),
        Question(
            id="test_q3",
            enunciado="¿Cuál es la tercera pregunta?",
            opciones={"a": "Primera", "b": "Segunda", "c": "Tercera"},
            respuesta_correcta="c",
            metadata=QuestionMetadata(
                title="Test Examen",
                subtitle="Test 02",
                total_questions=3,
                community="Valencia",
                year=2023,
                call="junio",
                test_code="Test02",
                numero_pregunta=1,
                categoria="1"
            )
        )
    ]
    
    # Asignar las preguntas al loader
    loader.all_questions = sample_questions
    
    return loader


@pytest.fixture
def exam_service_with_questions():
    """ExamService con QuestionLoader que tiene preguntas de ejemplo."""
    from app.services.exam_service import ExamService
    from unittest.mock import Mock
    
    service = ExamService()
    
    # Crear mock del question_loader
    mock_loader = Mock()
    
    # Configurar respuestas del mock
    mock_loader.get_questions_by_criteria.return_value = [
        Mock(
            id=f"q{i}",
            enunciado=f"Pregunta {i}",
            opciones={"a": "A", "b": "B", "c": "C"},
            respuesta_correcta="a",
            metadata=Mock(categoria=1, anio=2024)
        ) for i in range(1, 6)
    ]
    
    # Configurar método get_questions_for_specific_exam por defecto
    mock_loader.get_questions_for_specific_exam.return_value = []
    
    # Configurar otros métodos que podrían ser necesarios
    mock_loader.get_exam_metadata.return_value = {
        "comunidades": ["Madrid"],
        "anios": [2024],
        "convocatorias_por_comunidad_anio": {"Madrid": {2024: ["abril", "junio"]}}
    }
    
    # Asignar el mock al servicio
    service.question_loader = mock_loader
    
    return service
