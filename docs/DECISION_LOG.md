# DECISION_LOG — C’alma Data (Ilha Faceira)

> Decisões arquiteturais/produto. A mais recente fica no topo.

## 2025-09-29 — Unificação e correção de variáveis de ambiente

**Decisão:** Padronizar todas as variáveis de ambiente para o padrão `VITE_` (no frontend) e centralizar a configuração no `.env` da raiz, eliminando `REACT_APP_*`.

**Motivos:**
- Erro de build no Vercel e mensagens como “Backend URL ausente” eram causadas por nomes divergentes de variáveis.
- O código do frontend (App.jsx) já suporta `VITE_BACKEND_URL`, tornando redundante o uso de `REACT_APP_BACKEND_URL`.

**Impactos técnicos:**
- `VITE_BACKEND_URL` se torna fonte única para chamadas de API.
- `.env` raiz é espelhado nas plataformas (Vercel / Railway).
- Reduz risco de inconsistências entre ambientes.

---

## 2025-09-29 — Ajuste de wrapper da tabela de campanhas

**Decisão:** Remover altura fixa e criar wrapper responsivo para tabela `.table-campaigns`, com rolagem automática apenas quando necessário.

**Motivos:**
- Layout quebrava em telas menores com poucas linhas.
- Scroll duplo e excesso de espaço prejudicavam UX.

**Impactos técnicos:**
- CSS: adicionada `.table-campaigns-wrapper` com `max-height: 70vh` e `overflow-y: auto`.
- JSX: encapsulamento do `<table>` dentro de `<div className="table-campaigns-wrapper">`.
- Layout agora ajusta dinamicamente à quantidade de linhas.

---

## 2025-09-29 — Formatação de KPI de Custo

**Decisão:** Padronizar exibição de valores monetários nos KPIs com `formatBRLShort`, sem casas decimais e com abreviação (ex: `R$10,8K`).

**Motivos:**
- Manter consistência com o KPI de Receita.
- Melhorar legibilidade para valores altos.

**Impactos técnicos:**
- App.jsx: substituição de `.toFixed(2)` por `formatBRLShort(data?.kpis?.custo)`.
- Visual limpo e consistente para o painel principal.

---

## 2025-09-29 — Correção da API de Feedback

**Decisão:** Redirecionar requisição de feedback para o **backend** (`/api/feedback` do FastAPI), evitando chamada direta do frontend via domínio Vercel.

**Motivos:**
- Erro 405 (`Method Not Allowed`) devido a restrições de rota no Vercel.
- Backend já possui endpoint configurado com `RESEND_API_KEY`.

**Impactos técnicos:**
- Frontend ajustado para enviar feedback para `VITE_BACKEND_URL/api/feedback`.
- Emails agora enviados corretamente via Resend.

---

## 2025-09-28 — Wrapper de rolagem inteligente para card-body

**Decisão:** Remover `overflow-auto` do `.card-body` e delegar scroll exclusivamente ao wrapper interno da tabela.

**Motivos:**
- Evitar scroll duplo e garantir responsividade vertical.
- Melhorar UX em telas menores e dashboards longos.

**Impactos técnicos:**
- `.card-body`: altura automática e sem overflow.
- Wrapper exclusivo `.table-campaigns-wrapper` controla rolagem.

---

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
