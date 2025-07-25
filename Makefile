# Makefile para comandos de testing del proyecto PER Tests
# Facilita la ejecución de diferentes tipos de tests con opciones específicas

# Variables
PYTHON_CMD = venv/bin/python
PYTEST_CMD = venv/bin/python -m pytest
COV_MODULES = app config tools

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help test test-fast test-cov test-cov-html test-cov-xml test-unit test-integration test-api clean

# Comando por defecto
help:
	@echo "$(GREEN)PER Tests - Comandos disponibles:$(NC)"
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
	@echo "$(YELLOW)Limpieza:$(NC)"
	@echo "  make clean          - Limpiar archivos de cobertura y cache"
	@echo ""
	@echo "$(YELLOW)Ejemplos:$(NC)"
	@echo "  make test-fast                    # Durante desarrollo"
	@echo "  make test-cov                     # Para verificar cobertura"
	@echo "  make test-cov-html                # Para generar reporte visual"

# Tests rápidos sin cobertura (ideal para desarrollo)
test-fast:
	@echo "$(GREEN)🚀 Ejecutando tests rápidos (sin cobertura)...$(NC)"
	$(PYTEST_CMD)

# Alias para compatibilidad
test: test-fast

# Tests con cobertura básica
test-cov:
	@echo "$(GREEN)📊 Ejecutando tests con cobertura...$(NC)"
	$(PYTEST_CMD) --cov=app --cov=config --cov=tools --cov-report=term-missing

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
