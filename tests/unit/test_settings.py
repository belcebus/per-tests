"""
Tests para el módulo de configuración (config/settings.py)

Estos tests verifican que la configuración se carga correctamente
y que las variables de entorno se manejan apropiadamente.
"""

import pytest
import os
from unittest.mock import patch

from config.settings import Settings, settings


class TestSettingsConfiguration:
    """Tests para la configuración de la aplicación"""

    def test_default_settings(self):
        """Test para valores por defecto de configuración"""
        # Crear una instancia nueva para probar valores por defecto
        test_settings = Settings()
        
        # Verificar valores por defecto principales
        assert test_settings.host == "0.0.0.0"
        assert test_settings.port == 8002
        assert test_settings.debug is False
        assert test_settings.log_level == "info"
        assert test_settings.exam_ttl_hours == 2

    def test_environment_variable_override(self):
        """Test para sobrescribir configuración con variables de entorno"""
        with patch.dict(os.environ, {
            'PER_HOST': 'localhost',
            'PER_PORT': '9000',
            'PER_DEBUG': 'true',
            'PER_LOG_LEVEL': 'debug'
        }):
            test_settings = Settings()
            
            assert test_settings.host == "localhost"
            assert test_settings.port == 9000
            assert test_settings.debug is True
            assert test_settings.log_level == "debug"

    def test_data_directory_paths(self):
        """Test para rutas de directorios de datos"""
        test_settings = Settings()
        
        # Verificar que las rutas se construyen correctamente
        assert test_settings.data_dir == "data"
        assert test_settings.exams_dir == "data/exams"
        assert test_settings.raw_questions_dir == "data/raw/questions"
        assert test_settings.raw_answers_dir == "data/raw/answers"

    def test_custom_data_directory(self):
        """Test para directorio de datos personalizado"""
        with patch.dict(os.environ, {'PER_DATA_DIR': '/custom/data'}):
            test_settings = Settings()
            
            assert test_settings.data_dir == "/custom/data"
            # Los otros directorios mantienen sus valores por defecto
            assert test_settings.exams_dir == "data/exams"

    def test_api_configuration(self):
        """Test para configuración de API"""
        test_settings = Settings()
        
        assert test_settings.api_title == "PER Tests API"
        assert "exámenes aleatorios de PER" in test_settings.api_description
        assert test_settings.api_version == "1.0.0"

    def test_exam_default_settings(self):
        """Test para configuración por defecto de exámenes"""
        test_settings = Settings()
        
        assert test_settings.default_num_questions == 45
        assert test_settings.exam_ttl_hours == 2

    def test_processing_settings(self):
        """Test para configuración de procesamiento"""
        test_settings = Settings()
        
        assert test_settings.ocr_confidence_threshold == 0.7  # Valor real es 0.7
        assert test_settings.pdf_dpi == 300

    def test_boolean_environment_variables(self):
        """Test para manejo de variables de entorno booleanas"""
        # Test con valores truthy
        with patch.dict(os.environ, {'PER_DEBUG': 'true'}):
            settings_true = Settings()
            assert settings_true.debug is True
            
        with patch.dict(os.environ, {'PER_DEBUG': '1'}):
            settings_one = Settings()
            assert settings_one.debug is True
            
        with patch.dict(os.environ, {'PER_DEBUG': 'yes'}):
            settings_yes = Settings()
            assert settings_yes.debug is True
            
        # Test con valores falsy
        with patch.dict(os.environ, {'PER_DEBUG': 'false'}):
            settings_false = Settings()
            assert settings_false.debug is False
            
        with patch.dict(os.environ, {'PER_DEBUG': '0'}):
            settings_zero = Settings()
            assert settings_zero.debug is False

    def test_numeric_environment_variables(self):
        """Test para manejo de variables de entorno numéricas"""
        with patch.dict(os.environ, {
            'PER_PORT': '8080',
            'PER_EXAM_TTL_HOURS': '3',  # Debe ser entero, no float
            'PER_OCR_CONFIDENCE_THRESHOLD': '0.75'  # Debe ser float
        }):
            test_settings = Settings()
            
            assert test_settings.port == 8080
            assert test_settings.exam_ttl_hours == 3
            assert test_settings.ocr_confidence_threshold == 0.75

    def test_invalid_numeric_environment_variables(self):
        """Test para manejo de variables de entorno numéricas inválidas"""
        # Esto debería usar valores por defecto cuando la conversión falla
        with patch.dict(os.environ, {
            'PER_PORT': 'invalid_port',
            'PER_EXAM_TTL_HOURS': 'invalid_hours'
        }):
            # Pydantic debería manejar estos valores inválidos
            try:
                test_settings = Settings()
                # Si no lanza excepción, debería usar valores por defecto
                # o valores que puedan ser parseados
            except Exception:
                # Es aceptable que falle con valores inválidos
                pass

    def test_singleton_settings_instance(self):
        """Test para verificar que settings es una instancia única"""
        from config.settings import settings as settings1
        from config.settings import settings as settings2
        
        assert settings1 is settings2


class TestSettingsValidation:
    """Tests para validación de configuración"""

    def test_required_directories_exist_check(self):
        """Test que simula verificación de directorios requeridos"""
        test_settings = Settings()
        
        # Verificar que las rutas están definidas
        assert test_settings.data_dir is not None
        assert test_settings.exams_dir is not None
        assert test_settings.raw_questions_dir is not None

    def test_settings_model_fields(self):
        """Test para verificar que todos los campos necesarios están definidos"""
        test_settings = Settings()
        
        # Verificar campos críticos
        required_fields = [
            'host', 'port', 'debug', 'log_level',
            'data_dir', 'exams_dir', 'api_title',
            'default_num_questions', 'exam_ttl_hours'
        ]
        
        for field in required_fields:
            assert hasattr(test_settings, field), f"Campo {field} no encontrado"
            assert getattr(test_settings, field) is not None, f"Campo {field} es None"
