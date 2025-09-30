# STACK — Tecnologias e Arquitetura  
**C’Alma Data – Pousada Ilha Faceira**  
Versão: 1.0.0 – Produção  
Última atualização: 29/09/2025

---

## 1. Visão Geral

O **C’Alma Data** é um painel analítico completo, construído com foco em performance, clareza e integração direta com as fontes oficiais de dados da **Pousada Ilha Faceira**.

Este documento descreve as **tecnologias**, **bibliotecas**, **integrações** e **padrões de arquitetura** que sustentam o sistema.

---

## 2. Frontend

**Stack Principal**:  
- **Framework:** [Vite](https://vitejs.dev/) + [React 18](https://react.dev/)  
- **Estilo:** [Tailwind CSS](https://tailwindcss.com/)  
- **Gráficos:** [Recharts](https://recharts.org/en-US)  
- **State Management:** Hooks nativos do React  
- **Deploy:** [Vercel](https://vercel.com)

**Configurações Especiais**:
- **Modo demo:** `?demo=1` → gera dados plausíveis para demonstração da UI
- **Proxy de desenvolvimento:** `/api` → `http://localhost:8001`
- **Branding aplicado:** cores, tipografia, radius, alinhados à identidade da Ilha Faceira
- **Env:** `.env` com variáveis `VITE_BACKEND_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

**Comandos**:
```bash
yarn install
yarn dev       # ambiente local
yarn build     # build de produção
```

## 9. Estrutura de Diretórios

calma-data-beta/
├── backend/
│ ├── pycache/ # cache Python
│ ├── .env # variáveis do backend
│ ├── .env.example # modelo de variáveis
│ ├── requirements.txt # dependências Python
│ ├── server.py # app FastAPI principal
│ └── calma-data-beta.git # metadados do Railway
│
├── docs/ # documentação do projeto
│ ├── CHANGELOG.md
│ ├── DECISION_LOG.md
│ ├── OPERATIONS.md
│ ├── ROADMAP.md
│ └── STACK.md
│
├── frontend/
│ ├── .env # variáveis locais do front
│ ├── .env.production # variáveis de produção
│ ├── .yarnrc.yml # config Yarn
│ ├── index.html # template HTML
│ ├── package.json # dependências JS
│ ├── package-lock.json
│ ├── postcss.config.js
│ ├── public/
│ │ ├── About.pdf
│ │ └── logo-calma-data.png
│ └── src/
│ ├── App.css
│ ├── App.jsx
│ ├── AuthContext.jsx
│ ├── index.css
│ ├── index.jsx
│ ├── Login.css
│ └── Login.jsx
│
├── .emergent/ # configs internas
│ └── emergent.yml
│
├── .vscode/ # config VS Code
│ └── settings.json (se aplicável)
│
└── tree.txt # estrutura textual

---

## 3. Backend

**Stack Principal**:  
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)  
- **Servidor:** [Uvicorn](https://www.uvicorn.org/)  
- **Banco:** [Supabase](https://supabase.com/) (PostgreSQL)  
- **Deploy:** [Railway](https://railway.app)

**Endpoints Implementados**:
- `/api/kpis`
- `/api/acquisition-by-channel`
- `/api/revenue-by-uh`
- `/api/sales-uh-stacked`
- `/api/campaign-conversion-heatmap`
- `/api/performance-table`
- `/api/health`
- `/api/ga4/*`
- `/api/ads/*`
- `/api/auth/register`
- `/api/auth/login`
- `/api/auth/me`
- `/api/feedback`

**Receita (GA4)**: cálculo baseado na soma de `itemRevenue` (fonte oficial).  
> Importante: **não** utilizar `purchaseRevenue`.

**Cache:** Tabelas Supabase (`ga4_cache`, `ga4_cache_overview`) para reduzir latência.

**Execução local**:
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

**Comandos de Deploy (Railway)**:
```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port $PORT
```

---

## 4. Integrações

| Integração | Descrição | Tipo |
|-------------|------------|------|
| **Google Analytics 4** | Coleta de dados de usuários, receita e comportamento. | Service Account |
| **Google Ads** | Performance de campanhas e conversões. | OAuth2 |
| **Supabase** | Autenticação, banco de dados e cache. | API Key |
| **OpenAI API** | Suporte a análises futuras e respostas inteligentes. | API Key |
| **Resend** | Envio de e-mails de feedback (botão “Fale com o Dev”). | API Key |

---

## 5. Contratos de API

### 5.1. KPIs
```json
{
  "receita": 94775.12,
  "reservas": 39,
  "diarias": 386,
  "clicks": 7334,
  "impressoes": 186203,
  "cpc": 0.38,
  "custo": 1699.67
}
```

### 5.2. Tabela de Campanhas
```json
{
  "rows": [
    { "name": "Campanha 1", "type": "Search", "clicks": 1200, "cost_total": 350.0, ... }
  ],
  "total": { "clicks": 7334, "cost_total": 1699.67, ... }
}
```

### 5.3. Aquisição de Tráfego
```json
{
  "metric": "users",
  "points": [
    {
      "date": "2025-09-01",
      "values": {
        "Organic Search": 120.5,
        "Paid Search": 210.3,
        "Direct": 180.0,
        "Social": 90.2
      }
    }
  ]
}
```

---

## 6. Operacional

- Arquivo `.env` localizado na **raiz** do projeto, carregado automaticamente pelo VS Code ou PowerShell.  
- Parâmetro `refresh=1` pode ser adicionado à URL para **forçar atualização** e ignorar cache.

**Exemplo**:
```
https://calma-data-beta-production.up.railway.app/api/kpis?refresh=1
```

---

## 7. Deploy

| Componente | Plataforma | URL |
|-------------|-------------|-----|
| **Frontend** | Vercel | [https://calma-data-beta.vercel.app](https://calma-data-beta.vercel.app) |
| **Backend** | Railway | [https://calma-data-beta-production.up.railway.app](https://calma-data-beta-production.up.railway.app) |
| **Banco** | Supabase | [https://cycimguespvlynnabthx.supabase.co](https://cycimguespvlynnabthx.supabase.co) |

---

## 8. Observações

- **Branch principal:** `main`
- **Deploy automático** a cada push
- **Ambiente de produção** validado via healthcheck:
  [`https://calma-data-beta-production.up.railway.app/api/health`](https://calma-data-beta-production.up.railway.app/api/health)
- **Monitoramento** via dashboards Railway, Vercel e Supabase
- **Feedbacks** tratados via endpoint `/api/feedback`

---

> **C’Alma Data** — Stack moderna, eficiente e com propósito.
