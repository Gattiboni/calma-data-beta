# calma-data-beta
Beta version do C'alma Data, para build inteiro no Emergent

Entrega 19/09/2025


 Summary: Entrega concluída com sucesso! Implementações realizadas hoje:

1) Backend (FastAPI)
- Criado e publicado servidor FastAPI com rotas mockadas, todas com prefixo /api.
- Integração híbrida com GA4 e Google Ads: se variáveis GA4_* e ADS_* existirem, usa dados reais; caso contrário, mantém mocks. Cache simples com refresh=1.
- Endpoints: /api/kpis, /api/acquisition-by-channel, /api/revenue-by-uh, /api/sales-uh-stacked, /api/campaign-conversion-heatmap, /api/performance-table, /api/health.
- requirements.txt atualizado com fastapi/uvicorn e (opcional) google-analytics-data e google-ads.

2) Frontend (React + Vite + Tailwind + Recharts)
- Projeto Vite configurado (React 18, Tailwind 3, Recharts) com REACT_APP_BACKEND_URL=/api.
- Vite config atualizado (dev) + correção de variáveis para evitar “undefined”.
- Implementada UI completa: Sidebar (Início, Sobre, Configurações), Topbar com logo e chips 7D/30D/90D/Custom, 7 KPIs, 4 gráficos (linhas/empilhado/heatmap) e tabela de performance.
- Branding aplicado: paleta (Azul-Turquesa #2A8C99, Verde Orgânico #A8C6A6, Areia Suave #C4A981, Surface #FAFAF7, Darkgray #555251, Cinza Elegante #6D6A69), tipografia (Lora/Radley/Inter), radius 4/8/12/16 e sombras suaves.
- Modo de demonstração (dados dummy realistas) ativável por query: ?demo=1. Mantém hierarquia e usa valores plausíveis para KPIs, séries e tabela.
- Título atualizado: “C’alma Data, o dashboard da Ilha Faceira”.
- Logo substituída em /frontend/public/logo-calma-data.png.

3) Correções de ambiente
- Yarn Berry no Windows: orientado (e adicionado .yarnrc.yml) para nodeLinker: node-modules, resolvendo erro de esbuild com pacotes em .zip.
- Git push protection: sanitizado backend/.env, criado backend/.env.example, ampliado .gitignore para segredos e artefatos.

4) Como usar
- Local dev (recomendado):
  - Backend: uvicorn server:app --host 0.0.0.0 --port 8001 --reload
  - Frontend: yarn start
  - Preview com dados demo: http://localhost:3000/?demo=1
  - Preview com dados do backend: http://localhost:3000

5) Próximos passos sugeridos (quando retomarmos):
- Ajustar paleta específica dos gráficos para bater 100% com o mock do Figma.
- Trazer dados reais (GA4/Ads) com as credenciais rotacionadas e testadas.
- Pequenos refinamentos de espaçamentos/densidade e ícones sutis nos KPIs.

Obrigado! Ficou lindo e funcional. Quando quiser, seguimos com os ajustes finos. You rock também! 💙
Action: finish
Observation: 
 Summary: Entrega concluída com sucesso! Implementações realizadas hoje:

1) Backend (FastAPI)
- Criado e publicado servidor FastAPI com rotas mockadas, todas com prefixo /api.
- Integração híbrida com GA4 e Google Ads: se variáveis GA4_* e ADS_* existirem, usa dados reais; caso contrário, mantém mocks. Cache simples com refresh=1.
- Endpoints: /api/kpis, /api/acquisition-by-channel, /api/revenue-by-uh, /api/sales-uh-stacked, /api/campaign-conversion-heatmap, /api/performance-table, /api/health.
- requirements.txt atualizado com fastapi/uvicorn e (opcional) google-analytics-data e google-ads.

2) Frontend (React + Vite + Tailwind + Recharts)
- Projeto Vite configurado (React 18, Tailwind 3, Recharts) com REACT_APP_BACKEND_URL=/api.
- Vite config atualizado (dev) + correção de variáveis para evitar “undefined”.
- Implementada UI completa: Sidebar (Início, Sobre, Configurações), Topbar com logo e chips 7D/30D/90D/Custom, 7 KPIs, 4 gráficos (linhas/empilhado/heatmap) e tabela de performance.
- Branding aplicado: paleta (Azul-Turquesa #2A8C99, Verde Orgânico #A8C6A6, Areia Suave #C4A981, Surface #FAFAF7, Darkgray #555251, Cinza Elegante #6D6A69), tipografia (Lora/Radley/Inter), radius 4/8/12/16 e sombras suaves.
- Modo de demonstração (dados dummy realistas) ativável por query: ?demo=1. Mantém hierarquia e usa valores plausíveis para KPIs, séries e tabela.
- Título atualizado: “C’alma Data, o dashboard da Ilha Faceira”.
- Logo substituída em /frontend/public/logo-calma-data.png.

3) Correções de ambiente
- Yarn Berry no Windows: orientado (e adicionado .yarnrc.yml) para nodeLinker: node-modules, resolvendo erro de esbuild com pacotes em .zip.
- Git push protection: sanitizado backend/.env, criado backend/.env.example, ampliado .gitignore para segredos e artefatos.

4) Como usar
- Local dev (recomendado):
  - Backend: uvicorn server:app --host 0.0.0.0 --port 8001 --reload
  - Frontend: yarn start
  - Preview com dados demo: http://localhost:3000/?demo=1
  - Preview com dados do backend: http://localhost:3000

5) Próximos passos sugeridos (quando retomarmos):
- Ajustar paleta específica dos gráficos para bater 100% com o mock do Figma.
- Trazer dados reais (GA4/Ads) com as credenciais rotacionadas e testadas.
- Pequenos refinamentos de espaçamentos/densidade e ícones sutis nos KPIs.

Obrigado! Ficou lindo e funcional. Quando quiser, seguimos com os ajustes finos. You rock também! 💙
