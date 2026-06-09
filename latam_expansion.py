# -*- coding: utf-8 -*-
"""
LATAM Market Expansion Index — Modelo Completo
===============================================
Usa dados reais coletados via World Bank API (latam_dados_reais.csv)

Execucao:
    python latam_expansion.py

Requisitos:
    pip install pandas numpy matplotlib scikit-learn
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# =============================================================================
# 1. CARREGA DADOS REAIS
# =============================================================================

df = pd.read_csv("latam_dados_reais.csv", index_col="Pais")

# Proxies para variaveis sem fonte direta na API
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

print("=" * 55)
print("LATAM MARKET EXPANSION INDEX")
print("Dados: World Bank API (2019-2023)")
print("=" * 55)
print(f"\nPaises carregados: {len(df)}\n")

# =============================================================================
# 2. NORMALIZACAO E SCORE COMPOSTO
# =============================================================================

dimensoes = {
    "Tamanho de Mercado": {
        "vars": ["pib_usd_bi", "populacao_mi", "classe_media_pct"],
        "peso": 0.30
    },
    "Potencial Digital": {
        "vars": ["internet_pct", "smartphone_pct", "ecommerce_cresc"],
        "peso": 0.25
    },
    "Ambiente Macro": {
        "vars": ["crescimento_pib", "inflacao_pct", "idc_score"],
        "peso": 0.25
    },
    "Facilidade de Negocios": {
        "vars": ["ease_business", "estab_politica", "infraestrutura"],
        "peso": 0.20
    },
}

todas_vars = [v for d in dimensoes.values() for v in d["vars"]]
df_model = df[todas_vars].copy().astype(float)
df_model["inflacao_pct"] = 1 / (1 + df_model["inflacao_pct"].abs())

scaler = MinMaxScaler()
df_scaled = pd.DataFrame(
    scaler.fit_transform(df_model),
    index=df_model.index,
    columns=df_model.columns
)

scores = pd.DataFrame(index=df.index)
for dim, config in dimensoes.items():
    scores[dim] = df_scaled[config["vars"]].mean(axis=1)

scores["Score Final"] = sum(
    scores[dim] * config["peso"]
    for dim, config in dimensoes.items()
)
scores["Ranking"] = scores["Score Final"].rank(ascending=False).astype(int)

# =============================================================================
# 3. CLUSTERIZACAO
# =============================================================================

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
scores["Cluster"] = kmeans.fit_predict(scores[list(dimensoes.keys())])

means = scores.groupby("Cluster")["Score Final"].mean().sort_values(ascending=False)
nomes_cluster = {
    means.index[0]: "Alta Prioridade",
    means.index[1]: "Media Prioridade",
    means.index[2]: "Baixa Prioridade",
}
scores["Grupo"] = scores["Cluster"].map(nomes_cluster)
scores_sorted = scores.sort_values("Score Final", ascending=False)

print(f"{'#':<4} {'Pais':<28} {'Score':<8} {'Grupo'}")
print("-" * 60)
for pais, row in scores_sorted.iterrows():
    print(f"{row['Ranking']:<4} {pais:<28} {row['Score Final']:.3f}    {row['Grupo']}")

# =============================================================================
# 4. VISUALIZACOES
# =============================================================================

cores_grupo = {
    "Alta Prioridade":  "#48BB78",
    "Media Prioridade": "#ECC94B",
    "Baixa Prioridade": "#FC8181",
}

fig = plt.figure(figsize=(20, 16))
fig.patch.set_facecolor("#0f1117")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

plt.rcParams.update({
    "text.color":       "#e2e8f0",
    "axes.labelcolor":  "#e2e8f0",
    "xtick.color":      "#718096",
    "ytick.color":      "#718096",
    "axes.facecolor":   "#1a1f2e",
    "figure.facecolor": "#0f1117",
    "axes.edgecolor":   "#2d3748",
    "grid.color":       "#2d3748",
})

# Ranking Geral
ax1 = fig.add_subplot(gs[0, :2])
bar_cores = [cores_grupo[g] for g in scores_sorted["Grupo"]]
bars = ax1.barh(
    scores_sorted.index[::-1],
    scores_sorted["Score Final"][::-1],
    color=bar_cores[::-1], alpha=0.9, edgecolor="#0f1117", height=0.7
)
for bar, score, grupo in zip(bars, scores_sorted["Score Final"][::-1], scores_sorted["Grupo"][::-1]):
    ax1.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
             f"{score:.3f}", va="center", ha="left", fontsize=9,
             color=cores_grupo[grupo], fontweight="bold")
ax1.set_xlim(0, 0.98)
ax1.set_title("LATAM Market Expansion Index — Ranking Geral\n(World Bank API 2019-2023)",
              fontsize=13, fontweight="bold", color="#e2e8f0", pad=12)
ax1.set_xlabel("Score Composto (0-1)", fontsize=10)
ax1.grid(axis="x", alpha=0.3)
legend_patches = [mpatches.Patch(color=c, label=g) for g, c in cores_grupo.items()]
ax1.legend(handles=legend_patches, loc="lower right", fontsize=9,
           facecolor="#1a1f2e", edgecolor="#2d3748", labelcolor="#e2e8f0")

# Radar Top 5
ax2 = fig.add_subplot(gs[0, 2], polar=True)
dims   = list(dimensoes.keys())
angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist() + [0]
radar_cores = ["#48BB78", "#4299E1", "#ECC94B", "#F6AD55", "#FC8181"]
for i, pais in enumerate(scores_sorted.head(5).index):
    vals = [scores_sorted.loc[pais, d] for d in dims] + [scores_sorted.loc[pais, dims[0]]]
    ax2.plot(angles, vals, color=radar_cores[i], linewidth=2, label=pais)
    ax2.fill(angles, vals, color=radar_cores[i], alpha=0.08)
ax2.set_xticks(angles[:-1])
ax2.set_xticklabels([d.replace(" ", "\n", 1) for d in dims], fontsize=8, color="#a0aec0")
ax2.set_ylim(0, 1)
ax2.set_title("Perfil Top 5 Paises", fontsize=11, fontweight="bold", color="#e2e8f0", pad=20)
ax2.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=8,
           facecolor="#1a1f2e", edgecolor="#2d3748", labelcolor="#e2e8f0")
ax2.set_facecolor("#1a1f2e")
ax2.grid(color="#2d3748", alpha=0.5)

# Heatmap
ax3 = fig.add_subplot(gs[1, :])
heatmap_data = scores_sorted[dims].T
im = ax3.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
ax3.set_xticks(range(len(scores_sorted)))
ax3.set_xticklabels(scores_sorted.index, rotation=35, ha="right", fontsize=9)
ax3.set_yticks(range(len(dims)))
ax3.set_yticklabels(dims, fontsize=10)
ax3.set_title("Score por Dimensao — Todos os Paises",
              fontsize=13, fontweight="bold", color="#e2e8f0", pad=12)
for i in range(len(dims)):
    for j in range(len(scores_sorted)):
        val = heatmap_data.values[i, j]
        ax3.text(j, i, f"{val:.2f}", ha="center", va="center",
                 fontsize=8, color="black" if val > 0.6 else "white", fontweight="bold")
plt.colorbar(im, ax=ax3, orientation="vertical", fraction=0.015, label="Score (0-1)")

fig.suptitle("LATAM Market Expansion Index — World Bank Data 2023",
             fontsize=15, fontweight="bold", color="#e2e8f0", y=1.01)

plt.savefig("latam_expansion_index.png", dpi=150, bbox_inches="tight", facecolor="#0f1117")
print("\nGrafico salvo: latam_expansion_index.png")

# =============================================================================
# 5. RELATORIO
# =============================================================================

print("\n" + "=" * 55)
print("RELATORIO EXECUTIVO")
print("=" * 55)
for grupo in ["Alta Prioridade", "Media Prioridade", "Baixa Prioridade"]:
    subset = scores_sorted[scores_sorted["Grupo"] == grupo]
    print(f"\n[{grupo}] — {len(subset)} paises")
    for pais, row in subset.iterrows():
        print(f"  #{row['Ranking']} {pais} — Score {row['Score Final']:.3f}")
