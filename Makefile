# Análisis de calidad de código (linters y analizadores)
quality: venv
	@echo "$(GREEN)🔎 Análisis de calidad de código (flake8, pylint, black, mypy)...$(NC)"
	venv/bin/flake8 app config
	venv/bin/pylint --disable=all --enable=E,F app config
	venv/bin/black --check app config
	venv/bin/mypy app config
	@echo "$(GREEN)🔍 Verificando consistencia de archivos de exámenes...$(NC)"
	$(PYTHON_CMD) scripts/check_exam_consistency.py
# Instala solo las dependencias de linters y analizadores
install-lint: venv
	@echo "$(GREEN)📦 Instalando paquete con linters y analizadores...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[lint]"

# Instala solo toml-cli para operaciones con archivos TOML
install-toml-cli: venv
	@echo "$(GREEN)📦 Instalando toml-cli...$(NC)"
	@$(PYTHON_CMD) -m pip install toml-cli > /dev/null 2>&1

# Instala toml-cli silenciosamente (para uso interno)
install-toml-cli-quiet: venv
	@$(PYTHON_CMD) -m pip install toml-cli > /dev/null 2>&1

# Extrae la versión del pyproject.toml (asume que toml-cli ya está instalado)
get-version:
	@venv/bin/toml get --toml-path pyproject.toml project.version

# Makefile para comandos de testing del proyecto PER Tests
# Facilita la ejecución de diferentes tipos de tests con opciones específicas
# 
# NOTA: Este proyecto está diseñado para ser desplegado como servidor API en Azure.
# Los comandos de ejecución están optimizados para desarrollo y despliegue en servidor.

# Variables
PYTHON_CMD = venv/bin/python
PYTEST_CMD = venv/bin/python -m pytest
COV_MODULES = app config
TEST_ARGS = --cov=app --cov=config --cov-report=term-missing --cov-report=html:coverage_html --cov-report=xml:coverage.xml --cov-fail-under=95

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help test test-ci clean install install-dev install-full run run-prod run-azure run-debug run-local run-custom security build-deploy


# Comando por defecto
help:
	@echo "$(GREEN)PER Tests - Comandos disponibles:$(NC)"
	@echo ""
	@echo "$(YELLOW)Instalación:$(NC)"
	@echo "  make install         - Instalar dependencias básicas"
	@echo "  make install-dev     - Instalar con dependencias de desarrollo"
	@echo "  make install-full    - Instalar todas las dependencias"
	@echo "  make install-toml-cli - Instalar toml-cli para operaciones TOML"
	@echo ""
	@echo "$(YELLOW)Utilidades:$(NC)"
	@echo "  make get-version     - Extraer versión del pyproject.toml"
	@echo ""
	@echo "$(YELLOW)Tests:$(NC)"
	@echo "  make test             - Ejecutar todos los tests de la forma más estricta (cobertura 95%, HTML+XML)"
	@echo "  make test-ci          - Igual que 'make test' pero con timeout para CI/CD"
	@echo ""
	@echo "$(YELLOW)Calidad de código:$(NC)"
	@echo "  make quality          - Ejecutar linters y analizadores (flake8, pylint, black, mypy)"
	@echo ""
	@echo "$(YELLOW)Análisis de seguridad:$(NC)"
	@echo "  make security         - Ejecutar análisis de seguridad del código (semgrep)"
	@echo ""
	@echo "$(YELLOW)Ejecutar aplicación:$(NC)"
	@echo "  make run              - Iniciar aplicación (configuración por defecto)"
	@echo "  make run-prod         - Iniciar aplicación en modo producción (4 workers)"
	@echo "  make run-azure        - Iniciar aplicación optimizada para Azure (1 worker)"
	@echo "  make run-debug        - Iniciar aplicación con debug habilitado"
	@echo "  make run-local        - Iniciar aplicación solo en localhost"
	@echo "  make run-custom       - Iniciar con variables de entorno personalizadas"
	@echo ""
	@echo "$(YELLOW)Limpieza:$(NC)"
	@echo "  make clean            - Limpiar archivos de cobertura y cache"
	@echo "  make clean-venv       - Eliminar el entorno virtual"
	@echo ""
	@echo "$(YELLOW)Despliegue:$(NC)"
	@echo "  make build-deploy     - Instalar deps, ejecutar tests y preparar despliegue"
	@echo ""
	@echo "$(YELLOW)Ejemplos:$(NC)"
	@echo "  make install-dev                  # Instalación para desarrollo"
	@echo "  make test                         # Ejecutar la suite completa de tests"
	@echo "  make quality                      # Análisis de calidad de código"
	@echo "  make run                          # Aplicación con configuración por defecto"
	@echo "  PER_PORT=9000 make run            # Cambiar puerto"
	@echo "  PER_HOST=localhost make run-local # Localhost en puerto personalizado"


# Crea el entorno virtual si no existe
venv:
	@if [ ! -d "venv" ]; then \
		echo "$(YELLOW)🔧 Creando entorno virtual en venv...$(NC)"; \
		python3 -m venv venv; \
		venv/bin/pip install --upgrade pip; \
	fi

# Comandos de instalación
install: venv
	@echo "$(GREEN)📦 Instalando paquete en modo editable...$(NC)"
	$(PYTHON_CMD) -m pip install -e .

install-dev: venv
	@echo "$(GREEN)📦 Instalando paquete con dependencias de desarrollo...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[dev]"

install-full: venv
	@echo "$(GREEN)📦 Instalando paquete con todas las dependencias...$(NC)"
	$(PYTHON_CMD) -m pip install -e ".[full]"

# Ejecuta toda la suite de tests de la forma más estricta posible: cobertura
# mínima del 95% y reportes en terminal, HTML y XML.
test:
	@echo "$(GREEN)🧪 Ejecutando todos los tests (cobertura estricta 95%)...$(NC)"
	$(PYTEST_CMD) $(TEST_ARGS)

# Limpieza de archivos generados
clean:
	@echo "$(GREEN)🧹 Limpiando archivos de cobertura y cache...$(NC)"
	rm -rf coverage_html/
	rm -f coverage.xml
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf deploy-build/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

# Igual que 'test' pero con timeout, pensado para la pipeline de CI/CD
test-ci:
	@echo "$(GREEN)🤖 Ejecutando tests para CI/CD...$(NC)"
	$(PYTEST_CMD) $(TEST_ARGS) --timeout=300

# Comandos para ejecutar la aplicación
security:
	@echo "$(GREEN)🔎 Ejecutando análisis de seguridad del código (usando 'semgrep ci')...$(NC)"
	. venv/bin/activate && semgrep ci || exit 1
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

# Preparar archivos para despliegue (solo archivos de producción)
build-deploy:
	@echo "$(GREEN)📦 Preparando aplicación para despliegue...$(NC)"
	@echo "$(YELLOW)🔧 Instalando dependencias...$(NC)"
	@$(MAKE) install-dev
	@echo "$(YELLOW)🧪 Ejecutando tests para despliegue con timeout...$(NC)"
	@$(MAKE) test-ci
	@echo "$(YELLOW)📁 Preparando archivos de despliegue...$(NC)"
	@rm -rf deploy-build/
	@mkdir -p deploy-build
	@echo "$(YELLOW)📁 Copiando archivos de aplicación...$(NC)"
	@cp -r app/ deploy-build/
	@cp -r config/ deploy-build/
	@cp -r static/ deploy-build/
	@mkdir -p deploy-build/data
	@if [ -d "data/exams" ]; then \
		mkdir -p deploy-build/data/exams; \
		for exam_dir in data/exams/*/; do \
			if [ -d "$$exam_dir" ] && [ "$$(basename $$exam_dir)" != "answers" ]; then \
				cp -r "$$exam_dir" deploy-build/data/exams/; \
			fi; \
		done; \
	fi
	@cp pyproject.toml deploy-build/
	@cp README.md deploy-build/
	@cp LICENSE deploy-build/
	@echo "$(YELLOW)📦 Generando requirements.txt para Azure...$(NC)"
	@echo "# Generado automáticamente para despliegue en Azure" > deploy-build/requirements.txt
	@echo "# Dependencias básicas de la aplicación" >> deploy-build/requirements.txt
	@echo "import tomllib" > /tmp/gen_reqs.py
	@echo "with open('pyproject.toml', 'rb') as f:" >> /tmp/gen_reqs.py
	@echo "    data = tomllib.load(f)" >> /tmp/gen_reqs.py
	@echo "for dep in data['project']['dependencies']:" >> /tmp/gen_reqs.py
	@echo "    print(dep)" >> /tmp/gen_reqs.py
	@$(PYTHON_CMD) /tmp/gen_reqs.py >> deploy-build/requirements.txt
	@rm -f /tmp/gen_reqs.py
	@echo "$(YELLOW)🧹 Limpiando archivos innecesarios...$(NC)"
	@find deploy-build/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find deploy-build/ -name "*.pyc" -delete 2>/dev/null || true
	@find deploy-build/ -name "*.pyo" -delete 2>/dev/null || true
	@find deploy-build/ -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Aplicación lista para despliegue en: deploy-build/$(NC)"
