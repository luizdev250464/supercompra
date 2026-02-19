from flask import Flask, render_template, request, jsonify
from scrapers.savegnago import buscar_savegnago
from scrapers.taquaral import buscar_taquaral
from scrapers.superkoch import buscar_superkoch
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)

# ─────────────────────────────────────────────
#  Lojas ativas (Pão de Açúcar e Carrefour
#  bloqueiam acesso externo — substituídas por
#  lojas com APIs abertas)
# ─────────────────────────────────────────────
LOJAS = {
    'savegnago': {
        'nome': 'Savegnago',
        'emoji': '💚',
        'fn': buscar_savegnago,
    },
    'taquaral': {
        'nome': 'Taquaral',
        'emoji': '🧡',
        'fn': buscar_taquaral,
    },
    'superkoch': {
        'nome': 'Super Koch',
        'emoji': '💙',
        'fn': buscar_superkoch,
    },
}

MAX_ITENS = 30          # limite de itens por busca
TIMEOUT_BUSCA = 15      # segundos por tarefa de scraping
MAX_WORKERS = 12        # threads simultâneas no pool


@app.route('/')
def index():
    return render_template('index.html', lojas=LOJAS)


@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.json or {}
    lista_raw = data.get('itens', [])
    lojas_selecionadas = data.get('lojas', list(LOJAS.keys()))

    # Validação e sanitização dos itens
    lista = [str(i).strip() for i in lista_raw if str(i).strip()]
    lista = list(dict.fromkeys(lista))          # remove duplicatas mantendo ordem
    if not lista:
        return jsonify({'erro': 'Lista vazia'}), 400
    if len(lista) > MAX_ITENS:
        return jsonify({'erro': f'Máximo de {MAX_ITENS} itens por busca.'}), 400

    # Validação das lojas selecionadas
    lojas_selecionadas = [lid for lid in lojas_selecionadas if lid in LOJAS]
    if not lojas_selecionadas:
        return jsonify({'erro': 'Nenhuma loja válida selecionada.'}), 400

    resultados = {loja_id: {} for loja_id in lojas_selecionadas}
    erros = []

    def buscar_item(loja_id: str, item: str):
        fn = LOJAS[loja_id]['fn']
        r = fn(item)
        return loja_id, item, r

    tarefas = [(loja_id, item) for item in lista for loja_id in lojas_selecionadas]

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tarefas))) as executor:
        futures = {
            executor.submit(buscar_item, loja_id, item): (loja_id, item)
            for loja_id, item in tarefas
        }
        for future in as_completed(futures, timeout=TIMEOUT_BUSCA + 2):
            loja_id, item = futures[future]
            try:
                _, _, r = future.result(timeout=TIMEOUT_BUSCA)
                if r:
                    resultados[loja_id][item] = r
            except TimeoutError:
                erros.append(f"{LOJAS[loja_id]['nome']} - {item}: timeout")
                log.warning("Timeout: %s / %s", loja_id, item)
            except Exception as e:
                erros.append(f"{LOJAS[loja_id]['nome']} - {item}: {e}")
                log.error("Erro: %s / %s: %s", loja_id, item, e)

    comparacao = []
    totais = {loja_id: 0.0 for loja_id in lojas_selecionadas}
    total_otimo = 0.0

    for item in lista:
        linha = {'item': item, 'lojas': {}, 'mais_barato': None}
        precos = []
        for loja_id in lojas_selecionadas:
            prod = resultados[loja_id].get(item)
            linha['lojas'][loja_id] = prod
            if prod:
                totais[loja_id] += prod['preco']
                precos.append((loja_id, prod['preco']))

        if precos:
            precos.sort(key=lambda x: x[1])
            linha['mais_barato'] = precos[0][0]
            total_otimo += precos[0][1]

        comparacao.append(linha)

    return jsonify({
        'comparacao': comparacao,
        'totais': {k: round(v, 2) for k, v in totais.items()},
        'total_otimo': round(total_otimo, 2),
        'lojas_info': {k: {'nome': v['nome'], 'emoji': v['emoji']} for k, v in LOJAS.items()},
        'lojas_selecionadas': lojas_selecionadas,
        'erros': erros
    })


if __name__ == '__main__':
    import os, threading, webbrowser
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    print("🛒 SuperCompara iniciando...")
    print(f"📦 Acesse: http://localhost:{port}")

    # Abre o navegador automaticamente após o servidor subir
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    app.run(debug=debug, port=port, use_reloader=False)
