# CHANGELOG — C’alma Data (Ilha Faceira)

> Linha do tempo das entregas. Formato: **YYYY-MM-DD — título** + itens.

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
