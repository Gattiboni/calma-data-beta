# STACK — Tecnologias e contratos

## Frontend
- **Vite + React 18 + Tailwind + Recharts**  
- Modo demo: `?demo=1` (dados plausíveis para UI)  
- Proxy de dev: `/api` → `http://localhost:8001`  
- Branding aplicado (cores, tipografia, radius). :contentReference[oaicite:9]{index=9}

## Backend
- **FastAPI + Uvicorn**
- Endpoints:
  - `/api/kpis`
  - `/api/acquisition-by-channel`
  - `/api/revenue-by-uh`
  - `/api/sales-uh-stacked`
  - `/api/campaign-conversion-heatmap`
  - `/api/performance-table`
  - `/api/health`
- **Receita (GA4)**: **Σ `itemRevenue`** por dia/item (fonte oficial). *Não* usar `purchaseRevenue`. :contentReference[oaicite:10]{index=10}:contentReference[oaicite:11]{index=11}

## Integrações
- **GA4 Data API** (Service Account)
- **Google Ads API** (OAuth2)
- **Supabase** (Auth/DB/Cache simples)

## Contratos principais
- **KPIs** → `{ receita, reservas, diarias, clicks, impressoes, cpc, custo }`
- **Tabela** → `{ rows: [...] }`
- **Aquisição** → `{ metric: "users" | "...", points: [...] }`

## Operacional
- `.env` na **raiz**; backend/VS Code/PowerShell carregam em dev.
- `refresh=1` para bypass de cache ao testar fontes reais.