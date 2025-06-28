"""
Aplicación principal de FastAPI

Este es el punto de entrada de toda la aplicación.
Aquí se configura:
1. La aplicación FastAPI
2. Las rutas (endpoints)
3. El middleware para servir archivos estáticos
4. La carga inicial de preguntas
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn

from app.routers import exams
from app.services.question_loader import question_loader

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================

app = FastAPI(
    title="PER Tests API",
    description="API para generar y corregir exámenes aleatorios de PER España",
    version="1.0.0",
    docs_url="/docs",  # Documentación automática en /docs
    redoc_url="/redoc"  # Documentación alternativa en /redoc
)

# ================================
# CONFIGURACIÓN DE RUTAS
# ================================

# Incluir las rutas de exámenes
app.include_router(exams.router)

# Servir archivos estáticos (HTML, CSS, JS)
# Esto permite que el frontend esté en la carpeta 'static'
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================================
# EVENTOS DE LA APLICACIÓN
# ================================

@app.on_event("startup")
async def startup_event():
    """
    Se ejecuta cuando la aplicación arranca.
    
    Aquí cargamos todas las preguntas desde los archivos YAML
    para tenerlas listas en memoria.
    """
    print("🚀 Iniciando aplicación PER Tests...")
    
    # Cargar todas las preguntas
    question_loader.load_all_questions()
    
    print("✅ Aplicación lista!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Se ejecuta cuando la aplicación se cierra.
    
    Aquí podríamos hacer limpieza si fuera necesario.
    """
    print("👋 Cerrando aplicación...")


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
        host="0.0.0.0",
        port=8000,
        reload=True,  # Recarga automática cuando cambian archivos
        log_level="info"
    )
