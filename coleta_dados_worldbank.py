"""
LATAM Expansion Index — Coleta de Dados Reais
==============================================
Fonte: World Bank API (gratuita, sem autenticação)
Execução: rode na sua máquina local

Instalação:
    pip install wbdata pandas numpy

O script coleta automaticamente os indicadores mais recentes
disponíveis para os 18 países LATAM e salva em CSV.
"""

import datetime
import numpy as np
import pandas as pd
import wbdata

# =============================================================================
# 1. CONFIGURAÇÃO
# =============================================================================

# Países LATAM — código ISO 3166-1 alpha-2
PAISES = {
    "BR": "Brasil",
    "MX": "México",
    "AR": "Argentina",
    "CO": "Colômbia",
    "CL": "Chile",
    "PE": "Peru",
    "EC": "Equador",
    "GT": "Guatemala",
    "CR": "Costa Rica",
    "PA": "Panamá",
    "UY": "Uruguai",
    "DO": "República Dominicana",
    "BO": "Bolívia",
    "PY": "Paraguai",
    "HN": "Honduras",
    "SV": "El Salvador",
    "NI": "Nicarágua",
    "VE": "Venezuela",
}

# Indicadores do World Bank
# Código : nome amigável
# Todos disponíveis em: data.worldbank.org/indicator
INDICADORES = {
    # DIMENSÃO 1 — Tamanho de Mercado
    "NY.GDP.MKTP.CD":    "pib_usd",           # PIB em USD corrente
    "SP.POP.TOTL":       "populacao",          # População total
    "NY.GDP.PCAP.CD":    "pib_per_capita",     # PIB per capita USD

    # DIMENSÃO 2 — Potencial Digital
    "IT.NET.USER.ZS":    "internet_pct",       # % pop. usando internet
    "IT.CEL.SETS.P2":    "celular_por_100",    # Assinaturas celular /100 hab

    # DIMENSÃO 3 — Ambiente Macroeconômico
    "NY.GDP.MKTP.KD.ZG": "crescimento_pib",   # Crescimento real do PIB %
    "FP.CPI.TOTL.ZG":    "inflacao_pct",       # Inflação (IPC) %
    "GC.DOD.TOTL.GD.ZS": "divida_pib_pct",    # Dívida pública % PIB

    # DIMENSÃO 4 — Facilidade de Negócios
    "IC.BUS.EASE.XQ":    "ease_business",      # Ease of Doing Business score
    "IQ.CPA.STRS.XQ":    "estabilidade_politica", # CPIA estabilidade
    "GE.EST":            "eficiencia_governo", # Government Effectiveness
}

# Ano de referência — pega o mais recente disponível
ANO_REF = datetime.datetime(2022, 1, 1)

# =============================================================================
# 2. COLETA VIA API
# =============================================================================

def coletar_dados():
    """
    Coleta todos os indicadores para todos os países via World Bank API.
    Usa mrv=5 (most recent value) para preencher anos com dado ausente.
    """
    print("Coletando dados do World Bank API...")
    print(f"Países: {len(PAISES)} | Indicadores: {len(INDICADORES)}\n")

    codigos = list(PAISES.keys())
    frames = []

    for codigo_ind, nome in INDICADORES.items():
        print(f"  → {nome} ({codigo_ind})")
        try:
            serie = wbdata.get_series(
                indicator=codigo_ind,
                country=codigos,
                date=ANO_REF,
                mrv=5,          # usa valor mais recente dos últimos 5 anos
                convert_date=False
            )
            df_ind = serie.reset_index()
            df_ind.columns = ["país_codigo", "data", nome]
            df_ind = df_ind.groupby("país_codigo")[nome].first().reset_index()
            frames.append(df_ind.set_index("país_codigo"))
        except Exception as e:
            print(f"    ⚠️  Erro em {nome}: {e}")

    # Junta todos os indicadores
    df = pd.concat(frames, axis=1)

    # Adiciona nome do país
    df.index.name = "codigo"
    df["País"] = df.index.map(PAISES)
    df = df.set_index("País")

    return df


# =============================================================================
# 3. PÓS-PROCESSAMENTO
# =============================================================================

def processar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza e engenharia de features adicionais.
    """
    df = df.copy()

    # PIB em bilhões (mais legível)
    if "pib_usd" in df.columns:
        df["pib_usd_bi"] = df["pib_usd"] / 1e9

    # População em milhões
    if "populacao" in df.columns:
        df["populacao_mi"] = df["populacao"] / 1e6

    # Classe média proxy: PIB per capita normalizado
    # (sem fonte direta gratuita; usamos proxy baseado em PIB per capita)
    if "pib_per_capita" in df.columns:
        pib_max = df["pib_per_capita"].max()
        df["classe_media_proxy"] = (df["pib_per_capita"] / pib_max * 100).clip(0, 100)

    # Remove colunas brutas que viraram proxy
    colunas_remover = ["pib_usd", "populacao"]
    df = df.drop(columns=[c for c in colunas_remover if c in df.columns])

    # Report de dados ausentes
    print("\nDados ausentes por indicador:")
    ausentes = df.isnull().sum()
    for col, n in ausentes[ausentes > 0].items():
        print(f"  {col}: {n} países sem dado")

    # Preenche ausentes com mediana da coluna
    df = df.fillna(df.median(numeric_only=True))

    return df


# =============================================================================
# 4. SALVAR
# =============================================================================

def salvar(df: pd.DataFrame, caminho: str = "latam_dados_reais.csv"):
    df.to_csv(caminho)
    print(f"\n✅ Dados salvos em: {caminho}")
    print(f"   Shape: {df.shape}")
    print(f"\nPreview:")
    print(df[["pib_usd_bi", "populacao_mi", "internet_pct",
               "crescimento_pib", "inflacao_pct"]].round(2).to_string())


# =============================================================================
# 5. MAIN
# =============================================================================

if __name__ == "__main__":
    # Coleta
    df_raw = coletar_dados()

    # Processa
    df_final = processar(df_raw)

    # Salva
    salvar(df_final)

    print("""
=======================================================
PRÓXIMO PASSO
=======================================================
Com o CSV gerado, substitua o dicionário 'dados' no
arquivo latam_expansion.py pelos dados reais:

    df = pd.read_csv("latam_dados_reais.csv", index_col="País")

O restante do pipeline (normalização, score, cluster,
visualização) funciona exatamente igual.
=======================================================
""")
