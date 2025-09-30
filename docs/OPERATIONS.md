# OPERATIONS — Rotinas de Operação e Manutenção  
**C’Alma Data – Pousada Ilha Faceira**  
Versão: 1.0.0 – Produção  
Última atualização: 29/09/2025

---

## 1. Visão Geral

Este documento consolida as rotinas operacionais, comandos e práticas recomendadas para **execução, manutenção e suporte** do projeto **C’Alma Data** em ambiente local e produção.

Stack:  
- **Frontend**: Vite + React 18 + Tailwind CSS  
- **Backend**: FastAPI + Uvicorn  
- **Banco**: Supabase (PostgreSQL)  
- **Deploys**: Railway (backend), Vercel (frontend)  
- **Integrações**: Google Analytics 4, Google Ads (OAuth2), OpenAI, Resend

---

## 2. Ambientes de Produção

| Componente | Plataforma | URL | Observações |
|-------------|-------------|-----|-------------|
| **Frontend** | [Vercel](https://vercel.com) | [https://calma-data-beta.vercel.app](https://calma-data-beta.vercel.app) | Deploy automático via push na branch `main` |
| **Backend** | [Railway](https://railway.app) | [https://calma-data-beta-production.up.railway.app](https://calma-data-beta-production.up.railway.app) | Porta dinâmica `$PORT` |
| **Banco (Supabase)** | [Supabase](https://supabase.com) | [https://cycimguespvlynnabthx.supabase.co](https://cycimguespvlynnabthx.supabase.co) | Contém tabelas `users`, `feedbacks`, `reservations`, `ga4_cache`, `ga4_cache_overview` |

---

## 3. Deploys

### 3.1. Pipeline
- Branch principal: `main`
- Cada `commit + push` aciona **deploy automático**:
  - **Vercel** → Frontend (`frontend/`)
  - **Railway** → Backend (`backend/`)

### 3.2. Comandos e Configuração

#### Backend – Railway
- **Build Command:**  
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**  
  ```bash
  uvicorn server:app --host 0.0.0.0 --port $PORT
  ```
- **Healthcheck:**  
  [`/api/health`](https://calma-data-beta-production.up.railway.app/api/health)

#### Frontend – Vercel
- **Root Directory:** `frontend`  
- **Build Command:** `yarn build`  
- **Output Directory:** `dist`

### 3.3. Variáveis de Ambiente (Resumo)

| Ambiente | Chaves principais |
|----------|-------------------|
| **Backend (Railway)** | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GA4_PROPERTY_ID`, `GA4_PRIVATE_KEY`, `ADS_DEVELOPER_TOKEN`, `ADS_OAUTH_REFRESH_TOKEN`, `OPENAI_API_KEY`, `RESEND_API_KEY`, `FEEDBACK_TO`, `FEEDBACK_FROM` |
| **Frontend (Vercel)** | `VITE_BACKEND_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

> As variáveis devem estar espelhadas também no arquivo `.env` da **raiz** para testes locais.

---

## 4. Logs e Observabilidade

### 4.1. Railway (Backend)
- **Acesso:** [Railway Dashboard](https://railway.app/project/insightful-quietude)
- **Logs em tempo real:** seção **Deployments → Logs**
- **Região:** US East (Virginia)
- **Política de reinício:** On Failure (máx. 10 tentativas)
- **Healthcheck automático** após deploy

### 4.2. Vercel (Frontend)
- **Acesso:** [Vercel Project](https://vercel.com/alan-gattibonis-projects/calma-data-beta)
- **Logs de build e runtime** disponíveis no painel
- **Deploys:** automáticos, com histórico completo

### 4.3. Supabase (Banco)
- **Acesso:** [https://app.supabase.com/project/cycimguespvlynnabthx](https://app.supabase.com/project/cycimguespvlynnabthx)
- **Dashboard:** inclui **usage**, **tabelas**, **funções**, **logs** e **configurações**
- **Banco PostgreSQL** com tabelas:
  - `users`
  - `feedbacks`
  - `reservations`
  - `ga4_cache`
  - `ga4_cache_overview`

---

## 5. Operação Local

### 5.1. Requisitos
- Node.js LTS (>=18)
- Python 3.11+
- Git, Yarn, Pip
- PowerShell (Windows) ou Terminal (Mac/Linux)
- VS Code (recomendado)

### 5.2. Passos

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```
**Testes:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/health" | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://localhost:8001/api/kpis?start=2025-09-01&end=2025-09-07" | ConvertTo-Json -Depth 5
```

#### Frontend
```bash
cd frontend
cp .env.example .env
# edite: VITE_BACKEND_URL=http://localhost:8001
yarn install
yarn dev
```
**Acesso:** [http://localhost:5173](http://localhost:5173)

---

## 6. Testes de Rotas

| Endpoint | Descrição | Exemplo |
|-----------|------------|----------|
| `/api/health` | Healthcheck | ✅ retorna `{"status":"ok"}` |
| `/api/kpis` | KPIs do período | `?start=2025-09-01&end=2025-09-07` |
| `/api/performance-table` | Tabela de campanhas | `?start=2025-08-24&end=2025-09-23` |
| `/api/ga4/overview` | Métricas GA4 | `?start=7daysAgo&end=today` |
| `/api/ads/overview` | Métricas Ads | `?range=30d` |
| `/api/auth/register` | Cria usuário |
| `/api/auth/login` | Autentica usuário |
| `/api/feedback` | Envia mensagem ao dev (via Resend) |

---

## 7. Banco de Dados (Supabase)

### 7.1. Tabelas
- `users`: autenticação e gestão de usuários
- `feedbacks`: mensagens enviadas pelo botão “Fale com o Dev”
- `reservations`: dados de reservas e diárias
- `ga4_cache` / `ga4_cache_overview`: cache das métricas GA4

### 7.2. Recomendações
- Acessar via console Supabase
- Criar backups periódicos (opcional via export)
- Nunca editar tabelas diretamente em produção sem backup

---

## 8. Manutenção e Suporte

- **Monitorar logs** em Railway e Vercel após cada deploy
- **Verificar healthcheck** após deploys:  
  [`https://calma-data-beta-production.up.railway.app/api/health`](https://calma-data-beta-production.up.railway.app/api/health)
- **Validação funcional**:
  - Login e registro no frontend
  - Exibição dos KPIs e dashboards
  - Envio de feedbacks

---

## 9. Contatos

- **Responsável técnico:** Alan Gattiboni  
- **Organização:** Gattiboni Enterprises  
- **Repositório:** [https://github.com/Gattiboni/calma-data-beta](https://github.com/Gattiboni/calma-data-beta)

---

## 10. Anotações Importantes

- Deploys são **automáticos** ao push na `main`.
- Evitar commits diretos sem testes locais.
- Todas as variáveis de ambiente devem estar espelhadas no **Railway**, **Vercel** e `.env` local.
- Em caso de falhas:
  - Verificar logs do **Railway** e **Vercel**.
  - Validar variáveis de ambiente.
  - Rodar healthcheck.

---

> **C’Alma Data** — Operação leve, transparente e com propósito.
