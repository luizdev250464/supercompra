@echo off
chcp 65001 >nul 2>&1
title SuperCompara
cd /d "%~dp0"

echo.
echo  ==========================================
echo       SuperCompara - Inicializando...
echo  ==========================================
echo.

:: ── 1. Verificar Python ──────────────────────
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERRO] Python nao encontrado no PATH!
    echo  Instale em: https://python.org/downloads
    echo  Marque "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  [OK] Python %PYVER% encontrado.

:: ── 2. Criar / ativar ambiente virtual ───────
IF NOT EXIST ".venv\Scripts\activate.bat" (
    echo  [..] Criando ambiente virtual .venv ...
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo  [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo  [OK] Ambiente virtual criado.
) ELSE (
    echo  [OK] Ambiente virtual ja existe.
)

call .venv\Scripts\activate.bat

:: ── 3. Instalar dependencias ─────────────────
echo  [..] Verificando dependencias...
pip install -r requirements.txt -q --disable-pip-version-check
IF ERRORLEVEL 1 (
    echo  [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo  [OK] Dependencias instaladas.

:: ── 4. Iniciar servidor ──────────────────────
echo.
echo  ==========================================
echo   App rodando em: http://localhost:5000
echo   Pressione Ctrl+C para encerrar
echo  ==========================================
echo.

python app.py

echo.
echo  Servidor encerrado.
pause
