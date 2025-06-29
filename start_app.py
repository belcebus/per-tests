#!/usr/bin/env python3
"""
Script para arrancar la aplicación FastAPI con uvicorn
"""

import uvicorn
import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("🚀 Iniciando servidor uvicorn...")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            reload_dirs=["app"]
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
