# DECISION_LOG — C’alma Data (Ilha Faceira)

> Decisões arquiteturais/produto. A mais recente fica no topo.

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
