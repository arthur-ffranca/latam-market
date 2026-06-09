import requests
import pandas as pd

PAISES = {
    "BR":"Brasil","MX":"México","AR":"Argentina","CO":"Colômbia",
    "CL":"Chile","PE":"Peru","EC":"Equador","GT":"Guatemala",
    "CR":"Costa Rica","PA":"Panamá","UY":"Uruguai","DO":"República Dominicana",
    "BO":"Bolívia","PY":"Paraguai","HN":"Honduras","SV":"El Salvador",
    "NI":"Nicarágua","VE":"Venezuela",
}

INDICADORES = {
    "NY.GDP.MKTP.CD":    "pib_usd",
    "SP.POP.TOTL":       "populacao",
    "NY.GDP.PCAP.CD":    "pib_per_capita",
    "IT.NET.USER.ZS":    "internet_pct",
    "IT.CEL.SETS.P2":    "celular_por_100",
    "NY.GDP.MKTP.KD.ZG": "crescimento_pib",
    "FP.CPI.TOTL.ZG":    "inflacao_pct",
    "GC.DOD.TOTL.GD.ZS": "divida_pib_pct",
    "IC.BUS.EASE.XQ":    "ease_business",
    "IQ.CPA.STRS.XQ":    "estab_politica",
    "GE.EST":            "eficiencia_governo",
}

paises_str = ";".join(PAISES.keys())
resultados = {}

print("Coletando dados...\n")

for codigo, nome in INDICADORES.items():
    print(f"  -> {nome}")
    url = (
        f"https://api.worldbank.org/v2/country/{paises_str}"
        f"/indicator/{codigo}"
        f"?format=json&date=2019:2023&per_page=500"
    )
    try:
        r = requests.get(url, timeout=20)
        dados = r.json()
        registros = dados[1] if len(dados) > 1 and dados[1] else []

        pais_valor = {}
        for reg in registros:
            iso2  = reg.get("country", {}).get("id", "")
            valor = reg.get("value")
            ano   = reg.get("date", "0")
            if iso2 in PAISES and valor is not None:
                if iso2 not in pais_valor or ano > pais_valor[iso2][0]:
                    pais_valor[iso2] = (ano, valor)

        resultados[nome] = {PAISES[iso2]: v for iso2, (_, v) in pais_valor.items()}
        print(f"     OK - {len(resultados[nome])} paises")

    except Exception as e:
        print(f"     ERRO: {e}")

df = pd.DataFrame(resultados)
df.index.name = "Pais"

if "pib_usd" in df.columns:
    df["pib_usd_bi"] = df["pib_usd"] / 1e9
if "populacao" in df.columns:
    df["populacao_mi"] = df["populacao"] / 1e6

df = df.fillna(df.median(numeric_only=True))
df.to_csv("latam_dados_reais.csv")

print("\nSalvo em latam_dados_reais.csv")
print(df[["pib_usd_bi","populacao_mi","internet_pct","crescimento_pib","inflacao_pct"]].round(2).to_string())