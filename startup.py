#!/usr/bin/env python3
"""
Archivo de inicio para Azure Web App

Este archivo es ejecutado automáticamente por Azure Web App cuando inicia el contenedor.
Usa la configuración optimizada para Azure del Makefile.
"""

import os
import subprocess
import sys

def main():
    """
    Inicia la aplicación usando la configuración optimizada para Azure.
    
    Usa uvicorn con:
    - 1 worker (optimizado para Azure)
    - Host 0.0.0.0 (para escuchar en todas las interfaces)
    - Puerto desde variable de entorno o 8000 por defecto
    - Sin reload (producción)
    - Log level info
    """
    
    # Azure Web App usa la variable PORT o por defecto 8000
    port = os.environ.get('PORT', '8000')
    
    # Configurar variables de entorno para producción en Azure
    os.environ.setdefault('PER_RELOAD', 'false')
    os.environ.setdefault('PER_LOG_LEVEL', 'info')
    
    # Comando optimizado para Azure (como en make run-azure)
    cmd = [
        sys.executable, '-m', 'uvicorn', 
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', '1'
    ]
    
    print(f"🚀 Iniciando aplicación en Azure Web App...")
    print(f"📡 Host: 0.0.0.0, Puerto: {port}")
    print(f"⚙️  Comando: {' '.join(cmd)}")
    
    # Ejecutar el comando
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Aplicación detenida por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()
