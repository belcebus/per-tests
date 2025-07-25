"""
Aplicación principal de FastAPI

Este es el punto de entrada de toda la aplicación.
Aquí se configura:
1. La aplicación FastAPI
2. Las rutas (endpoints)
3. El middleware para servir archivos estáticos
4. La carga inicial de preguntas
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
import sys
import os

# Añadir el directorio padre al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routers import exams
from app.services.question_loader import question_loader
from config.settings import settings

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
        print(f"✅ Directorio encontrado")
        yaml_files = list(question_loader.data_directory.glob("**/*.yaml"))
        print(f"📄 Archivos YAML encontrados: {[f.name for f in yaml_files]}")
    else:
        print(f"❌ Directorio no encontrado: {question_loader.data_directory}")
    
    # Cargar todas las preguntas
    question_loader.load_all_questions()
    
    print(f"📊 Total preguntas cargadas: {len(question_loader.all_questions)}")
    print(f"📂 Categorías cargadas: {list(question_loader.questions_cache.keys())}")
    
    print("✅ Aplicación lista!")
    
    yield  # Aquí la aplicación está funcionando
    
    # SHUTDOWN - Se ejecuta cuando la aplicación se cierra
    print("👋 Cerrando aplicación...")

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",  # Documentación automática en /docs
    redoc_url="/redoc",  # Documentación alternativa en /redoc
    lifespan=lifespan  # Usar el nuevo manejador de eventos
)

# ================================
# CONFIGURACIÓN DE RUTAS
# ================================

# Incluir las rutas de exámenes
app.include_router(exams.router)

# Servir archivos estáticos (HTML, CSS, JS)
# Esto permite que el frontend esté en la carpeta 'static'
app.mount("/static", StaticFiles(directory=str(settings.get_static_path())), name="static")

# ================================
# RUTAS BÁSICAS
# ================================

@app.get("/")
async def root():
    """
    Ruta raíz - redirige al cliente web.
    
    Cuando alguien visita http://localhost:8000/
    lo redirigimos automáticamente al frontend.
    """
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health_check():
    """
    Endpoint de salud - para verificar que la API funciona.
    
    Útil para:
    - Monitoreo en producción
    - Verificar que Azure Web App está funcionando
    - Tests automáticos
    """
    return {
        "status": "healthy",
        "message": "PER Tests API está funcionando correctamente",
        "preguntas_cargadas": len(question_loader.all_questions)
    }


# ================================
# PUNTO DE ENTRADA
# ================================

if __name__ == "__main__":
    """
    Esto se ejecuta solo si corremos el archivo directamente.
    
    Para desarrollo local:
    python app/main.py
    
    Para producción se usa:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )
