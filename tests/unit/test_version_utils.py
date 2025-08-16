"""
Tests para las utilidades de versión.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from app.utils.version import get_app_version


class TestGetAppVersion:
    """Tests para la función get_app_version."""

    def setup_method(self):
        """Limpiar cache antes de cada test."""
        # Limpiar el cache de la función
        get_app_version.cache_clear()

    def test_get_app_version_success(self):
        """Test de extracción exitosa de versión."""
        # Contenido simulado de pyproject.toml
        mock_toml_content = b"""
[project]
name = "per-tests"
version = "1.2.3"
description = "Test app"
"""
        
        with patch("app.utils.version.Path") as mock_path:
            with patch("builtins.open", mock_open(read_data=mock_toml_content)):
                # Simular que el archivo existe
                mock_path.return_value.parent.parent.parent.__truediv__.return_value = Path("pyproject.toml")
                
                version = get_app_version()
                assert version == "1.2.3"

    def test_get_app_version_file_not_found(self):
        """Test cuando el archivo pyproject.toml no existe."""
        with patch("app.utils.version.Path"):
            with patch("builtins.open", side_effect=FileNotFoundError):
                version = get_app_version()
                assert version == "desconocida"

    def test_get_app_version_invalid_toml(self):
        """Test cuando el archivo TOML es inválido."""
        # Contenido TOML inválido
        mock_invalid_toml = b"invalid toml content ["
        
        with patch("app.utils.version.Path"):
            with patch("builtins.open", mock_open(read_data=mock_invalid_toml)):
                version = get_app_version()
                assert version == "desconocida"

    def test_get_app_version_missing_version_key(self):
        """Test cuando el TOML no tiene la clave version."""
        # Contenido TOML válido pero sin version
        mock_toml_content = b"""
[project]
name = "per-tests"
description = "Test app"
"""
        
        with patch("app.utils.version.Path"):
            with patch("builtins.open", mock_open(read_data=mock_toml_content)):
                version = get_app_version()
                assert version == "desconocida"

    def test_get_app_version_caching(self):
        """Test que la función usa cache correctamente."""
        mock_toml_content = b"""
[project]
version = "1.0.0"
"""
        
        with patch("app.utils.version.Path"):
            with patch("builtins.open", mock_open(read_data=mock_toml_content)) as mock_file:
                # Llamar múltiples veces
                version1 = get_app_version()
                version2 = get_app_version()
                version3 = get_app_version()
                
                # Todas deberían devolver el mismo valor
                assert version1 == version2 == version3 == "1.0.0"
                
                # El archivo solo debería haberse abierto una vez debido al cache
                assert mock_file.call_count == 1

    def test_get_app_version_real_file(self):
        """Test con un archivo TOML real temporal."""
        # Crear archivo temporal con contenido TOML válido
        toml_content = """
[project]
name = "test-project"
version = "2.1.0"
description = "Test project"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            temp_path = f.name
        
        try:
            with patch("app.utils.version.Path") as mock_path:
                mock_path.return_value.parent.parent.parent.__truediv__.return_value = Path(temp_path)
                
                version = get_app_version()
                assert version == "2.1.0"
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_path)
