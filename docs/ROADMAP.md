# ROADMAP — C’alma Data (Ilha Faceira)

> Documento vivo. Visão por fases, com critérios de aceite e dependências.

---

## 0) Estado atual (baseline estável)

**Entregue**
- **Health ativo** com teste real → **GA4 ✅ / Ads ✅** (local).  
- **Receita GA4 = Σ `itemRevenue`** como fonte oficial (HSystem não entrega `purchaseRevenue` confiável). :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}  
- Contratos checados:
  - `/api/kpis` → `{ receita, reservas, diarias, clicks, impressoes, cpc, custo }`.
  - `/api/performance-table` → `{ rows: [...] }`.  
- Front **pixel-perfect** com **presets 7D/30D/90D** funcionando; **Custom Date** a ajustar; alguns gráficos ainda **mock/dummy**. :contentReference[oaicite:2]{index=2}  
- Processo e docs v2 (front-first, integrações em fases, cache com `refresh=1`). :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}

**Riscos/observações**
- Séries podem vir vazias em janelas curtas com baixo tráfego (GA4).  
- Log `ALTS creds ignored` (gRPC) é **benigno** fora do GCP (ignorar em dev).  

---

## 1) Próximo sprint — **gráficos com dados reais** + **Date Picker Custom**

### 1.1 Gráficos com dados reais
**Objetivo**: substituir mocks por dados dos endpoints atuais.

- **Aquisição (Users)**  
  - **Endpoint**: `/api/acquisition-by-channel?metric=users&start&end`  
  - **Frontend**: LineChart de **users por canal** (x=data, y=valor, série=canal)  
  - **Critérios de aceite**:
    - Retorna `{ metric: "users", points: [{ date, values: { <channel>: number } }] }` com **≥1 ponto** para 30D.
    - Troca de métrica (quando houver outras) mantém contrato.
- **Receita por período (por UH)**  
  - **Endpoint**: `/api/revenue-by-uh?start&end`  
  - **Backend**: trocar mock por GA4 **Σ itemRevenue** agregando por “tipo de UH” (definir dimensão — ex.: `itemCategory` ou custom dimension).  
  - **Critérios**:
    - `{ points: [{ date, values: { Standard, Deluxe, Suite, Bungalow } }] }` non-empty em 30–90D.
- **UH por tipo (stacked bars)**  
  - **Endpoint**: `/api/sales-uh-stacked?start&end`  
  - **Backend**: série empilhada diária/semana por tipo de UH usando **itemRevenue** (ou **diárias** se preferir) — confirmar métrica.  
  - **Critérios**:
    - `{ series_labels: ["Standard","Deluxe","Suite","Bungalow"], points: [...] }` renderiza sem placeholder.
- **Heatmap conversões por hora/dia**  
  - **Endpoint**: `/api/campaign-conversion-heatmap?start&end`  
  - **Backend**: GA4 ou Ads (definir “conversão” para este heatmap); agregar `(dow,hour)`.  
  - **Critérios**:
    - `{ cells: [{ day: 0..6, hour: 0..23, value }] }` com densidade suficiente para 30D.

**Dependências**
- Confirmar dimensão que identifica **tipo de UH** no GA4 (ex.: `itemCategory` ou custom dimension).  
- Caso não exista ainda, **implantar dimensão** e documentar no `STACK.md`.

### 1.2 Date Picker Custom (corrigir)
**Objetivo**: presets já OK; **Custom** deve atualizar a query global.

- **Tarefas**:
  - Consolidar **fonte da janela** (contexto global) e disparo único de fetch ao alterar datas.
  - Garantir que **todos os cards/gráficos** leem a mesma janela (evitar chamadas divergentes).
- **Critérios de aceite**:
  - Alterar o custom range atualiza KPIs, todos os gráficos e tabela **de uma vez**.
  - Voltar aos presets (7D/30D/90D) mantém consistência.

---

## 2) Autenticação — **Login por e-mail com allowlist de domínio**

**Objetivo**: acesso autenticado por e-mail (Supabase Auth), com allowlist:
- **@amandagattiboni.com**
- **@ilhafaceira.com.br**
- **alangattiboni@gmail.com** (exceção explícita)

**Tarefas**
- Backend/Front: integrar **Supabase Auth** (email magic link).
- Middleware/Guard no front: proteger rotas (exceto “Sobre”).
- Allowlist:
  - Regra: `email.endsWith('@amandagattiboni.com') || email.endsWith('@ilhafaceira.com.br') || email === 'alangattiboni@gmail.com'`.
- UX:
  - Tela de login minimalista + estados (enviando, email enviado, erro).
  - Logout e exibição do e-mail logado.
- **Critérios de aceite**:
  - Usuário fora da allowlist **não** acessa a home (redirect para login).
  - Sessão persiste entre refreshes; logout limpa sessão.

**Dependências**
- Variáveis do Supabase no `.env` (já existem). :contentReference[oaicite:5]{index=5}  
- Política de domínio definida e testada.

---

## 3) **Onboarding “LEGAL PRA CACETE”** + **Página “Sobre”**

### 3.1 Onboarding (in-app tour e dicas por tela)
**Objetivo**: guiar o usuário com tours, dicas contextuais e “primeiros passos”.

- **Tarefas**
  - Definir **trilhas** (Home, Configurações, Tabela) e etapas (bubbles).
  - Salvar progresso (localStorage ou `profiles` no Supabase) para **não repetir** tours completos.
  - Tooltips “?” em cards/gráficos com **explicação curta** + link para “Sobre”.
- **Critérios de aceite**
  - Tour acionável manualmente (“Ver tour”) e automático apenas na **primeira** visita.
  - Tooltips presentes em **todos** os KPIs e gráficos.

### 3.2 “Sobre” (conteúdo e glossário)
**Objetivo**: explicar tudo sobre o dashboard, fórmulas e limitações.

- **Conteúdo mínimo**
  - **O que é** cada KPI e **como é calculado**.  
  - Limitação HSystem → **receita = Σ itemRevenue**; `purchaseRevenue` não é usado. :contentReference[oaicite:6]{index=6}  
  - **Fontes**: GA4 (overview/ecommerce) e Ads (impressions/clicks/cost/cpc/tabelão). :contentReference[oaicite:7]{index=7}  
  - **Como testar** (`/api/*`, `?refresh=1`). :contentReference[oaicite:8]{index=8}
- **Critérios de aceite**
  - Página “Sobre” navegável pelo menu; conteudão claro, com links para docs.
  - Glossário pesquisável e ancorado (hash links).

---

## 4) **Inteligência & IA** (camada real, state-of-the-art público)

**Objetivo**: transformar dados em **insights acionáveis** e **preditivos**.

**4.1 Tooltips inteligentes (explicabilidade rápida)**
- Heurísticas: variação vs período anterior, anomalias simples (z-score), insights de ROAS por campanha.
- Backend: `/api/insights/kpis?start&end`, `/api/insights/campaigns?start&end`.
- Critérios:
  - Cada KPI/gráfico exibe **1–3 insights curtos** (“Seu CPC caiu 12% vs 30D…”).

**4.2 Análises preditivas**
- Séries: `itemRevenue`, `reservas`, `diarias`, `clicks`, `impressoes`, `custo`.
- Técnicas abertas (exemplos): regressão com sazonalidade (statsmodels), ARIMA/ETS, Prophet; baseline simples antes de modelos mais pesados.
- Critérios:
  - Endpoint `/api/forecast/:metric?horizon=30` retorna `[{date, yhat, yhat_lower, yhat_upper}]`.
  - Front mostra **trendline** + faixa de confiança (área).

**4.3 Recomendador leve (campanhas)**
- Sinais: ROAS, CPC, CTR, share de custo/clicks, conversões/receita atribuída.
- Saída: 3 ações priorizadas por potencial impacto (“Aumentar 20% orçamento em X”, “pausar ad group Y”).
- Critério:
  - Endpoint `/api/recommendations/ads?start&end` retorna lista priorizada com `justificativa`.

**Dependências**
- Dados já integrados nos gráficos/tabelas (fases 1–3).  
- Documentar fórmulas e limitações em “Sobre”.

---

## 5) **Dashboard internacional padrão** (i18n + UX)

- **i18n**: i18next (ou equivalente) com **pt-BR** default e **en-US** opcional (strings centralizadas).
- **Unidades**: moeda e formatos por locale.
- **UX**: drilldown, tooltips ricos, quick infos em todos os KPIs (liga com 4.1).
- **Critérios**:
  - Toggle de idioma persistente.
  - Cada KPI com “info” (o que é / fórmula / por que importa).

---

## 6) **Loop de feedback integrado**

- **Em toda tela**: botão/ícone “Ajuda/Feedback”.
- Formulário com **texto + anexos** (prints) → **email do dev** + registro no Supabase.
- **Painel de mensagens** (em “Configurações”) para ver status/retorno do dev.
- Critérios:
  - Envio funcional com anexo.
  - Listagem de feedbacks do usuário autenticado.

---

## 7) Expansão futura (planejada)

- [ ] Integração com **Meta Ads**  
- [ ] Integração com **RD Station** (email marketing/automação)  
- [ ] Integração com outros **ERPs/partners**  
- [ ] Refinamento contínuo de UX (interatividade, responsividade)

---

## Cronograma sugerido (2–3 semanas por fase)

1. **Fase 1**: Gráficos reais + Date Picker Custom  
2. **Fase 2**: Login/allowlist + Onboarding (tour/Tooltips)  
3. **Fase 3**: “Sobre” + Base de IA (insights)  
4. **Fase 4**: Preditivo/Recommendations + i18n  
5. **Fase 5**: Feedback loop + Expansões (Meta/RD/ERPs)

> Ordem reflete dependências: insights e preditivo dependem dos gráficos/tabelas reais.

---

## Definições de pronto/feito

**DoR (Ready)**
- Endpoint e contrato definidos (request/response).
- Janela de datas padronizada.
- Dimensões/métricas mapeadas (ex.: tipo de UH).

**DoD (Done)**
- UI plugada, **sem mocks**.
- Testes manuais: presets 7D/30D/90D e Custom.
- Documentação atualizada (`OPERATIONS`, `STACK`, “Sobre”).
- Commit + push; changelog anotado. :contentReference[oaicite:9]{index=9}

---

## Itens trazidos do v2 (referências)
- Front-first com placeholders → depois integrações. :contentReference[oaicite:10]{index=10}  
- Receita oficial = Σ itemRevenue (HSystem). :contentReference[oaicite:11]{index=11}  
- Fases GA4 overview → GA4 ecommerce → Ads. :contentReference[oaicite:12]{index=12}
