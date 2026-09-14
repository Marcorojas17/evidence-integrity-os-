# ---------------------------------------------------------------------------
# Evidence Integrity OS - Tareas de desarrollo
# ---------------------------------------------------------------------------
# Uso: make <target>
# ---------------------------------------------------------------------------

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose -f ops/docker-compose.yml

.PHONY: help install dev lint format typecheck test test-unit test-integration \
        test-security test-payments coverage security sbom clean \
        up down reset psql logs migrate-0001 migrate-0002 migrate-all

help: ## Muestra esta ayuda
	@echo "Evidence Integrity OS - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------------------

install: ## Instala dependencias de desarrollo
	pip install -e ".[dev]"

dev: install ## Alias de install

# ---------------------------------------------------------------------------
# Calidad de codigo
# ---------------------------------------------------------------------------

lint: ## Ejecuta ruff
	ruff check src tests scripts

format: ## Formatea con ruff
	ruff format src tests scripts
	ruff check --fix src tests scripts

typecheck: ## Ejecuta mypy
	mypy src

# ---------------------------------------------------------------------------
# Pruebas
# ---------------------------------------------------------------------------

test: ## Ejecuta todas las pruebas
	pytest

test-unit: ## Solo pruebas unitarias
	pytest -m unit

test-integration: ## Solo pruebas de integracion
	pytest -m integration

test-security: ## Solo pruebas de seguridad
	pytest -m security

test-payments: ## Solo pruebas de pagos
	pytest -m payments

coverage: ## Reporte de cobertura
	pytest --cov=src --cov-report=html
	@echo "Reporte en htmlcov/index.html"

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------

security: ## Analisis estatico de seguridad
	bandit -c pyproject.toml -r src

sbom: ## Genera SBOM CycloneDX
	pip-audit --format cyclonedx-json --output sbom.json || true
	@echo "SBOM en sbom.json"

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

up: ## Levanta PostgreSQL y Redis
	$(COMPOSE) up -d
	@echo "Servicios iniciados. Verifica con: make psql"

down: ## Detiene servicios sin borrar datos
	$(COMPOSE) down

reset: ## Detiene y borra volumenes (reset limpio)
	$(COMPOSE) down -v
	$(COMPOSE) up -d
	@echo "Base de datos reiniciada. Aplica migraciones con: make migrate-all"

psql: ## Abre sesion psql en la base de datos
	$(COMPOSE) exec db psql -U evidence -d evidence_dev

logs: ## Muestra logs de los servicios
	$(COMPOSE) logs -f

# ---------------------------------------------------------------------------
# Migraciones
# ---------------------------------------------------------------------------

migrate-0001: ## Aplica migracion 0001
	$(COMPOSE) exec -T db psql -U evidence -d evidence_dev < migrations/0001_init_orders.sql

migrate-0002: ## Aplica migracion 0002
	$(COMPOSE) exec -T db psql -U evidence -d evidence_dev < migrations/0002_init_payment_events.sql

migrate-all: ## Aplica todas las migraciones aprobadas
	make migrate-0001
	make migrate-0002

# ---------------------------------------------------------------------------
# Limpieza
# ---------------------------------------------------------------------------

clean: ## Limpia artefactos locales
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml sbom.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
