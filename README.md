# 🛒 SuperCompara

Compara preços em múltiplos supermercados a partir da sua lista de compras e monta o **carrinho mais barato**.

---

## ▶️ Como iniciar

### Windows (recomendado)
Dê duplo clique em **`iniciar.bat`** — ele instala as dependências e abre o app automaticamente.

### Manual (qualquer sistema)
```bash
pip install -r requirements.txt
python app.py
# Acesse http://localhost:5000
```

### Variáveis de ambiente opcionais
| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `5000` | Porta do servidor |
| `FLASK_DEBUG` | `0` | Ativar modo debug (`1` = ativado) |

---

## 🏪 Lojas suportadas

| Loja | Plataforma | Status |
|---|---|---|
| 💚 Savegnago | VTEX Intelligent Search | ✅ Ativo |
| 🧡 Taquaral | VipCommerce | ✅ Ativo |
| 💙 Super Koch | OSuper | ✅ Ativo |
| Pão de Açúcar | — | ❌ Bloqueia acesso externo |
| Carrefour | — | ❌ Bloqueia acesso externo |

> Os scrapers do Pão de Açúcar e Carrefour estão em `scrapers/` mas não são usados pois esses sites bloqueiam requisições externas.

---

## 📋 Como usar

1. Acesse `http://localhost:5000`
2. Digite sua lista de compras (um item por linha, máx. 30 itens)
3. Selecione as lojas desejadas
4. Clique em **"Buscar melhores preços"**
5. Veja a tabela comparativa com o mais barato destacado
6. O **Carrinho Ótimo** mostra o menor custo possível comprando cada item no mais barato

> 💡 Seja específico: `"arroz tio joão 5kg"` funciona melhor que só `"arroz"`.

---

## 🔧 Estrutura do projeto

```
supercompara/
├── app.py                  # Servidor Flask — rotas e lógica de comparação
├── requirements.txt        # Dependências Python
├── iniciar.bat             # Atalho Windows (instala deps + abre app)
├── iniciar.sh              # Atalho Mac/Linux
├── templates/
│   └── index.html          # Interface web (CSS + JS embutidos)
└── scrapers/
    ├── __init__.py         # Exporta as funções de busca ativas
    ├── savegnago.py        # VTEX Intelligent Search + fallback legacy
    ├── taquaral.py         # VipCommerce API + fallback HTML scraping
    ├── superkoch.py        # OSuper API + fallback HTML scraping
    ├── paodeacucar.py      # (inativo — site bloqueia acesso externo)
    └── carrefour.py        # (inativo — site bloqueia acesso externo)
```

---

## ⚙️ Detalhes técnicos

- Buscas em paralelo via `ThreadPoolExecutor` (máx. 12 workers simultâneos)
- Timeout de 15 s por tarefa — sem travar o servidor
- Deduplicação e sanitização automática dos itens da lista
- Cada scraper tenta múltiplos endpoints (API primária → API legada → scraping HTML)

---

## ⚠️ Observações

- As APIs dos supermercados podem mudar — se parar de funcionar, pode ser necessário ajustar os scrapers
- Os preços refletem o momento da busca
- Resultados podem variar por região (alguns sites retornam o estoque mais próximo)

---

## 🚀 Próximos passos (melhorias futuras)

- [ ] Adicionar mais supermercados (Atacadão, Assaí, Extra)
- [ ] Exportar lista para Excel / PDF
- [ ] Salvar listas favoritas no navegador
- [ ] Histórico de preços por produto
- [ ] Alertas de queda de preço
- [ ] Considerar frete no cálculo do carrinho ótimo
