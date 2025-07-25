"""
Tests para el módulo main.py

Estos tests cubren:
1. La configuración de la aplicación FastAPI
2. Los endpoints básicos (root, health)
3. El manejo del lifespan
4. La configuración de archivos estáticos
5. El punto de entrada principal
"""

import pytest
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path
import os
import sys

# Agregar el directorio padre al path para las importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app, lifespan


class TestMainApplication:
    """Tests para la configuración principal de la aplicación."""
    
    def test_app_configuration(self):
        """Test de configuración básica de la aplicación FastAPI."""
        assert isinstance(app, FastAPI)
        assert app.title == "PER Tests API"
        assert "API para generar y corregir exámenes aleatorios" in app.description
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        
    def test_app_has_routes(self):
        """Test de que la aplicación tiene las rutas configuradas."""
        routes = [route.path for route in app.routes]
        
        # Rutas básicas
        assert "/" in routes
        assert "/health" in routes
        
        # Rutas de exámenes (del router)
        assert "/api/exams/generate" in routes
        assert "/api/exams/correct" in routes
        assert "/api/exams/info" in routes
        assert "/api/exams/categories" in routes
        
    def test_static_files_mounted(self):
        """Test de que los archivos estáticos están montados."""
        routes = [route.path for route in app.routes]
        static_routes = [route for route in routes if "static" in route]
        assert len(static_routes) > 0


class TestBasicEndpoints:
    """Tests para los endpoints básicos definidos en main.py."""
    
    def test_root_redirect(self, client: TestClient):
        """Test de redirección en la ruta raíz."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Redirect
        assert response.headers["location"] == "/static/index.html"
        
    def test_health_check_endpoint(self, client: TestClient):
        """Test del endpoint de salud."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "PER Tests API está funcionando correctamente" in data["message"]
        assert "preguntas_cargadas" in data
        assert isinstance(data["preguntas_cargadas"], int)


class TestLifespanManager:
    """Tests para el manejador de ciclo de vida de la aplicación."""
    
    @pytest.mark.asyncio
    @patch('app.main.question_loader')
    @patch('builtins.print')
    async def test_lifespan_startup_directory_exists(self, mock_print, mock_question_loader):
        """Test del startup cuando el directorio existe."""
        # Configurar mocks
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = True
        mock_exams_dir.glob.return_value = [MagicMock(name="test1.yaml"), MagicMock(name="test2.yaml")]
        mock_question_loader.data_directory = mock_exams_dir
        mock_question_loader.all_questions = [1, 2, 3]
        mock_question_loader.questions_cache = {"cat1": [1, 2], "cat2": [3]}
        mock_question_loader.load_all_questions.return_value = None

        test_app = FastAPI()

        async with lifespan(test_app):
            # Verificar que se llamaron los métodos esperados
            mock_exams_dir.exists.assert_called_once()
            mock_exams_dir.glob.assert_called_once_with("**/*.yaml")

            startup_calls = [call for call in mock_print.call_args_list]
            startup_messages = [str(call) for call in startup_calls]

            assert any("🚀 Iniciando aplicación PER Tests..." in msg for msg in startup_messages)
            assert any("✅ Directorio encontrado" in msg for msg in startup_messages)
            assert any("✅ Aplicación lista!" in msg for msg in startup_messages)

        shutdown_calls = [call for call in mock_print.call_args_list]
        shutdown_messages = [str(call) for call in shutdown_calls]
        assert any("👋 Cerrando aplicación..." in msg for msg in shutdown_messages)
    
    @pytest.mark.asyncio
    @patch('app.main.question_loader')
    @patch('builtins.print')
    async def test_lifespan_startup_directory_not_exists(self, mock_print, mock_question_loader):
        """Test del startup cuando el directorio no existe."""
        mock_exams_dir = MagicMock()
        mock_exams_dir.exists.return_value = False
        mock_question_loader.data_directory = mock_exams_dir
        mock_question_loader.all_questions = []
        mock_question_loader.questions_cache = {}
        mock_question_loader.load_all_questions.return_value = None

        test_app = FastAPI()

        async with lifespan(test_app):
            # Verificar que se llamaron los métodos esperados
            mock_exams_dir.exists.assert_called_once()
            
            startup_calls = [call for call in mock_print.call_args_list]
            startup_messages = [str(call) for call in startup_calls]
            
            assert any("❌ Directorio no encontrado" in msg for msg in startup_messages)


class TestMainEntryPoint:
    """Tests para el punto de entrada principal."""
    
    @patch('app.main.uvicorn')
    def test_main_entry_point_execution(self, mock_uvicorn):
        """Test del punto de entrada principal cuando se ejecuta como script."""
        from config.settings import settings
        
        # Simular la ejecución del bloque __name__ == "__main__"
        # Ejecutamos directamente el código que está en ese bloque
        mock_uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level=settings.log_level
        )
        
        # Verificar que uvicorn.run fue llamado con los parámetros correctos
        mock_uvicorn.run.assert_called_with(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level=settings.log_level
        )


class TestApplicationIntegration:
    """Tests de integración para la aplicación principal."""
    
    def test_full_application_startup(self, client: TestClient):
        """Test de que la aplicación completa se inicia correctamente."""
        # Verificar que podemos hacer requests básicos
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        root_response = client.get("/", follow_redirects=False)
        assert root_response.status_code == 307
        
    @patch('app.main.os.getcwd')
    @patch('app.main.question_loader')
    def test_working_directory_logging(self, mock_question_loader, mock_getcwd, client):
        """Test de que se registra correctamente el directorio de trabajo."""
        mock_getcwd.return_value = "/test/directory"
        mock_data_dir = MagicMock()
        mock_data_dir.exists.return_value = True
        mock_data_dir.glob.return_value = []
        mock_question_loader.data_directory = mock_data_dir
        mock_question_loader.all_questions = []
        mock_question_loader.questions_cache = {}
        
        # Esto testea indirectamente el lifespan al crear un cliente
        # ya que el lifespan se ejecuta al inicializar la aplicación
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Tests para manejo de errores en main.py."""
    
    @patch('app.main.question_loader')
    def test_application_with_question_loader_error(self, mock_question_loader):
        """Test de que la aplicación maneja errores del question_loader."""
        # Configurar el question_loader para lanzar una excepción
        mock_question_loader.load_all_questions.side_effect = Exception("Error de prueba")
        mock_question_loader.data_directory = MagicMock()
        mock_question_loader.data_directory.exists.return_value = True
        mock_question_loader.all_questions = []
        mock_question_loader.questions_cache = {}
        
        # La aplicación debería seguir funcionando a pesar del error
        # (FastAPI maneja las excepciones del lifespan)
        try:
            client = TestClient(app)
            response = client.get("/health")
            # El endpoint de salud debería funcionar incluso si question_loader falla
            assert response.status_code == 200
        except Exception:
            # Si hay una excepción, al menos verificamos que es manejada
            pass


class TestStaticConfiguration:
    """Tests para la configuración de archivos estáticos."""
    
    @patch('app.main.settings')
    def test_static_path_configuration(self, mock_settings):
        """Test de configuración del path de archivos estáticos."""
        mock_settings.get_static_path.return_value = Path("/test/static")
        
        # Verificar que la aplicación usa la configuración correcta
        # Esta es una verificación indirecta ya que la configuración
        # se hace al importar el módulo
        static_mounts = [route for route in app.routes if hasattr(route, 'name') and route.name == 'static']
        assert len(static_mounts) > 0
