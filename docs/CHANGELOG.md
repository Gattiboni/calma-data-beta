# CHANGELOG — C’alma Data (Ilha Faceira)

> Linha do tempo das entregas. Formato: **YYYY-MM-DD — título** + itens.

## [1.0.0] — 2025-09-29 — Release de Produção

### Added
- Deploy completo em **produção**:
  - **Backend** (FastAPI) publicado na **Railway**: [`https://calma-data-beta-production.up.railway.app`](https://calma-data-beta-production.up.railway.app)
  - **Frontend** (Vite/React) publicado na **Vercel**: [`https://calma-data-beta.vercel.app`](https://calma-data-beta.vercel.app)
- Integrações ativas e testadas:
  - **Google Analytics 4** (Service Account)
  - **Google Ads** (OAuth2)
  - **Supabase** (banco e autenticação)
  - **OpenAI API** (suporte a futuras análises)
  - **Resend** (envio de e-mails de feedback)
- Healthcheck `/api/health` confirmando integrações ativas:
  ```json
  {"status":"ok","integrations":{"ga4":true,"google_ads":true}}
Fixed
Erro 405 no envio de feedback: requisições agora direcionadas ao backend (/api/feedback).

Altura fixa da tabela de campanhas: substituída por wrapper responsivo com rolagem automática.

Inconsistências de variáveis de ambiente: unificação sob o padrão VITE_* no frontend.

Changed
KPI de Custo: agora formatado com formatBRLShort (sem casas decimais, abreviação “K”).

Layout do card de campanhas: rolagem controlada, responsividade aprimorada.

.env unificado: fonte única de variáveis para Railway e Vercel.

Documentação: atualização completa do README.md com instruções de deploy, stack e setup local.

Notes
Versão 1.0.0 marca o início da fase produção.

Entrega validada e aprovada para uso real pelo cliente.

## [Unreleased] — 2025-09-24
### Changed
- **KPI Receita:** correção — agora soma o **total do período** diretamente pela métrica `itemRevenue` (GA4 Data API).
- **Carregamento de env:** `.env` na raiz como fonte canônica; fallback para `backend/.env`.

### Fixed
- Healthcheck não “false-positivo”: valida GA4 com `itemRevenue` 7d e Ads com GAQL `LIMIT 1`.

### Chore
- Unificação de branches: remoção do branch `conflict_230925_0029` e operação somente em `main`.


## 2025-09-23 — Health ativo OK (GA4+Ads), receita via itemRevenue
- **Healthcheck ativo**: GA4 e Google Ads agora validados por chamadas reais; resultado `true/true` em ambiente local.
- **Receita (GA4)**: fonte oficial passou a ser **Σ `itemRevenue`** (soma por dia/item). *Não* usamos `purchaseRevenue` por limitação da HSystem. :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}:contentReference[oaicite:2]{index=2}
- **Contratos checados**:
  - `/api/kpis` → objeto com 7 chaves: `receita`, `reservas`, `diarias`, `clicks`, `impressoes`, `cpc`, `custo`.
  - `/api/performance-table` → `{ "rows": [...] }`.
- **Ambiente**:
  - `.env` posicionado na **raiz** do repositório; backend carrega via `load_dotenv`/execução com VS Code/PowerShell.
- **Frontend**:
  - Presets de período **7D/30D/90D** funcionando e refletindo GA4/Ads.
  - Date picker **custom** ainda a ajustar.
  - Gráficos principais permanecem **mock/dummy** (habilitar dados reais nas próximas sprints).
- **Observações de Log**:
  - Mensagem `ALTS creds ignored` do gRPC é **benigna** fora do GCP; pode ser ignorada ou silenciada via env (`GRPC_VERBOSITY=ERROR`) no processo local.

## 2025-09-19 — Base beta no Emergent (snapshot do repo)
- Backend FastAPI com rotas `/api/*` (mocks + integrações condicionais), frontend Vite/React/Tailwind, modo demo (`?demo=1`), e instruções de uso. :contentReference[oaicite:3]{index=3}
