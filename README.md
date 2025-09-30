# C’Alma Data — o dashboard da Ilha Faceira

> “Mais do que números, uma forma de contar histórias com alma.”

O **C’Alma Data** é mais do que um painel de indicadores — é uma **janela estratégica** que traduz a essência da **Pousada Ilha Faceira** em números vivos e cheios de significado.

Cada gráfico, card e tabela foi desenhado para **inspirar decisões conscientes**, refletir autenticidade e facilitar a gestão diária da operação.  
Aqui, **os dados contam histórias** — com propósito, clareza e serenidade.

---

## O que você vai encontrar

### Indicadores-Chave
Um resumo inteligente do mês com os números que realmente importam:  
**Receita, Reservas, Diárias, Cliques, Impressões e CPC**.  
Pense nesses cards como um **painel de bordo** para entender a saúde do negócio e a eficiência das campanhas.

### Receita por Período (por UH)
Descubra quais categorias mais contribuem para o faturamento e identifique seus **“dias ouro”**.

### Aquisição de Tráfego
Acompanhe de onde vêm seus visitantes (**orgânico**, **pago**, **direto**, **social**), identifique tendências e otimize seus canais.

### Preço Médio por Compra
Avalie o **tíquete médio** e veja o impacto de promoções e estratégias de **upsell**.

### Performance de Campanhas e Redes (Google Ads)
Entenda o **retorno de cada investimento** e ajuste o que for necessário para **melhorar resultados**.

Cada componente do dashboard foi desenvolvido com **cuidado e intenção** — alinhando tecnologia, design e essência.

---

## Nossa Essência

Assim como a **renda de bilros** inspira o design da pousada e sua marca, o C’Alma Data busca traduzir com leveza e elegância o que faz parte da identidade da **Ilha Faceira**:

- **Acolhimento**  
- **Autenticidade**  
- **Excelência**  
- **Conexão com a natureza**  
- **Respeito**

Explore, experimente e permita que os dados contem a história da sua operação — **com alma, propósito e serenidade**.

---

## Stack Técnica

| Camada     | Tecnologia                                  |
|-------------|---------------------------------------------|
| **Frontend** | [Vite](https://vitejs.dev/) + React 18 + Tailwind CSS + Recharts |
| **Backend**  | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Banco**    | [Supabase](https://supabase.com/) (PostgreSQL) |
| **Deploy**   | **Frontend** – [Vercel](https://vercel.com) <br> **Backend** – [Railway](https://railway.app) |
| **Integrações** | Google Analytics 4, Google Ads (OAuth2), OpenAI API, Resend (email) |

---

## Arquitetura de Deploy

### Backend – FastAPI
- **Plataforma:** Railway  
- **URL:** https://calma-data-beta-production.up.railway.app  
- **Porta:** `$PORT` (definida pela Railway)  
- **Comandos:**
  ```bash
  pip install -r requirements.txt
  uvicorn server:app --host 0.0.0.0 --port $PORT
  ```
- **Variáveis de ambiente principais:**
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - `GA4_PROPERTY_ID`, `GA4_PRIVATE_KEY`
  - `ADS_DEVELOPER_TOKEN`, `ADS_OAUTH_REFRESH_TOKEN`
  - `OPENAI_API_KEY`, `RESEND_API_KEY`
  - `FEEDBACK_TO`, `FEEDBACK_FROM`

### Frontend – Vite/React
- **Plataforma:** Vercel  
- **URL:** https://calma-data-beta.vercel.app  
- **Root Directory:** `frontend`  
- **Build Command:** `yarn build`  
- **Output Directory:** `dist`  
- **Variáveis de ambiente:**
  - `VITE_BACKEND_URL=https://calma-data-beta-production.up.railway.app`
  - `VITE_SUPABASE_URL=https://cycimguespvlynnabthx.supabase.co`
  - `VITE_SUPABASE_ANON_KEY=<chave>`

---

## Como rodar localmente

### 1. Clone o projeto
```bash
git clone https://github.com/Gattiboni/calma-data-beta.git
cd calma-data-beta
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```
Acesse: [http://localhost:8001/api/health](http://localhost:8001/api/health)

### 3. Frontend
```bash
cd frontend
cp .env.example .env
# edite VITE_BACKEND_URL para http://localhost:8001
yarn install
yarn dev
```
Acesse: [http://localhost:5173](http://localhost:5173)

---

## Autenticação & Banco

**Tabela `users` – Supabase**
```sql
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  created_at timestamp with time zone DEFAULT now()
);
```

Endpoints:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

---

## Suporte e Feedback

O C’Alma Data foi feito para **evoluir junto com você**.

Se surgir uma dúvida, sugestão ou ideia de melhoria, use o botão  
**“Fale com o Dev”** no topo da página.

Seu feedback é essencial para que o sistema continue refletindo a **essência da Ilha Faceira** — autêntica, acolhedora e em constante aperfeiçoamento.

---

## Licença

© 2025 Pousada Ilha Faceira • Desenvolvido com alma por Alan Gattiboni [Gattiboni Enterprises](https://github.com/Gattiboni)

---

> “Decisões conscientes nascem de dados com alma.”
