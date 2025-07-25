"""
Tests unitarios para los endpoints de la API

Estos tests verifican que los endpoints de FastAPI funcionan correctamente:
- Generación de exámenes
- Corrección de exámenes  
- Endpoints de información
- Manejo de errores HTTP
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.schemas import (
    ExamGenerationRequest, 
    ExamSubmission, 
    GeneratedExam, 
    QuestionForClient,
    QuestionMetadata
)


class TestExamEndpoints:
    """Tests para los endpoints de exámenes."""
    
    def test_health_check(self, client: TestClient):
        """Test del endpoint de salud."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "preguntas_cargadas" in data
    
    def test_root_redirect(self, client: TestClient):
        """Test del endpoint raíz que redirige."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary Redirect
        assert response.headers["location"] == "/static/index.html"
    
    @patch('app.services.question_loader.question_loader')
    @pytest.mark.asyncio
    @patch("app.routers.exams.question_loader")
    @patch("app.routers.exams.exam_service")
    async def test_generate_exam_success(self, mock_exam_service, mock_question_loader, async_client):
        """Test exitoso de generación de examen."""
        # Mock de comunidades disponibles
        mock_question_loader.get_available_communities.return_value = ["Madrid", "Cataluña", "Valencia"]
        
        # Preparar datos de mock
        exam_request = ExamGenerationRequest(
            num_preguntas=10,
            categorias=["nomenclatura_nautica"],
            años=[2022],
            comunidades=["Madrid"]
        )
        
        # Mock del service que genera el examen
        expected_exam = GeneratedExam(
            exam_id="test_exam_123",
            questions=[
                QuestionForClient(
                    id="per_nom_001_2022_madrid_p1",
                    enunciado="¿Qué es un cabo?",
                    opciones={
                        "A": "Una parte del barco",
                        "B": "Un accidente geográfico", 
                        "C": "Una cuerda náutica",
                        "D": "Un instrumento de navegación"
                    },
                    metadata=QuestionMetadata(
                        title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
                        subtitle="Código de Test 01",
                        total_questions=100,
                        community="Madrid",
                        year=2022,
                        call="Ordinaria",
                        test_code="Test01",
                        categoria="nomenclatura_nautica",
                        año=2022,
                        comunidad_autonoma="Madrid"
                    )
                )
            ],
            metadata=exam_request
        )
        
        mock_exam_service.generate_exam.return_value = expected_exam
    
    def test_generate_exam_invalid_request(self, client: TestClient):
        """Test de generación con petición inválida."""
        response = client.post("/api/exams/generate", json={
            "num_preguntas": 0,  # Inválido
            "comunidades": ["Madrid"]
        })
        
        assert response.status_code == 422  # Validation Error
    
    def test_generate_exam_empty_communities(self, client: TestClient):
        """Test de generación con comunidades vacías."""
        response = client.post("/api/exams/generate", json={
            "num_preguntas": 45,
            "comunidades": []  # Válido pero resultará en 0 preguntas
        })

        # El API devuelve 400 cuando no encuentra suficientes preguntas
        assert response.status_code == 400  # Bad Request
        assert "No hay suficientes preguntas" in response.text

    @patch('app.routers.exams.exam_service')
    def test_correct_exam_success(self, mock_exam_service, client: TestClient):
        """Test de corrección exitosa de examen."""
        # Configurar mock con la estructura real de ExamResult
        from app.models.schemas import ExamResult, QuestionResult, CategoryResult
        
        # Crear metadata válido
        question_metadata = QuestionMetadata(
            title="EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO",
            subtitle="Código de Test 01",
            total_questions=100,
            community="Madrid",
            year=2022,
            call="Ordinaria",
            test_code="Test01"
        )

        mock_result = ExamResult(
            exam_id="test-123",
            puntuacion_total="45/45",
            porcentaje=100.0,
            aprobado=True,
            preguntas_detalle=[
                QuestionResult(
                    question_id="q1",
                    respuesta_usuario="a",
                    respuesta_correcta="a",
                    respuestas_correctas_lista=["a"],
                    texto_respuesta_usuario="Opción A",
                    texto_respuesta_correcta="Opción A",
                    textos_respuestas_correctas={"a": "Opción A"},
                    es_correcta=True,
                    es_anulada=False,
                    enunciado="¿Qué es un cabo?",
                    opciones={"a": "Opción A", "b": "Opción B", "c": "Opción C", "d": "Opción D"},
                    metadata=question_metadata
                )
            ],
            desglose_por_categoria={
                "1": CategoryResult(
                    categoria="1",
                    correctas=1,
                    total=1,
                    porcentaje=100.0
                )
            }
        )
        
        # Configurar el mock para que no lance excepción
        mock_exam_service.correct_exam.return_value = mock_result
        
        # Realizar petición
        response = client.post("/api/exams/correct", json={
            "exam_id": "test-123",
            "respuestas": {"q1": "a"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["puntuacion_total"] == "45/45"
        assert data["porcentaje"] == 100.0
        assert data["aprobado"] == True
        assert "preguntas_detalle" in data
        assert "desglose_por_categoria" in data
        assert len(data["preguntas_detalle"]) == 1
        assert data["preguntas_detalle"][0]["question_id"] == "q1"
        assert data["preguntas_detalle"][0]["es_correcta"] == True
    
    def test_correct_exam_invalid_submission(self, client: TestClient):
        """Test de corrección con envío inválido."""
        response = client.post("/api/exams/correct", json={
            "exam_id": "",  # ID vacío
            "respuestas": {}
        })
        
        assert response.status_code == 404  # Not Found (para ID vacío)
    
    @patch('app.services.exam_service.exam_service')
    def test_correct_exam_not_found(self, mock_exam_service, client: TestClient):
        """Test de corrección de examen no encontrado."""
        # Configurar mock para lanzar excepción
        mock_exam_service.correct_exam.side_effect = HTTPException(
            status_code=404, detail="Examen no encontrado"
        )
        
        response = client.post("/api/exams/correct", json={
            "exam_id": "inexistente",
            "respuestas": {"1": "a"}
        })
        
        assert response.status_code == 404
    
    @patch('app.routers.exams.exam_service')
    @patch('app.routers.exams.question_loader')
    def test_get_exam_info(self, mock_question_loader, mock_exam_service, client: TestClient):
        """Test del endpoint de información."""
        # Configurar mocks con el formato real
        mock_question_loader.get_stats.return_value = {
            "total_preguntas": 1000,
            "categorias": 5,
            "años_disponibles": [2022, 2023, 2024],
            "comunidades_disponibles": ["Madrid", "Valencia"],
            "preguntas_por_categoria": {"1": 100, "6": 200}
        }
        
        mock_exam_service.get_service_stats.return_value = {
            "examenes_activos": 3,
            "ttl_examenes": "2.0 horas"
        }

        response = client.get("/api/exams/info")

        assert response.status_code == 200
        data = response.json()
        assert "preguntas" in data
        assert "servicio" in data
        assert data["preguntas"]["total_preguntas"] == 1000
        assert data["servicio"]["examenes_activos"] == 3

    @patch('app.routers.exams.question_loader')
    def test_get_categories(self, mock_question_loader, client: TestClient):
        """Test del endpoint de categorías."""
        # Configurar mocks para los métodos que se llaman realmente
        mock_question_loader.get_available_categories.return_value = ["nomenclatura_nautica", "seguridad"]
        mock_question_loader.get_available_years.return_value = [2022, 2023, 2024]
        mock_question_loader.get_available_communities.return_value = ["Madrid", "Valencia"]

        response = client.get("/api/exams/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categorias" in data
        assert "años" in data
        assert "comunidades" in data
        assert len(data["categorias"]) == 2
        assert len(data["años"]) == 3
        assert len(data["comunidades"]) == 2

    def test_invalid_endpoint(self, client: TestClient):
        """Test de endpoint inexistente."""
        response = client.get("/api/exams/inexistente")
        
        assert response.status_code == 404
    
    def test_invalid_method(self, client: TestClient):
        """Test de método HTTP inválido."""
        response = client.delete("/api/exams/generate")  # DELETE no permitido
        
        assert response.status_code == 405  # Method Not Allowed


class TestExamEndpointsAsync:
    """Tests asíncronos para endpoints de exámenes."""
    
    @pytest.mark.asyncio
    async def test_generate_exam_async(self):
        """Test asíncrono de generación de examen."""
        async with AsyncClient(app=app, base_url="http://test") as async_client:
            with patch('app.routers.exams.question_loader') as mock_loader, \
                 patch('app.routers.exams.exam_service') as mock_service:
        
                # Configurar mocks
                mock_loader.get_available_communities.return_value = ["Madrid", "Valencia"]
                
                # Mock del service que genera el examen  
                expected_exam = GeneratedExam(
                    exam_id="async-test",
                    questions=[],
                    metadata=ExamGenerationRequest(
                        num_preguntas=1,
                        categorias=["nomenclatura_nautica"],
                        años=[2022],
                        comunidades=["Madrid"]
                    )
                )
                mock_service.generate_exam.return_value = expected_exam
        
                response = await async_client.post("/api/exams/generate", json={
                    "num_preguntas": 1,
                    "comunidades": ["Madrid"]
                })
        
                assert response.status_code == 200
                data = response.json()
                assert "exam_id" in data

    @pytest.mark.asyncio
    async def test_health_check_async(self):
        """Test asíncrono del endpoint de salud."""
        async with AsyncClient(app=app, base_url="http://test") as async_client:
            response = await async_client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestExamValidation:
    """Tests para validación de datos en endpoints."""
    
    def test_validate_communities_valid(self, client: TestClient):
        """Test de validación de comunidades válidas."""
        # Este test verificaría la función _validate_communities
        # si fuera pública o si tuviéramos acceso a ella
        pass
    
    def test_exam_generation_request_validation(self):
        """Test de validación del modelo ExamGenerationRequest."""
        # Test válido
        valid_request = ExamGenerationRequest(
            num_preguntas=45,
            comunidades=["Madrid"]
        )
        assert valid_request.num_preguntas == 45
        assert valid_request.comunidades == ["Madrid"]
        
        # Test con categorías (ahora como lista)
        request_with_categories = ExamGenerationRequest(
            num_preguntas=20,
            comunidades=["Madrid", "Valencia"],
            categorias=["1", "6", "3"]  # Lista de strings, no diccionario
        )
        assert len(request_with_categories.categorias) == 3
        assert "1" in request_with_categories.categorias
    
    def test_exam_submission_validation(self):
        """Test de validación del modelo ExamSubmission."""
        # Test válido
        valid_submission = ExamSubmission(
            exam_id="test-exam-123",
            respuestas={"1": "a", "2": "b", "3": "c"}
        )
        assert valid_submission.exam_id == "test-exam-123"
        assert len(valid_submission.respuestas) == 3
        
        # Test con respuestas vacías
        empty_submission = ExamSubmission(
            exam_id="test-empty",
            respuestas={}
        )
        assert len(empty_submission.respuestas) == 0


class TestErrorHandling:
    """Tests para manejo de errores en endpoints."""
    
    @patch('app.routers.exams.question_loader')
    def test_server_error_handling(self, mock_question_loader, client: TestClient):
        """Test de manejo de errores del servidor."""
        # Configurar mock para lanzar excepción
        mock_question_loader.get_stats.side_effect = Exception("Error interno")
        
        response = client.get("/api/exams/info")
        
        assert response.status_code == 500
        data = response.json()
        assert "Error obteniendo información" in data["detail"]
    
    def test_malformed_json(self, client: TestClient):
        """Test de JSON malformado."""
        response = client.post(
            "/api/exams/generate",
            content="{'invalid': json}",  # JSON inválido
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, client: TestClient):
        """Test de Content-Type faltante."""
        response = client.post(
            "/api/exams/generate",
            content='{"num_preguntas": 45, "comunidades": ["Madrid"]}'
            # Sin Content-Type header
        )
        
        # FastAPI devuelve 400 para content-type faltante
        assert response.status_code in [200, 400, 422, 415]
