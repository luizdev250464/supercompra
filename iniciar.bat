@echo off
echo ==========================================
echo       SuperCompara - Iniciando...
echo ==========================================
echo.

:: Verifica se Python está instalado
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERRO: Python nao encontrado!
    echo Instale em: https://python.org/downloads
    pause
    exit /b 1
)

:: Instala dependências se necessário
echo Instalando dependencias...
pip install -r requirements.txt -q

echo.
echo ==========================================
echo  App rodando em: http://localhost:5000
echo  Pressione Ctrl+C para encerrar
echo ==========================================
echo.

:: Abre o navegador automaticamente
start "" http://localhost:5000

:: Inicia o app
python app.py

pause
