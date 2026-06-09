# -*- coding: utf-8 -*-
"""
LATAM Market Expansion Index — Dashboard Streamlit
===================================================
Execucao:
    pip install streamlit plotly pandas numpy scikit-learn
    streamlit run dashboard_latam.py

Coloque este arquivo na mesma pasta que latam_dados_reais.csv
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import streamlit as st

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================

st.set_page_config(
    page_title="LATAM Expansion Index",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f1117; }
    [data-testid="stSidebar"] { background-color: #1a1f2e; }
    h1, h2, h3 { color: #e2e8f0 !important; }
    p, label { color: #a0aec0 !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CARREGA DADOS
# =============================================================================

@st.cache_data
def carregar_dados():
    df = pd.read_csv("latam_dados_reais.csv", index_col="Pais")

    df["classe_media_pct"] = (df["pib_per_capita"] / df["pib_per_capita"].max() * 100).clip(0, 100)
    df["smartphone_pct"]   = (df["internet_pct"] * 0.92).clip(0, 100)
    df["ecommerce_cresc"]  = (df["crescimento_pib"].clip(0) * 3 + 15).clip(5, 40)
    df["idc_score"]        = (df["internet_pct"] * 0.8).clip(0, 100)

    if "eficiencia_governo" in df.columns:
        df["ease_business"] = df["eficiencia_governo"].fillna(df["eficiencia_governo"].median())
    else:
        df["ease_business"] = 50

    if "estab_politica" not in df.columns:
        df["estab_politica"] = 50

    df["infraestrutura"] = (df["pib_per_capita"] / df["pib_per_capita"].max() * 80).clip(20, 80)
    return df


@st.cache_data
def calcular_scores(peso_mercado, peso_digital, peso_macro, peso_negocios):
    df = carregar_dados()

    dimensoes = {
        "Tamanho de Mercado":    {"vars": ["pib_usd_bi", "populacao_mi", "classe_media_pct"],         "peso": peso_mercado},
        "Potencial Digital":     {"vars": ["internet_pct", "smartphone_pct", "ecommerce_cresc"],       "peso": peso_digital},
        "Ambiente Macro":        {"vars": ["crescimento_pib", "inflacao_pct", "idc_score"],            "peso": peso_macro},
        "Facilidade de Negocios":{"vars": ["ease_business", "estab_politica", "infraestrutura"],       "peso": peso_negocios},
    }

    todas_vars = [v for d in dimensoes.values() for v in d["vars"]]
    df_model = df[todas_vars].copy().astype(float)
    df_model["inflacao_pct"] = 1 / (1 + df_model["inflacao_pct"].abs())

    scaler = MinMaxScaler()
    df_scaled = pd.DataFrame(
        scaler.fit_transform(df_model),
        index=df_model.index, columns=df_model.columns
    )

    scores = pd.DataFrame(index=df.index)
    total = sum(d["peso"] for d in dimensoes.values()) or 1
    for dim, config in dimensoes.items():
        scores[dim] = df_scaled[config["vars"]].mean(axis=1)

    scores["Score Final"] = sum(
        scores[dim] * (config["peso"] / total)
        for dim, config in dimensoes.items()
    )
    scores["Ranking"] = scores["Score Final"].rank(ascending=False).astype(int)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    scores["Cluster"] = kmeans.fit_predict(scores[list(dimensoes.keys())])
    means = scores.groupby("Cluster")["Score Final"].mean().sort_values(ascending=False)
    nomes = {means.index[0]: "Alta Prioridade", means.index[1]: "Media Prioridade", means.index[2]: "Baixa Prioridade"}
    scores["Grupo"] = scores["Cluster"].map(nomes)

    return scores.sort_values("Score Final", ascending=False), df, list(dimensoes.keys())


# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown("## Configurar Pesos")
st.sidebar.markdown("Ajuste a importancia de cada dimensao:")
st.sidebar.markdown("---")

peso_mercado  = st.sidebar.slider("Tamanho de Mercado",    0, 100, 30, 5)
peso_digital  = st.sidebar.slider("Potencial Digital",     0, 100, 25, 5)
peso_macro    = st.sidebar.slider("Ambiente Macro",        0, 100, 25, 5)
peso_negocios = st.sidebar.slider("Facilidade de Negocios",0, 100, 20, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Presets por Setor")

col1, col2 = st.sidebar.columns(2)

if col1.button("Fintech"):
    peso_digital  = 40
    peso_mercado  = 30
    peso_macro    = 20
    peso_negocios = 10

if col2.button("E-commerce"):
    peso_mercado  = 35
    peso_digital  = 35
    peso_macro    = 20
    peso_negocios = 10

if col1.button("Industria"):
    peso_mercado  = 40
    peso_macro    = 30
    peso_negocios = 20
    peso_digital  = 10

if col2.button("Balanceado"):
    peso_mercado  = 25
    peso_digital  = 25
    peso_macro    = 25
    peso_negocios = 25

st.sidebar.markdown("---")
st.sidebar.markdown("**Fonte:** World Bank API 2019-2023")
st.sidebar.markdown("**Paises:** 18 | **Variaveis:** 11")

# =============================================================================
# CALCULA
# =============================================================================

resultado, df_raw, dims = calcular_scores(peso_mercado, peso_digital, peso_macro, peso_negocios)

cores_grupo = {
    "Alta Prioridade":  "#48BB78",
    "Media Prioridade": "#ECC94B",
    "Baixa Prioridade": "#FC8181",
}

# =============================================================================
# HEADER
# =============================================================================

st.markdown("# LATAM Market Expansion Index")
st.markdown("**Modelo de priorizacao de mercados para expansao na America Latina**")
st.markdown("*Dados: World Bank API 2019-2023*")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
lider = resultado.index[0]
alta  = (resultado["Grupo"] == "Alta Prioridade").sum()
media = (resultado["Grupo"] == "Media Prioridade").sum()

col1.metric("Mercado #1",         lider,        f"Score {resultado.iloc[0]['Score Final']:.3f}")
col2.metric("Alta Prioridade",    f"{alta} paises",  "Entrada recomendada")
col3.metric("Media Prioridade",   f"{media} paises", "Monitorar 12-24m")
col4.metric("Paises Analisados",  "18",          "LATAM completo")

st.markdown("---")

# =============================================================================
# TABS
# =============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["Ranking", "Mapa de Calor", "Comparar Paises", "Dados"])

# ── TAB 1: RANKING ──────────────────────────────────────────────────────────
with tab1:
    col_esq, col_dir = st.columns([3, 2])

    with col_esq:
        st.markdown("### Ranking Geral")

        fig_rank = go.Figure(go.Bar(
            x=resultado["Score Final"],
            y=resultado.index,
            orientation="h",
            marker_color=[cores_grupo[g] for g in resultado["Grupo"]],
            text=[f"{s:.3f}" for s in resultado["Score Final"]],
            textposition="outside",
        ))
        fig_rank.update_layout(
            height=580,
            margin=dict(l=10, r=60, t=10, b=10),
            plot_bgcolor="#1a1f2e", paper_bgcolor="#0f1117",
            font_color="#e2e8f0",
            xaxis=dict(range=[0, 0.85], gridcolor="#2d3748", title="Score (0-1)"),
            yaxis=dict(autorange="reversed", gridcolor="#2d3748"),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with col_dir:
        st.markdown("### Perfil Top 5 — Radar")

        top5 = resultado.head(5)
        fig_radar = go.Figure()
        radar_cores = ["#48BB78", "#4299E1", "#ECC94B", "#F6AD55", "#FC8181"]

        for i, (pais, row) in enumerate(top5.iterrows()):
            vals = [row[d] for d in dims] + [row[dims[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=dims + [dims[0]],
                fill="toself", name=pais,
                line_color=radar_cores[i],
                fillcolor=radar_cores[i], opacity=0.15,
            ))

        fig_radar.update_layout(
            polar=dict(
                bgcolor="#1a1f2e",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="#2d3748", color="#718096"),
                angularaxis=dict(gridcolor="#2d3748", color="#a0aec0"),
            ),
            paper_bgcolor="#0f1117", font_color="#e2e8f0",
            legend=dict(bgcolor="#1a1f2e", bordercolor="#2d3748"),
            height=360, margin=dict(l=40, r=40, t=20, b=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("### Top 10")
        tabela = resultado.head(10)[["Ranking", "Score Final", "Grupo"]].copy()
        tabela["Score Final"] = tabela["Score Final"].round(3)
        st.dataframe(tabela, use_container_width=True, height=320)

# ── TAB 2: MAPA DE CALOR ────────────────────────────────────────────────────
with tab2:
    st.markdown("### Score por Dimensao")

    fig_heat = px.imshow(
        resultado[dims].T,
        color_continuous_scale="YlOrRd",
        zmin=0, zmax=1,
        text_auto=".2f",
        aspect="auto",
    )
    fig_heat.update_layout(
        height=320,
        plot_bgcolor="#1a1f2e", paper_bgcolor="#0f1117",
        font_color="#e2e8f0",
        xaxis=dict(tickangle=-35, tickfont=dict(size=11)),
    )
    fig_heat.update_traces(textfont_size=10)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### Matriz Estrategica — Atratividade vs Tamanho de Mercado")
    df_scatter = resultado.reset_index().merge(
        df_raw[["pib_usd_bi", "populacao_mi"]].reset_index(),
        on="Pais"
    )
    fig_sc = px.scatter(
        df_scatter,
        x="pib_usd_bi", y="Score Final",
        size="populacao_mi", color="Grupo",
        text="Pais",
        color_discrete_map=cores_grupo,
        size_max=60,
        labels={"pib_usd_bi": "PIB (USD Bilhoes)", "Score Final": "Score de Atratividade"},
    )
    fig_sc.update_traces(textposition="top center", textfont_size=10)
    fig_sc.update_layout(
        height=450,
        plot_bgcolor="#1a1f2e", paper_bgcolor="#0f1117",
        font_color="#e2e8f0",
        xaxis=dict(gridcolor="#2d3748"),
        yaxis=dict(gridcolor="#2d3748"),
        legend=dict(bgcolor="#1a1f2e", bordercolor="#2d3748"),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

# ── TAB 3: COMPARAR ─────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Comparar Paises")

    selecionados = st.multiselect(
        "Selecione ate 6 paises:",
        resultado.index.tolist(),
        default=resultado.index[:4].tolist(),
        max_selections=6,
    )

    if selecionados:
        comp = resultado.loc[selecionados]
        fig_comp = go.Figure()
        comp_cores = ["#48BB78","#4299E1","#ECC94B","#F6AD55","#FC8181","#B794F4"]

        for i, pais in enumerate(selecionados):
            row  = comp.loc[pais]
            vals = [row[d] for d in dims] + [row[dims[0]]]
            fig_comp.add_trace(go.Scatterpolar(
                r=vals, theta=dims + [dims[0]],
                fill="toself", name=pais,
                line_color=comp_cores[i % len(comp_cores)],
                fillcolor=comp_cores[i % len(comp_cores)], opacity=0.2,
            ))

        fig_comp.update_layout(
            polar=dict(
                bgcolor="#1a1f2e",
                radialaxis=dict(visible=True, range=[0, 1], gridcolor="#2d3748", color="#718096"),
                angularaxis=dict(gridcolor="#2d3748", color="#a0aec0"),
            ),
            paper_bgcolor="#0f1117", font_color="#e2e8f0",
            legend=dict(bgcolor="#1a1f2e", bordercolor="#2d3748"),
            height=420,
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### Dados Detalhados")
        cols = ["Ranking", "Score Final"] + dims
        st.dataframe(comp[cols].round(3).T, use_container_width=True)

# ── TAB 4: DADOS ─────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Dataset Completo")
    st.caption("Fonte: World Bank API 2019-2023")

    cols_exibir = ["Ranking", "Score Final", "Grupo"] + dims
    df_export = resultado[cols_exibir].round(3)
    st.dataframe(df_export, use_container_width=True, height=500)

    csv = df_export.to_csv().encode("utf-8")
    st.download_button(
        label="Baixar CSV",
        data=csv,
        file_name="latam_expansion_index.csv",
        mime="text/csv",
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#718096; font-size:12px'>"
    "LATAM Market Expansion Index | Fonte: World Bank API | "
    "Metodologia: Min-Max Normalization + K-Means Clustering"
    "</div>",
    unsafe_allow_html=True
)
