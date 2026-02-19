"""
Scraper para Carrefour
Usa a API GraphQL do site delivery.carrefour.com.br
"""
import requests
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://mercado.carrefour.com.br',
    'Referer': 'https://mercado.carrefour.com.br/',
}

GRAPHQL_URL = "https://mercado.carrefour.com.br/api/graphql"

QUERY = """
query SearchQuery($term: String!, $from: Int, $to: Int) {
  productSearch(term: $term, from: $from, to: $to, selectedFacets: []) {
    products {
      productName
      items {
        images { imageUrl }
        sellers {
          commertialOffer {
            Price
            ListPrice
          }
        }
      }
      linkText
    }
  }
}
"""


def buscar_carrefour(termo: str) -> dict | None:
    """
    Busca um produto no Carrefour e retorna o mais relevante.
    """
    payload = {
        "query": QUERY,
        "variables": {"term": termo, "from": 0, "to": 4}
    }

    try:
        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise Exception(f"Erro ao acessar Carrefour: {e}")

    try:
        produtos = data['data']['productSearch']['products']
    except (KeyError, TypeError):
        produtos = []

    if not produtos:
        # Tenta API alternativa REST
        return _buscar_carrefour_rest(termo)

    p = produtos[0]
    nome = p.get('productName', termo)
    link = f"https://mercado.carrefour.com.br/{p.get('linkText', '')}/p"

    # Imagem
    try:
        imagem = p['items'][0]['images'][0]['imageUrl']
    except (KeyError, IndexError):
        imagem = ''

    # Preço
    try:
        preco = p['items'][0]['sellers'][0]['commertialOffer']['Price']
    except (KeyError, IndexError):
        preco = 0

    return {
        'nome': nome,
        'preco': float(preco),
        'preco_str': f"R$ {float(preco):.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Carrefour'
    }


def _buscar_carrefour_rest(termo: str) -> dict | None:
    """Fallback: API REST pública do Carrefour"""
    url = (
        f"https://mercado.carrefour.com.br/api/catalog_system/pub/products/search"
        f"?ft={requests.utils.quote(termo)}&_from=0&_to=4"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        produtos = resp.json()
    except Exception:
        return None

    if not produtos:
        return None

    p = produtos[0]
    nome = p.get('productName', termo)
    link = f"https://mercado.carrefour.com.br/{p.get('linkText', '')}/p"

    try:
        imagem = p['items'][0]['images'][0]['imageUrl']
    except (KeyError, IndexError):
        imagem = ''

    try:
        preco = p['items'][0]['sellers'][0]['commertialOffer']['Price']
    except (KeyError, IndexError):
        preco = 0

    return {
        'nome': nome,
        'preco': float(preco),
        'preco_str': f"R$ {float(preco):.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Carrefour'
    }
