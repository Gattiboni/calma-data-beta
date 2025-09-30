# ROADMAP — C’Alma Data

## Visão Geral  
Este roadmap descreve as próximas etapas evolutivas do **C’Alma Data**, priorizando clareza de execução, impacto funcional e expansão de inteligência analítica.  
Cada fase é incremental, garantindo estabilidade e continuidade do produto em produção.

---

## Fase 1 — **Aprimoramentos do Dashboard Atual (UX/UI + Dados)**

### 1.1. Formatação e Visualização
- Corrigir layout e responsividade das páginas de **Resumo Mensal**.
- Revisar **formatação dos gráficos** (eixos, legendas, espaçamentos).
- Padronizar **cores e tipografia** em todos os componentes visuais.
- Ajustar proporção e espaçamento entre cards, tabelas e painéis.

### 1.2. KPI Cards e Dials
- Melhorar **visual dos cards de insight** (hierarquia e contraste).
- Atualizar **progress dials** para exibir thresholds dinâmicos.
- Implementar **tooltips explicativos** com descrição dos indicadores.

---

## Fase 2 — **Inteligência de Dados e Insights Automáticos**

### 2.1. Tooltips Inteligentes
- Explicações automáticas para cada KPI:
  - O que representa  
  - Fórmula  
  - Por que é importante  
  - Variação vs período anterior  
  - Detecção de anomalias (z-score simples)  
  - Insight de ROAS por campanha  

### 2.2. Camada Analítica com GPT
- Integração GPT para análise descritiva e interpretativa:
  - Insights acionáveis baseados em variações de métricas
  - Identificação de tendências e outliers
- API de insights sob demanda:
  - `/api/insights` → retorna análise contextual dos dados carregados
  - Modo “Assistente de decisão”

---

## Fase 3 — **Configurações e Personalização**

### 3.1. Módulo “Configurações”
- Aba de **Configurações Básicas**:
  - Atualização de variáveis de ambiente controladas
  - Controle de acesso e autenticação
- Aba de **Relatórios e Visualizações**:
  - Ativar/desativar seções do dashboard
  - Selecionar métricas visíveis
  - Definir período padrão e formato de moeda
- Aba de **Estilo/Branding**:
  - Ajuste de cores, fontes, logotipo

---

## Fase 4 — **Análises Preditivas e Recomendação**

### 4.1. Modelos Preditivos
- Forecast simples (receita, reservas, custo) via modelos estatísticos (ARIMA ou regressão linear)
- Previsão de demanda por categoria de UH

### 4.2. Recomendador
- Sugestões automáticas de:
  - Investimento ideal por canal
  - Campanhas com melhor ROAS
  - Ajustes de orçamento

---

## Fase 5 — **Expansões e Integrações**

### 5.1. Novas Fontes de Dados
- Integração com **Meta Ads** (Facebook/Instagram)
- Integração com **RD Station** (CRM / automação de marketing)
- Integração com **ERP Desbravador** (reservas e faturamento)
- Normalização de dados entre plataformas

### 5.2. Camadas e Seções
- Organização do dashboard por **tema**:
  - Marketing Digital (GA4 + Ads + Meta)
  - Operacional (Reservas + Diárias)
  - Financeiro (Receita + Custos)

---

## Fase 6 — **Loop de Feedback e Suporte**

### 6.1. Feedback Integrado
- Botão fixo “Fale com o Dev” em todas as telas
- Histórico de feedbacks enviados no módulo “Configurações”
- Sistema de resposta com status (pendente / respondido / resolvido)

### 6.2. Base de Ajuda
- Adição de FAQ dinâmico
- Artigos breves com instruções de uso

---

## Fase 7 — **Internacionalização e Escalabilidade**

### 7.1. Internacionalização (i18n)
- Estrutura para múltiplos idiomas (PT-BR / EN)
- Seleção de idioma nas configurações

### 7.2. Escalabilidade
- Separação de instâncias por cliente
- Migração futura para plano multi-tenant

---

## Observações Gerais
- As fases são incrementais; cada entrega deve manter compatibilidade com a produção.
- As releases devem ser acompanhadas por **logs**, **testes** e **validação de UX**.
- Cada módulo (Insights, Configurações, Preditivo, Integrações) deve ser versionado independentemente no CHANGELOG.

---

> **C’Alma Data** — evolução contínua, com propósito e clareza.
