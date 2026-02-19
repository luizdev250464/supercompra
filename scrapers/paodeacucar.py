"""
Scraper para Pão de Açúcar
Usa a API interna do site: api.paodeacucar.com
"""
import requests
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.paodeacucar.com',
    'Referer': 'https://www.paodeacucar.com/',
}

# ID de loja padrão (São Paulo - Loja 1)
STORE_ID = 1


def buscar_paodeacucar(termo: str) -> dict | None:
    """
    Busca um produto no Pão de Açúcar e retorna o mais relevante.
    Retorna dict com: nome, preco, preco_str, unidade, link, imagem
    """
    url = (
        f"https://api.paodeacucar.com/v3/products/search"
        f"?term={requests.utils.quote(termo)}&store={STORE_ID}&size=5&page=0"
    )

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise Exception(f"Erro ao acessar Pão de Açúcar: {e}")

    produtos = data.get('products') or data.get('data', {}).get('products', [])

    if not produtos:
        return None

    # Pega o primeiro resultado (mais relevante)
    p = produtos[0]

    # Extrai preço — pode vir em campos diferentes
    preco = (
        p.get('price')
        or p.get('currentPrice')
        or p.get('salePrice')
        or p.get('promotionalPrice')
        or 0
    )

    # Alguns campos vêm como string "R$ 12,99" — limpa
    if isinstance(preco, str):
        preco = float(re.sub(r'[^\d,]', '', preco).replace(',', '.') or 0)

    nome = p.get('description') or p.get('name') or termo
    imagem = p.get('image') or p.get('photo') or ''
    link = f"https://www.paodeacucar.com/produto/{p.get('id', '')}"

    return {
        'nome': nome,
        'preco': float(preco),
        'preco_str': f"R$ {float(preco):.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Pão de Açúcar'
    }
