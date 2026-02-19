"""
Scraper para Savegnago
O site usa VTEX — utiliza a API pública de busca do VTEX Intelligent Search
Endpoint: /api/io/_v/api/intelligent-search/product_search
"""
import requests
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.savegnago.com.br/',
}

BASE = "https://www.savegnago.com.br"


def buscar_savegnago(termo: str) -> dict | None:
    """
    Busca produto no Savegnago via VTEX Intelligent Search API.
    Retorna o produto mais relevante com nome, preço, link e imagem.
    """
    # Tenta primeiro pela API VTEX Intelligent Search
    resultado = _buscar_vtex_intelligent(termo)
    if resultado:
        return resultado

    # Fallback: API legada do VTEX
    return _buscar_vtex_legacy(termo)


def _buscar_vtex_intelligent(termo: str) -> dict | None:
    """VTEX Intelligent Search API"""
    url = (
        f"{BASE}/api/io/_v/api/intelligent-search/product_search"
        f"?query={requests.utils.quote(termo)}&count=5&page=1"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    produtos = data.get('products', [])
    if not produtos:
        return None

    return _extrair_produto_vtex(produtos[0], termo)


def _buscar_vtex_legacy(termo: str) -> dict | None:
    """API legada VTEX catalog"""
    url = (
        f"{BASE}/api/catalog_system/pub/products/search"
        f"?ft={requests.utils.quote(termo)}&_from=0&_to=4"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        produtos = resp.json()
    except Exception as e:
        raise Exception(f"Erro ao acessar Savegnago: {e}")

    if not produtos or not isinstance(produtos, list):
        return None

    return _extrair_produto_vtex_legacy(produtos[0], termo)


def _extrair_produto_vtex(p: dict, termo: str) -> dict | None:
    """Extrai dados do formato VTEX Intelligent Search"""
    nome = p.get('productName', termo)
    link = f"{BASE}/{p.get('linkText', '')}/p"

    # Imagem
    try:
        imagem = p['items'][0]['images'][0]['imageUrl']
    except (KeyError, IndexError):
        imagem = p.get('images', [{}])[0].get('imageUrl', '')

    # Preço — pode estar em várias localizações
    preco = 0
    try:
        sellers = p['items'][0]['sellers']
        preco = sellers[0]['commertialOffer']['Price']
    except (KeyError, IndexError):
        pass

    if preco == 0:
        try:
            preco = p['priceRange']['sellingPrice']['lowPrice']
        except (KeyError, TypeError):
            pass

    if preco == 0:
        return None

    return _montar_resultado(nome, float(preco), link, imagem)


def _extrair_produto_vtex_legacy(p: dict, termo: str) -> dict | None:
    """Extrai dados do formato VTEX legacy"""
    nome = p.get('productName', termo)
    link = f"{BASE}/{p.get('linkText', '')}/p"

    try:
        imagem = p['items'][0]['images'][0]['imageUrl']
    except (KeyError, IndexError):
        imagem = ''

    try:
        preco = p['items'][0]['sellers'][0]['commertialOffer']['Price']
    except (KeyError, IndexError):
        preco = 0

    if preco == 0:
        return None

    return _montar_resultado(nome, float(preco), link, imagem)


def _montar_resultado(nome: str, preco: float, link: str, imagem: str) -> dict:
    return {
        'nome': nome,
        'preco': preco,
        'preco_str': f"R$ {preco:.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Savegnago'
    }
