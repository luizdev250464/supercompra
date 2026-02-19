#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo ""
echo "=========================================="
echo "     SuperCompara - Inicializando..."
echo "=========================================="
echo ""

# ── 1. Verificar Python ──────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERRO] Python não encontrado!"
    echo "Instale em: https://python.org/downloads"
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo "[OK] $PYVER encontrado."

# ── 2. Criar / ativar ambiente virtual ────────
if [ ! -d ".venv" ]; then
    echo "[..] Criando ambiente virtual .venv ..."
    $PYTHON -m venv .venv
    echo "[OK] Ambiente virtual criado."
else
    echo "[OK] Ambiente virtual já existe."
fi

source .venv/bin/activate

# ── 3. Instalar dependências ─────────────────
echo "[..] Verificando dependências..."
pip install -r requirements.txt -q --disable-pip-version-check
echo "[OK] Dependências instaladas."

# ── 4. Iniciar servidor ──────────────────────
echo ""
echo "=========================================="
echo " App rodando em: http://localhost:5000"
echo " Pressione Ctrl+C para encerrar"
echo "=========================================="
echo ""

python app.py
