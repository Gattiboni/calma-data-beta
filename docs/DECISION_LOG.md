# DECISION_LOG — C’alma Data (Ilha Faceira)

> Decisões arquiteturais/produto. A mais recente fica no topo.

## 2025-09-24 — Padronização de branch e fonte de receita

**Decisão:** Operar o repositório em **apenas um branch: `main`**.  
**Motivos:** reduzir atrito com merges e alinhar com o fluxo do Neo (sem branches de trabalho paralelos).

**Impactos técnicos:**
- `backend/server.py`: KPI de **receita** passa a usar **Σ `itemRevenue` agregado no período** (sem `dimensions`/`limit=1`).
- Healthcheck permanece **ativo** (GA4: `itemRevenue` 7d; Ads: GAQL `LIMIT 1`).
- `/api/revenue-by-uh`: segue **real-only** (sem mock); em falha → `points: []`.
- `.env`: carregado da **raiz do projeto** como fonte canônica (fallback para `backend/.env`).

**Próximos:** corrigir `/api/acquisition-by-channel` para nunca 500 e retornar `points: []` em erro.


## 2025-09-23 — Receita oficial = Σ itemRevenue
**Decisão:** Toda a API e o frontend passam a tratar **Σ `itemRevenue`** como fonte de verdade da **receita** (ecommerce GA4).
- **Motivo:** A HSystem **não entrega `purchaseRevenue` confiável**; contabiliza receita no nível de itens. :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}
- **Impactos:**
  - KPIs e séries de receita usam agregação por item/dia.
  - `purchases/purchasers` ficam **indisponíveis/estimáveis** até `transaction_id` estar confiável (quando houver, reavaliar).
  - `health` (GA4) valida com `itemRevenue` (janela móvel de 7 dias).

## 2025-09-23 — `.env` na raiz do monorepo
**Decisão:** Centralizar o `.env` na **raiz** e garantir carregamento para o backend em dev (VS Code + PowerShell).
- **Motivo:** Evitar inconsistências de carregamento (hot reload / múltiplos shells).
- **Impacto:** Documentado no `OPERATIONS.md`; comandos de inicialização consideram a raiz.

## 2025-09-19 — Front-first e contratos simples (v2)
**Decisão:** Construir front **pixel-perfect** primeiro (placeholders), plugando dados por fases (GA4 overview → GA4 ecommerce → Ads) com **cache simples** e bypass via `refresh=1`. :contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7}
