# OPERATIONS — Dev local, testes e rotinas

## Requisitos
- Node.js LTS (>=18)
- Python 3.11+ (venv recomendado)
- VS Code (sugestão) + PowerShell (Windows)
- `.env` na **raiz do repo** (`/calma-data-beta/.env`) com chaves GA4/Ads/Supabase

## Subir o backend (FastAPI)
```powershell
cd "D:\Backup C 256\Desktop\Gattiboni Enterprises\Ilha Faceira\calma-data-beta\backend"
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
Testes rápidos (PowerShell)
powershell
Copiar código
Invoke-RestMethod -Uri "http://localhost:8001/api/health" | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://localhost:8001/api/kpis?start=2025-09-01&end=2025-09-07" | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri "http://localhost:8001/api/performance-table?start=2025-08-24&end=2025-09-23&refresh=1" | ConvertTo-Json -Depth 5
Contratos esperados

/api/kpis → objeto com receita, reservas, diarias, clicks, impressoes, cpc, custo.

/api/performance-table → { "rows": [...] }.

/api/acquisition-by-channel?metric=users → { "metric": "users", "points": [...] }.

Subir o frontend (Vite/React)
powershell
Copiar código
cd "D:\Backup C 256\Desktop\Gattiboni Enterprises\Ilha Faceira\calma-data-beta\frontend"
# backend é proxied via /api -> http://localhost:8001
"REACT_APP_BACKEND_URL=/api" | Out-File -FilePath .env -Encoding ascii
npm install
npm run start
# abrir http://localhost:3000
Variáveis de ambiente (resumo)
GA4: GA4_PROPERTY_ID, GA4_CLIENT_EMAIL, GA4_PRIVATE_KEY

Google Ads: ADS_DEVELOPER_TOKEN, ADS_LOGIN_CUSTOMER_ID, ADS_CUSTOMER_ID, ADS_OAUTH_CLIENT_ID, ADS_OAUTH_CLIENT_SECRET, ADS_OAUTH_REFRESH_TOKEN

Supabase: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

v2 já vinha prevendo essa organização e fases de integração. 
B_readme


Dicas / Known issues
gRPC/ALTS log (ALTS creds ignored): benigno fora do GCP; pode ser ignorado.

Cache/bypass: algumas rotas aceitam ?refresh=1 para forçar leitura direta das fontes.

Datas: se a janela for muito curta e o GA4 não tiver usuários, séries podem vir vazias.