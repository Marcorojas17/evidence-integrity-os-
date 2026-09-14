@echo off
REM ============================================================
REM Evidence Integrity OS - Aplica migraciones en orden
REM Uso: scripts\run_migrations.cmd
REM ============================================================

setlocal

set COMPOSE=docker compose -f ops\docker-compose.yml
set MIGRATIONS=migrations\0001_init_orders.sql migrations\0002_init_payment_events.sql migrations\0003_init_payment_fulfillments.sql migrations\0004_init_fulfillment_attempts.sql migrations\0005_indexes_and_constraints.sql

echo.
echo [1/2] Verificando servicios...
%COMPOSE% ps
echo.

echo [2/2] Aplicando migraciones...
for %%F in (%MIGRATIONS%) do (
  echo   -^> %%F
  %COMPOSE% exec -T db psql -U evidence -d evidence_dev -v ON_ERROR_STOP=1 < %%F
  if errorlevel 1 (
    echo     ERROR en %%F
    exit /b 1
  )
)

echo.
echo Migraciones aplicadas correctamente.
endlocal
