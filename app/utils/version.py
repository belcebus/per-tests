"""
Utilidades para manejo de versión de la aplicación.
"""

import tomllib
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """
    Extrae la versión actual del pyproject.toml.

    Usa cache para evitar leer el archivo múltiples veces.
    El cache se limpia automáticamente al reiniciar la aplicación.

    Returns:
        str: Versión de la aplicación (ej: "1.0.0")

    Note:
        En caso de error leyendo el archivo, devuelve "desconocida"
        para evitar fallos en la aplicación.
    """
    try:
        # Ruta relativa al archivo pyproject.toml desde app/utils/
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        return data["project"]["version"]

    except Exception:
        # Fallback silencioso en caso de error
        # No loggeamos para evitar ruido en producción
        return "desconocida"
