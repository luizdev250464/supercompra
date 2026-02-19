#!/bin/bash
echo "=========================================="
echo "      SuperCompara - Iniciando..."
echo "=========================================="

# Instala dependências
echo "Instalando dependências..."
pip install -r requirements.txt -q

echo ""
echo "=========================================="
echo " App rodando em: http://localhost:5000"
echo " Pressione Ctrl+C para encerrar"
echo "=========================================="

# Abre o navegador (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 1.5 && open http://localhost:5000 &
else
    sleep 1.5 && xdg-open http://localhost:5000 &
fi

python app.py
