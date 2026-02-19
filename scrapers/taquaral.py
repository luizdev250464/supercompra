"""
Scraper para Supermercado Taquaral (Campinas - SP)
Plataforma: VipCommerce

O VipCommerce expõe endpoints públicos de busca acessíveis pelo frontend,
sem necessidade de token. Testamos múltiplos padrões de URL conhecidos
e usamos BeautifulSoup como fallback via scraping HTML.
"""
import requests
import re
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Referer': 'https://www.taquaralsupermercado.com.br/',
}

BASE = 'https://www.taquaralsupermercado.com.br'


def buscar_taquaral(termo: str) -> dict | None:
    """
    Busca produto no Taquaral.
    Tenta múltiplos endpoints da API VipCommerce antes de fazer scraping HTML.
    """
    # Tentativa 1: API VipCommerce padrão /api/catalog/products
    resultado = _tentar_api_vipcommerce_v1(termo)
    if resultado:
        return resultado

    # Tentativa 2: endpoint alternativo /api/v2/catalog/products
    resultado = _tentar_api_vipcommerce_v2(termo)
    if resultado:
        return resultado

    # Tentativa 3: scraping da página de busca HTML
    resultado = _scraping_html(termo)
    if resultado:
        return resultado

    return None


def _tentar_api_vipcommerce_v1(termo: str) -> dict | None:
    """Endpoint padrão VipCommerce público"""
    endpoints = [
        f"{BASE}/api/catalog/products?term={quote(termo)}&limit=5",
        f"{BASE}/api/v1/catalog/products?q={quote(termo)}&per_page=5",
        f"{BASE}/api/products?search={quote(termo)}&limit=5",
        f"{BASE}/busca?q={quote(termo)}&format=json",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, headers={**HEADERS, 'Accept': 'application/json'}, timeout=8)
            if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', ''):
                data = resp.json()
                produto = _extrair_de_json_generico(data, termo)
                if produto:
                    return produto
        except Exception:
            continue
    return None


def _tentar_api_vipcommerce_v2(termo: str) -> dict | None:
    """Tenta endpoint de busca com headers específicos VipCommerce"""
    url = f"{BASE}/api/v2/catalog/products"
    params = {'q': termo, 'per_page': 5, 'page': 1}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return _extrair_de_json_generico(data, termo)
    except Exception:
        pass
    return None


def _scraping_html(termo: str) -> dict | None:
    """
    Faz scraping da página de busca HTML do Taquaral.
    Procura padrões comuns de e-commerce: preços, nomes de produto, links.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    url = f"{BASE}/busca?q={quote(termo)}"
    try:
        resp = requests.get(url, headers={**HEADERS, 'Accept': 'text/html'}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"Erro ao acessar Taquaral: {e}")

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Procura por dados JSON embutidos (padrão VipCommerce / React)
    scripts = soup.find_all('script', type='application/json')
    for script in scripts:
        try:
            import json
            data = json.loads(script.string or '{}')
            produto = _extrair_de_json_generico(data, termo)
            if produto:
                return produto
        except Exception:
            continue

    # Fallback: procura por elementos HTML de produto
    # Padrões comuns em temas VipCommerce
    seletores_produto = [
        'div.product-card', 'div.product-item', 'article.product',
        'div[class*="product"]', 'li[class*="product"]',
        '.prateleira li', '.vitrine li'
    ]

    for seletor in seletores_produto:
        items = soup.select(seletor)
        if items:
            produto = _extrair_de_html_elemento(items[0], termo)
            if produto:
                return produto

    # Último fallback: procura por qualquer preço na página
    return _extrair_preco_generico(soup, termo, url)


def _extrair_de_json_generico(data, termo: str) -> dict | None:
    """Tenta extrair produto de várias estruturas JSON possíveis"""
    if not data:
        return None

    # Estrutura tipo lista
    produtos = None
    if isinstance(data, list) and len(data) > 0:
        produtos = data
    elif isinstance(data, dict):
        for chave in ['products', 'data', 'items', 'results', 'produtos']:
            val = data.get(chave)
            if isinstance(val, list) and len(val) > 0:
                produtos = val
                break
            elif isinstance(val, dict) and val.get('data'):
                produtos = val['data']
                break

    if not produtos:
        return None

    p = produtos[0]
    if not isinstance(p, dict):
        return None

    # Nome
    nome = (p.get('name') or p.get('title') or p.get('nome') or
            p.get('description') or p.get('product_name') or termo)

    # Preço
    preco = 0
    for campo in ['price', 'sale_price', 'promotional_price', 'special_price',
                  'preco', 'preco_venda', 'price_sale', 'valor']:
        val = p.get(campo)
        if val and float(str(val).replace(',', '.').replace('R$', '').strip() or 0) > 0:
            preco = float(str(val).replace(',', '.').replace('R$', '').strip())
            break

    if preco == 0:
        return None

    # Imagem
    imagem = (p.get('image') or p.get('photo') or p.get('thumbnail') or
              p.get('images', [{}])[0].get('url', '') if isinstance(p.get('images'), list) else '')

    # Link
    slug = p.get('slug') or p.get('url') or p.get('link') or ''
    link = slug if slug.startswith('http') else f"{BASE}/{slug}"

    return _montar_resultado(nome, preco, link, str(imagem))


def _extrair_de_html_elemento(elem, termo: str) -> dict | None:
    """Extrai produto de elemento HTML BeautifulSoup"""
    from bs4 import BeautifulSoup

    # Nome
    nome_el = (elem.select_one('[class*="name"]') or
               elem.select_one('[class*="title"]') or
               elem.select_one('h2') or elem.select_one('h3') or
               elem.select_one('a'))
    nome = nome_el.get_text(strip=True) if nome_el else termo

    # Preço
    preco_el = (elem.select_one('[class*="price"]') or
                elem.select_one('[class*="preco"]') or
                elem.select_one('[class*="valor"]'))
    if not preco_el:
        return None

    preco_txt = preco_el.get_text(strip=True)
    preco = _parse_preco(preco_txt)
    if preco == 0:
        return None

    # Link
    link_el = elem.select_one('a[href]')
    href = link_el['href'] if link_el else ''
    link = href if href.startswith('http') else f"{BASE}{href}"

    return _montar_resultado(nome, preco, link, '')


def _extrair_preco_generico(soup, termo: str, url: str) -> dict | None:
    """Último recurso: busca qualquer padrão de preço R$ na página"""
    texto = soup.get_text()
    # Procura padrões tipo R$ 12,99 ou R$12.99
    matches = re.findall(r'R\$\s*(\d{1,4}[.,]\d{2})', texto)
    if not matches:
        return None

    # Pega o menor preço encontrado (mais provável ser o produto)
    precos = []
    for m in matches:
        try:
            precos.append(float(m.replace('.', '').replace(',', '.')))
        except ValueError:
            continue

    if not precos:
        return None

    preco = sorted(precos)[0]
    if preco <= 0:
        return None

    return _montar_resultado(f"{termo} (Taquaral)", preco, url, '')


def _parse_preco(texto: str) -> float:
    """Converte texto de preço para float"""
    if not texto:
        return 0.0
    limpo = re.sub(r'[^\d,.]', '', texto)
    # Formato brasileiro: 12,99 ou 1.234,56
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def _montar_resultado(nome: str, preco: float, link: str, imagem: str) -> dict:
    return {
        'nome': nome,
        'preco': preco,
        'preco_str': f"R$ {preco:.2f}".replace('.', ','),
        'link': link,
        'imagem': imagem,
        'loja': 'Taquaral'
    }
