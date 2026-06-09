# 🌎 LATAM Market Expansion Index

Modelo de priorização de mercados para expansão na América Latina, combinando dados reais do World Bank com técnicas de Machine Learning.

---

## 📌 Sobre o Projeto

Empresas que planejam expansão na LATAM geralmente tomam decisões baseadas apenas em tamanho de mercado (PIB e população). Este modelo vai além — combina **4 dimensões e 11 variáveis reais** para gerar um score de atratividade por país, considerando risco macroeconômico, maturidade digital e facilidade de fazer negócios.

**Resultado contra-intuitivo:** Costa Rica lidera o ranking à frente de Brasil e México, quando você pondera risco e potencial digital — não só escala.

---

## 🗂️ Estrutura do Projeto

```
latam-expansion-index/
│
├── coleta_v2.py              # Coleta de dados via World Bank REST API
├── latam_expansion.py        # Modelo principal + visualizações estáticas
├── dashboard_latam.py        # Dashboard interativo (Streamlit)
├── latam_dados_reais.csv     # Dados coletados (gerado pelo coleta_v2.py)
└── README.md
```

---

## 🔢 Metodologia

### Dimensões e Variáveis

| Dimensão | Variáveis | Peso padrão |
|---|---|---|
| Tamanho de Mercado | PIB, população, classe média | 30% |
| Potencial Digital | Internet %, smartphones, crescimento e-commerce | 25% |
| Ambiente Macro | Crescimento PIB, inflação, competitividade | 25% |
| Facilidade de Negócios | Ease of Business, estabilidade política, infraestrutura | 20% |

### Pipeline

```
World Bank API → Coleta → Normalização Min-Max → Score Ponderado → K-Means Clustering
```

1. **Coleta** — dados extraídos via World Bank REST API (2019-2023, valor mais recente disponível)
2. **Normalização** — Min-Max Scaler por variável; inflação invertida (menor = melhor)
3. **Score por dimensão** — média simples das variáveis normalizadas
4. **Score final** — média ponderada das 4 dimensões
5. **Clustering** — K-Means (k=3) para segmentar países em Alta, Média e Baixa Prioridade

### Pesos Configuráveis

Os pesos são ajustáveis via dashboard — o ranking muda conforme o setor:

- **Fintech** → Potencial Digital tem maior peso
- **Indústria** → Tamanho de Mercado domina
- **E-commerce** → Mercado + Digital equilibrados

---

## 📊 Resultados

### Ranking Geral (pesos padrão)

| # | País | Score | Grupo |
|---|---|---|---|
| 1 | Costa Rica | 0.601 | 🟢 Alta Prioridade |
| 2 | Brasil | 0.580 | 🟡 Média Prioridade |
| 3 | Uruguai | 0.580 | 🟢 Alta Prioridade |
| 4 | México | 0.560 | 🟡 Média Prioridade |
| 5 | Panamá | 0.530 | 🟢 Alta Prioridade |
| 6 | Chile | 0.516 | 🟢 Alta Prioridade |
| 7 | Argentina | 0.420 | 🟡 Média Prioridade |
| ... | ... | ... | ... |
| 18 | Honduras | 0.124 | 🔴 Baixa Prioridade |

### Principais Insights

- **Costa Rica #1** — inflação de 0,5%, crescimento de 5,1% e 85% de penetração de internet geram score superior a mercados muito maiores
- **Brasil e México em Média Prioridade** — dominam em escala mas perdem em previsibilidade macro
- **Colômbia surpreende negativamente** — inflação de 11,7% e crescimento fraco (0,71%) em 2022/2023 penalizam o score
- **Venezuela isolada** — score 0.270 reflete colapso macroeconômico estrutural

---

## 🚀 Como Executar

### 1. Instalar dependências

```bash
pip install requests pandas numpy matplotlib scikit-learn streamlit plotly
```

### 2. Coletar dados reais

```bash
python coleta_v2.py
```

Gera o arquivo `latam_dados_reais.csv` com dados do World Bank.

### 3. Rodar o modelo

```bash
python latam_expansion.py
```

Gera o ranking, relatório executivo e salva `latam_expansion_index.png`.

### 4. Abrir o dashboard interativo

```bash
python -m streamlit run dashboard_latam.py
```

Abre no navegador em `localhost:8501`.

---

## 🛠️ Tecnologias

- **Python 3.10+**
- **Pandas / NumPy** — manipulação de dados
- **Scikit-learn** — normalização e clustering
- **Matplotlib** — visualizações estáticas
- **Plotly + Streamlit** — dashboard interativo
- **World Bank REST API** — fonte de dados

---

## 📁 Fonte dos Dados

Todos os dados são públicos e gratuitos:

| Indicador | Código | Fonte |
|---|---|---|
| PIB total | NY.GDP.MKTP.CD | World Bank |
| População | SP.POP.TOTL | World Bank |
| PIB per capita | NY.GDP.PCAP.CD | World Bank |
| Internet % | IT.NET.USER.ZS | World Bank / ITU |
| Crescimento PIB | NY.GDP.MKTP.KD.ZG | World Bank / IMF |
| Inflação | FP.CPI.TOTL.ZG | World Bank / IMF |
| Dívida/PIB | GC.DOD.TOTL.GD.ZS | World Bank |
| Ease of Business | IC.BUS.EASE.XQ | World Bank |
| Estabilidade política | IQ.CPA.STRS.XQ | World Bank |
| Eficiência de governo | GE.EST | World Bank |

---

## ⚠️ Limitações

- Dados de 2022/2023 — cenário pode ter mudado
- Algumas variáveis usam proxies calculados (classe média, e-commerce)
- Modelo não captura fatores qualitativos (cultura, relacionamentos, timing)
- K-Means é sensível à escala — normalização é crítica

---

## 👤 Autor

Projeto desenvolvido como parte de portfólio em Strategy Analytics & Data Science.

Conecte-se no [LinkedIn](https://linkedin.com/in/seu-perfil)
