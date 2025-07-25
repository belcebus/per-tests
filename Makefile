# Makefile para comandos de testing del proyecto PER Tests
# Facilita la ejecución de diferentes tipos de tests con opciones específicas
# 
# NOTA: Este proyecto está diseñado para ser desplegado como servidor API en Azure.
# Los comandos de ejecución están optimizados para desarrollo y despliegue en servidor.

# Variables
PYTHON_CMD = venv/bin/python
PYTEST_CMD = venv/bin/python -m pytest
COV_MODULES = app config tools

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help test test-fast test-cov test-cov-html test-cov-xml test-unit test-integration test-api clean install install-dev install-tools install-full run run-prod run-azure run-debug run-local run-custom

# Comando por defecto
help:
	@echo "$(GREEN)PER Tests - Comandos disponibles:$(NC)"
	@echo ""
	@echo "$(YELLOW)Instalación:$(NC)"
	@echo "  make install         - Instalar dependencias básicas"
	@echo "  make install-dev     - Instalar con dependencias de desarrollo"
	@echo "  make install-tools   - Instalar con herramientas de procesamiento"
	@echo "  make install-full    - Instalar todas las dependencias"
	@echo ""
	@echo "$(YELLOW)Tests rápidos (sin cobertura):$(NC)"
	@echo "  make test-fast      - Ejecutar todos los tests sin cobertura (rápido)"
	@echo "  make test-unit      - Ejecutar solo tests unitarios"
	@echo "  make test-api       - Ejecutar solo tests de API"
	@echo ""
	@echo "$(YELLOW)Tests con cobertura (más lentos):$(NC)"
	@echo "  make test-cov       - Ejecutar tests con cobertura en terminal"
	@echo "  make test-cov-html  - Ejecutar tests y generar reporte HTML"
	@echo "  make test-cov-xml   - Ejecutar tests y generar reporte XML"
	@echo ""
	@echo "$(YELLOW)Ejecutar aplicación:$(NC)"
	@echo "  make run            - Iniciar aplicación (configuración desde config/settings.py)"
	@echo "  make run-prod       - Iniciar aplicación en modo producción (4 workers)"
	@echo "  make run-azure      - Iniciar aplicación optimizada para Azure (1 worker)"
	@echo "  make run-debug      - Iniciar aplicación con debug habilitado"
	@echo "  make run-local      - Iniciar aplicación solo en localhost"
	@echo "  make run-custom     - Iniciar con variables de entorno personalizadas"
	@echo ""
	@echo "$(YELLOW)Limpieza:$(NC)"
	@echo "  make clean          - Limpiar archivos de cobertura y cache"
	@echo ""
	@echo "$(YELLOW)Ejemplos:$(NC)"
	@echo "  make install-dev                  # Instalación para desarrollo"
	@echo "  make test-fast                    # Durante desarrollo"
	@echo "  make test-cov                     # Para verificar cobertura"
	@echo "  make test-cov-html                # Para generar reporte visual"
	@echo ""
	@echo "  make run                          # Aplicación con configuración por defecto"
	@echo "  PER_PORT=9000 make run            # Cambiar puerto"
	@echo "  PER_HOST=localhost make run-local # Localhost en puerto personalizado"

# Comandos de instalación
install:
	@echo "$(GREEN)📦 Instalando paquete en modo editable...$(NC)"
	$(PYTHON_CMD) -m pip install -e .

install-dev:
	@echo "$(GREEN)📦 Instalando paquete con dependencias de desarrollo...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[dev]"

install-tools:
	@echo "$(GREEN)📦 Instalando paquete con herramientas de procesamiento...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[tools]"

install-full:
	@echo "$(GREEN)📦 Instalando paquete con todas las dependencias...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[full]"

# Tests rápidos sin cobertura (ideal para desarrollo)
test-fast:
	@echo "$(GREEN)🚀 Ejecutando tests rápidos (sin cobertura)...$(NC)"
	$(PYTEST_CMD)

# Alias para compatibilidad
test: test-fast

# Tests con cobertura básica
test-cov:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov-report=term-missing --cov-fail-under=0 --cov-config=.coveragerc --ignore=tools

# Tests con cobertura y reporte HTML
test-cov-html:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura y reporte HTML...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=term-missing --cov-report=html:coverage_html
	@echo "$(YELLOW)📄 Reporte HTML generado en: coverage_html/index.html$(NC)"

# Tests con cobertura y reporte XML (para CI/CD)
test-cov-xml:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura y reporte XML...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=term-missing --cov-report=xml:coverage.xml
	@echo "$(YELLOW)📄 Reporte XML generado en: coverage.xml$(NC)"

# Tests con cobertura completa (HTML + XML)
test-cov-full:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura completa...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=term-missing --cov-report=html:coverage_html --cov-report=xml:coverage.xml
	@echo "$(YELLOW)📄 Reportes generados:$(NC)"
	@echo "  - HTML: coverage_html/index.html"
	@echo "  - XML:  coverage.xml"

# Tests por categoría
test-unit:
	@echo "$(GREEN)🧪 Ejecutando tests unitarios...$(NC)"
	$(PYTEST_CMD) -m unit

test-integration:
	@echo "$(GREEN)🔗 Ejecutando tests de integración...$(NC)"
	$(PYTEST_CMD) -m integration

test-api:
	@echo "$(GREEN)🌐 Ejecutando tests de API...$(NC)"
	$(PYTEST_CMD) -m api

# Tests con umbral de cobertura mínimo
test-cov-strict:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura (umbral 95%)...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=term-missing --cov-fail-under=95

# Limpieza de archivos generados
clean:
	@echo "$(GREEN)🧹 Limpiando archivos de cobertura y cache...$(NC)"
	rm -rf coverage_html/
	rm -f coverage.xml
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

# Tests para CI/CD con timeout
test-ci:
	@echo "$(GREEN)🤖 Ejecutando tests para CI/CD...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=xml:coverage.xml --cov-report=term --timeout=300

# Comandos para ejecutar la aplicación
run:
	@echo "$(GREEN)🚀 Iniciando aplicación (configuración por defecto desde settings.py)...$(NC)"
	$(PYTHON_CMD) -c "from app.main import main; main()"

run-prod:
	@echo "$(GREEN)🌟 Iniciando aplicación en modo producción...$(NC)"
	PER_RELOAD=false PER_LOG_LEVEL=warning $(PYTHON_CMD) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

run-azure:
	@echo "$(GREEN)☁️  Iniciando aplicación para Azure (configuración optimizada)...$(NC)"
	PER_RELOAD=false PER_LOG_LEVEL=info $(PYTHON_CMD) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

run-debug:
	@echo "$(GREEN)🐛 Iniciando aplicación con debug habilitado...$(NC)"
	PER_LOG_LEVEL=debug $(PYTHON_CMD) -c "from app.main import main; main()"

run-local:
	@echo "$(GREEN)🏠 Iniciando aplicación solo en localhost...$(NC)"
	PER_HOST=127.0.0.1 $(PYTHON_CMD) -c "from app.main import main; main()"

run-custom:
	@echo "$(GREEN)⚙️  Iniciando aplicación con configuración personalizada...$(NC)"
	@echo "$(YELLOW)Uso: PER_PORT=9000 PER_HOST=localhost make run-custom$(NC)"
	$(PYTHON_CMD) -c "from app.main import main; main()"
