C'alma DATA Dashboard — Ilha Faceira 

Bem-vindo ao repositório oficial do dashboard analítico da Pousada Ilha Faceira. Projeto criado para oferecer um painel intuitivo, elegante e fiel ao branding “Calma para a Alma”, facilitando a gestão e análise de dados (GA4 e Google Ads).

# calma-data-beta
Beta version do C'alma Data, para build inteiro no Emergent

Entrega 19/09/2025

> **Status atual (2025-09-23)**  
> - **Health ativo OK**: GA4 ✅ / Google Ads ✅  
> - **Receita GA4 = Σ `itemRevenue`** (fonte oficial; HSystem não fornece `purchaseRevenue` confiável).  
> - Contratos confirmados: `/api/kpis` (7 chaves) e `/api/performance-table` (`rows`).  
> - Front com presets **7D/30D/90D** funcionando; date picker custom ainda a ajustar; gráficos principais ainda mock/dummy.  
> - Log `ALTS creds ignored` do gRPC é benigno fora do GCP.

---

## Summary
Entrega concluída com sucesso! Implementações realizadas:

1) **Backend (FastAPI)**
- Servidor FastAPI com rotas `/api/*`.
- Integração híbrida com **GA4** e **Google Ads**: se variáveis `GA4_*` e `ADS_*` existirem, usa dados reais; caso contrário, mantém mocks. Cache simples com `refresh=1`.
- **Receita GA4**: **Σ `itemRevenue`** (soma por dia/item). *Não* usar `purchaseRevenue`.  
- Endpoints: `/api/kpis`, `/api/acquisition-by-channel`, `/api/revenue-by-uh`, `/api/sales-uh-stacked`, `/api/campaign-conversion-heatmap`, `/api/performance-table`, `/api/health`.

2) **Frontend (React + Vite + Tailwind + Recharts)**
- Projeto Vite (React 18, Tailwind 3, Recharts) com `REACT_APP_BACKEND_URL=/api`.
- UI completa: Sidebar (Início, Sobre, Configurações), Topbar com logo e chips 7D/30D/90D/Custom, 7 KPIs, 4 gráficos e tabela de performance.
- Branding aplicado: paleta (Azul-Turquesa #2A8C99, Verde Orgânico #A8C6A6, Areia Suave #C4A981, Surface #FAFAF7, Darkgray #555251, Cinza Elegante #6D6A69), tipografia (Lora/Radley/Inter), radius 4/8/12/16 e sombras suaves.
- **Modo de demonstração** (dados dummy) via `?demo=1`.

3) **Correções de ambiente**
- `.env` **na raiz** do repo; backend carrega em dev (VS Code/PowerShell).
- `requirements.txt` atualizado (fastapi/uvicorn e, opcionalmente, google-analytics-data/google-ads).
- `.gitignore` ampliado para segredos e artefatos.

4) **Como usar (dev local)**
```powershell
# Backend
cd ./backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd ./frontend
"REACT_APP_BACKEND_URL=/api" | Out-File -FilePath .env -Encoding ascii
npm install
npm run start
# http://localhost:3000
Próximos passos sugeridos

Ativar dados reais nos gráficos (hoje mock).

Ajustar date picker custom.

(Opcional) Silenciar gRPC em dev: GRPC_VERBOSITY=ERROR.