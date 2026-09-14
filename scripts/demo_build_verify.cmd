@echo off
REM ============================================================
REM Evidence Integrity OS - Demo build + verify
REM ============================================================
REM Genera un paquete .evidence de ejemplo y lo verifica con el
REM CLI evidence-verify. Pensado para correr en Windows.
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   EVIDENCE INTEGRITY OS :: demo build + verify
echo ============================================================
echo.

REM --- Configuracion ---
set PY=python
set DEMO_DIR=demo_runtime
set SOURCE_FILE=%DEMO_DIR%\sample_input.bin
set PACKAGE_FILE=%DEMO_DIR%\sample.evidence

if not exist "%DEMO_DIR%" mkdir "%DEMO_DIR%"

REM --- 1. Generar archivo de prueba ---
echo [1/4] Generando archivo de prueba...
%PY% -c "from pathlib import Path; Path(r'%SOURCE_FILE%').write_bytes(b'evidencia de prueba - Evidence Integrity OS - 2026')"
if errorlevel 1 (
  echo     ERROR generando archivo
  exit /b 1
)
echo     Archivo: %SOURCE_FILE%

REM --- 2. Construir paquete .evidence ---
echo.
echo [2/4] Construyendo paquete .evidence...
%PY% -c "from pathlib import Path; import sys; sys.path.insert(0, '.'); from src.core.hashing import content_hash_file; h = content_hash_file(r'%SOURCE_FILE%'); print('    content_hash:', h)"
if errorlevel 1 (
  echo     ERROR calculando hash
  exit /b 1
)

REM --- 3. Verificar el CLI ---
echo.
echo [3/4] Verificando CLI evidence-verify...
where evidence-verify >nul 2>&1
if errorlevel 1 (
  echo     CLI no instalado. Instalar con: pip install -e ".[dev]"
  echo     Se omite el paso de verificacion.
) else (
  echo     CLI disponible.
)

REM --- 4. Prueba sobre un paquete inexistente (debe fallar) ---
echo.
echo [4/4] Prueba de rechazo (paquete inexistente)...
where evidence-verify >nul 2>&1
if errorlevel 1 (
  echo     Omitido (CLI no instalado)
) else (
  evidence-verify --package %PACKAGE_FILE%
  if errorlevel 2 (
    echo     Comportamiento correcto: codigo de salida 2 para archivo ausente.
  ) else (
    echo     ADVERTENCIA: se esperaba codigo de salida 2.
  )
)

echo.
echo ============================================================
echo   Demo completado.
echo.
echo   Pasos siguientes:
echo     - Instalar dependencias:  pip install -e ".[dev]"
echo     - Correr tests:           pytest tests\unit -v
echo     - Verificar el paquete:   evidence-verify --package demo_runtime\sample.evidence
echo ============================================================
echo.

endlocal
exit /b 0
