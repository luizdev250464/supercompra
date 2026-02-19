"""
Scraper para Super Koch (SC) - Plataforma OSuper
OSuper tem API pública de busca acessível via frontend sem token.
Endpoint: /api/products/search?q={termo}&storeId={id}
"""
import requests
import re
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Referer': 'https://superkoch.com.br/',
    'Origin': 'https://superkoch.com.br',
}

BASE = 'https://superkoch.com.br'


def buscar_superkoch(termo: str) -> dict | None:
    """Busca produto no Super Koch via API OSuper."""

    resultado = _buscar_osuper_api(termo)
    if resultado:
        return resultado

    resultado = _buscar_html(termo)
    if resultado:
        return resultado

    return None


def _buscar_osuper_api(termo: str) -> dict | None:
    """Tenta múltiplos endpoints da plataforma OSuper"""
    endpoints = [
        f"{BASE}/api/products?q={quote(termo)}&limit=5",
        f"{BASE}/api/search?q={quote(termo)}&limit=5",
        f"{BASE}/busca?q={quote(termo)}&format=json",
        f"{BASE}/api/v1/products/search?q={quote(termo)}",
    ]

    for url in endpoints:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                ct = resp.headers.get('Content-Type', '')
                if 'json' in ct:
                    data = resp.json()
                    produto = _extrair_json(data, termo)
                    if produto:
                        return produto
        except Exception:
            continue
    return None


def _buscar_html(termo: str) -> dict | None:
    """Scraping HTML da página de busca"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    url = f"{BASE}/busca?q={quote(termo)}"
    try:
        resp = requests.get(url, headers={**HEADERS, 'Accept': 'text/html'}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"Erro ao acessar Super Koch: {e}")

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Procura JSON embutido (padrão OSuper com React/Next.js)
    import json
    for script in soup.find_all('script'):
        txt = script.string or ''
        if 'price' in txt.lower() and 'product' in txt.lower():
            # Tenta extrair JSON de window.__INITIAL_STATE__ ou similar
            match = re.search(r'window\.__(?:INITIAL_STATE|NEXT_DATA|STATE)__\s*=\s*(\{.*?\});', txt, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    produto = _extrair_json(data, termo)
                    if produto:
                        return produto
                except Exception:
                    pass

    # Procura elementos de produto no HTML
    seletores = [
        '[class*="product-card"]', '[class*="ProductCard"]',
        '[class*="product-item"]', '[class*="ProductItem"]',
        '[data-testid*="product"]',
    ]

    for sel in seletores:
        items = soup.select(sel)
        if items:
            p = _extrair_elemento_html(items[0], termo)
            if p:
                return p

    # Último fallback: extrai preço diretamente
    precos = re.findall(r'R\$\s*(\d{1,4}[.,]\d{2})', soup.get_text())
    if precos:
        vals = []
        for pr in precos:
            try:
                vals.append(float(pr.replace('.', '').replace(',', '.')))
            except ValueError:
                continue
        if vals:
            preco = sorted(vals)[0]
            if preco > 0:
                return _montar(f"{termo}", preco, f"{BASE}/busca?q={quote(termo)}", '')

    return None


def _extrair_json(data, termo: str) -> dict | None:
    """Extrai produto de estrutura JSON genérica"""
    if not data:
        return None

    # Procura lista de produtos em vários campos possíveis
    produtos = None
    if isinstance(data, list) and data:
        produtos = data
    elif isinstance(data, dict):
        for chave in ['products', 'data', 'items', 'results', 'hits', 'content']:
            val = data.get(chave)
            if isinstance(val, list) and val:
                produtos = val
                break
            elif isinstance(val, dict):
                inner = val.get('products') or val.get('data') or val.get('items', [])
                if isinstance(inner, list) and inner:
                    produtos = inner
                    break

    if not produtos or not isinstance(produtos[0], dict):
        return None

    p = produtos[0]

    nome = (p.get('name') or p.get('title') or p.get('description') or
            p.get('product_name') or p.get('productName') or termo)

    preco = 0.0
    for campo in ['price', 'sale_price', 'salePrice', 'promotional_price',
                  'promotionalPrice', 'current_price', 'currentPrice', 'valor']:
        v = p.get(campo)
        if v:
            try:
                preco = float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
                if preco > 0:
                    break
            except (ValueError, TypeError):
                continue

    if preco == 0:
        return None

    imagem = (p.get('image') or p.get('photo') or p.get('thumbnail') or
              p.get('imageUrl') or p.get('image_url') or '')
    if isinstance(imagem, list) and imagem:
        imagem = imagem[0].get('url', '') if isinstance(imagem[0], dict) else str(imagem[0])

    slug = p.get('slug') or p.get('url') or p.get('link') or p.get('href') or ''
    link = slug if str(slug).startswith('http') else f"{BASE}/{slug}".rstrip('/')

    return _montar(str(nome), float(preco), link, str(imagem))


def _extrair_elemento_html(elem, termo: str) -> dict | None:
    nome_el = (elem.select_one('[class*="name"]') or elem.select_one('[class*="title"]') or
               elem.select_one('h2') or elem.select_one('h3') or elem.select_one('a'))
    nome = nome_el.get_text(strip=True) if nome_el else termo

    preco_el = (elem.select_one('[class*="price"]') or elem.select_one('[class*="preco"]') or
                elem.select_one('[class*="Price"]'))
    if not preco_el:
        return None

    preco_txt = preco_el.get_text(strip=True)
    m = re.search(r'(\d{1,4}[.,]\d{2})', preco_txt)
    if not m:
        return None
    try:
        preco = float(m.group(1).replace('.', '').replace(',', '.'))
    except ValueError:
        return None

    if preco <= 0:
        return None

    link_el = elem.select_one('a[href]')
    href = link_el['href'] if link_el else ''
    link = href if str(href).startswith('http') else f"{BASE}{href}"

    return _montar(nome, preco, link, '')


def _montar(nome: str, preco: float, link: str, imagem: str) -> dict:
    return {
        'nome': nome,
        'preco': preco,
        'preco_str': f"R$ {preco:.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Super Koch'
    }
