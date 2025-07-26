"""
Aplicación principal de FastAPI

Este es el punto de entrada de toda la aplicación.
Aquí se configura:
1. La aplicación FastAPI
2. Las rutas (endpoints)
3. El middleware para servir archivos estáticos
4. La carga inicial de preguntas
"""


import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from app.routers import exams
from app.services.question_loader import question_loader
from config.settings import settings


# Añadir el directorio padre al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================================
# CONFIGURACIÓN DE LIFESPAN
# ================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador de eventos de ciclo de vida de la aplicación.

    Se ejecuta al inicio y al final de la aplicación.
    """
    # STARTUP - Se ejecuta cuando la aplicación arranca
    print("🚀 Iniciando aplicación PER Tests...")
    print(f"📂 Directorio de trabajo: {os.getcwd()}")
    print(f"📁 Buscando archivos en: {question_loader.data_directory}")

    # Verificar si el directorio existe
    if question_loader.data_directory.exists():
        print("✅ Directorio encontrado")
        yaml_files = list(question_loader.data_directory.glob("**/*.yaml"))
        archivos = [f.name for f in yaml_files]
        print(f"📄 Archivos YAML encontrados: {archivos}")
    else:
        print(f"❌ Directorio no encontrado: {question_loader.data_directory}")

    # Cargar todas las preguntas
    question_loader.load_all_questions()

    print(f"📊 Total preguntas cargadas: {len(question_loader.all_questions)}")
    categorias = list(question_loader.questions_cache.keys())
    print(f"📂 Categorías cargadas: {categorias}")

    print("✅ Aplicación lista!")

    yield  # Aquí la aplicación está funcionando

    # SHUTDOWN - Se ejecuta cuando la aplicación se cierra
    print("👋 Cerrando aplicación...")

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================


def create_app() -> FastAPI:
    """
    Crea una nueva instancia de la aplicación FastAPI con todas las rutas y
    configuración.
    Útil para tests que requieren aislamiento.
    """
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.include_router(exams.router)
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.get_static_path())),
        name="static",
    )

    @app.get("/")
    async def root():
        return RedirectResponse(url="/static/index.html")

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "message": "PER Tests API está funcionando correctamente",
            "preguntas_cargadas": len(question_loader.all_questions),
        }

    return app


# Instancia global para producción/servidor
app = create_app()


# ================================
# PUNTO DE ENTRADA
# ================================


def main():
    """
    Función principal para ejecutar la aplicación.

    Esta función se puede llamar desde el script instalado 'per-tests'
    o ejecutando directamente 'python app/main.py'.

    Configuración basada en config/settings.py
    """
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    """
    Esto se ejecuta solo si corremos el archivo directamente.

    Para desarrollo local:
    python app/main.py

    Para producción se usa:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    main()
