import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from scipy.stats import zscore
import plotly.express as px
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import numpy as np

features = ["manubrio", "sellino"]  # puoi estendere se vuoi




st.set_page_config(page_title="Dashboard Vibrazioni", layout="wide")
st.title("🚴‍♂️ Dashboard Analisi Vibrazioni Sellino & Manubrio")

# 📥 Caricamento dati
df = pd.read_csv("dati.csv", sep=";")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.rename(columns={"superfice": "superficie"})
# df["data"] = pd.to_datetime(df["data"], errors="coerce")




def calcola_outlier(df, colonna, soglia_z=3.0, iqr_coef=1.5, contamination=0.1):
    df = df.copy()  # lavora su copia per sicurezza

    # 🔢 Z-Score
    media = df[colonna].mean()
    std_dev = df[colonna].std()
    z_score = (df[colonna] - media) / std_dev
    df["outlier_z"] = (np.abs(z_score) > soglia_z).astype(int)

    # 📦 IQR
    q1 = df[colonna].quantile(0.25)
    q3 = df[colonna].quantile(0.75)
    iqr = q3 - q1
    limite_inferiore = q1 - iqr_coef * iqr
    limite_superiore = q3 + iqr_coef * iqr
    df["outlier_iqr"] = ((df[colonna] < limite_inferiore) | (df[colonna] > limite_superiore)).astype(int)

    # 🤖 Isolation Forest
    clf = IsolationForest(contamination=contamination, random_state=42)
    X = df[[colonna]].values
    clf.fit(X)
    pred = clf.predict(X)  # -1 = outlier, 1 = normale
    df["outlier_label_ml"] = pred
    df["outlier_ml"] = (pred == -1).astype(int)

    return df



# 🎛️ Sidebar
st.sidebar.header("🔍 Filtri")
superfici = df["superficie"].dropna().unique()
superficie = st.sidebar.selectbox("🌍 Superficie", superfici)



df_sel = df.copy()


variabili_grafico = st.sidebar.multiselect(
    "📈 Seleziona variabili da visualizzare",
    options=["manubrio", "sellino", "diff_percentuale", "manubrio+sellino"],
    default=["manubrio"]
)






# 🚴‍♂️ Filtro Velocità (multiselect)
velocita_disponibili = sorted(df["velocita"].dropna().unique())
velocita_selezionate = st.sidebar.multiselect(
    "🚴‍♂️ Seleziona una o più velocità (km/h)",
    options=velocita_disponibili,
    default=velocita_disponibili
)

# 🏗️ Crea e addestra il modello
modello_iforest = IsolationForest(contamination=0.1, random_state=42)
modello_iforest.fit(df[features])

# ✅ Controllo selezione e filtro dati
if not velocita_selezionate:
    st.warning("Seleziona almeno una velocità per visualizzare il grafico.")
else:
    df_filtrato = df[df["velocita"].isin(velocita_selezionate)]








soglia_z = st.sidebar.slider("🎯 Z-score ±", 1.5, 3.5, 2.5)
iqr_coef = st.sidebar.slider("📐 IQR coefficiente", 1.0, 3.0, 1.5)
contamination = st.sidebar.slider("🤖 Contamination ML", 0.01, 0.20, 0.05)




with st.sidebar.expander("📘 Cosa fanno i metodi"):
    st.markdown("""
**Z-score**: rileva valori molto lontani dalla media statistica  
**IQR**: identifica valori estremi rispetto alla distribuzione interna  
**Isolation Forest**: identifica anomalie con machine learning multivariato  
""")

# 🔍 Filtro superficie
df = df[
    (df["superficie"].str.lower() == superficie.lower()) &
    (df["velocita"].isin(velocita_selezionate))
]

# 📊 Calcolo outlier su dataframe filtrato
df_sel = calcola_outlier(
    df_filtrato.dropna(subset=features),
    colonna="manubrio",
    soglia_z=soglia_z,
    iqr_coef=iqr_coef,
    contamination=contamination
)


# ➕ Feature combinata se richiesta
if "manubrio+sellino" in variabili_grafico:
    df_sel["manubrio+sellino"] = df_sel["manubrio"] + df_sel["sellino"]

# 🧼 Conversione numerica
for col in ["manubrio", "sellino", "diff_percentuale"]:
    if col in df_sel.columns:
        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce")

# 🚨 Record sospetti aggregati
out_z = df_sel[df_sel["outlier_z"] == 1]
out_iqr = df_sel[df_sel["outlier_iqr"] == 1]
out_ml = df_sel[df_sel["outlier_ml"] == 1]

sospetti = pd.concat([out_z, out_iqr, out_ml]).drop_duplicates()

st.subheader("🚨 Record Sospetti Identificati")
if not sospetti.empty:
    st.dataframe(sospetti[["data", "luogo", "manubrio", "sellino", "diff_percentuale"]])
else:
    st.info("✅ Nessun record sospetto rilevato con i parametri correnti.")

# 🧹 Esclusione manuale da Streamlit
st.subheader("🧹 Escludi manualmente record sospetti")
da_escludere = st.multiselect("Seleziona gli ID da escludere", sospetti.index.tolist())
df_sel = df_sel.drop(index=da_escludere)
st.success(f"{len(da_escludere)} record esclusi manualmente.")

# 🧾 Costruzione tabella finale da esportare
df_export = df_sel.copy()
df_export["outlier_z_flag"] = df_export["outlier_z"].map({1: "Outlier", 0: "Normale"})
df_export["outlier_iqr_flag"] = df_export["outlier_iqr"].map({1: "Outlier", 0: "Normale"})
df_export["outlier_ml_flag"] = df_export["outlier_ml"].map({1: "Outlier", 0: "Normale", None: "Non calcolato"})
df_export["escluso_manual"] = df_export.index.isin(da_escludere)

# 📥 Esportazione Excel multischeda
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df_export.to_excel(writer, sheet_name="Analisi Completa", index=False)
    if not out_z.empty:
        out_z.to_excel(writer, sheet_name="Outlier Z-Score", index=False)
    if not out_iqr.empty:
        out_iqr.to_excel(writer, sheet_name="Outlier IQR", index=False)
    if not out_ml.empty:
        out_ml.to_excel(writer, sheet_name="Outlier ML", index=False)
    if da_escludere:
        df_esclusi = df_filtrato.loc[da_escludere]
        df_esclusi.to_excel(writer, sheet_name="Record Esclusi", index=False)

excel_data = excel_buffer.getvalue()
st.download_button(
    label="📥 Scarica Analisi Multischeda",
    data=excel_data,
    file_name="vibrazioni_analisi_multi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)






    # 📋 Riepilogo
dev_std = df_sel["diff_percentuale"].std() * 100
st.subheader("📋 Riepilogo Diagnostico")
st.markdown(f"""
- Superficie: **{superficie}**  
- Record analizzati dopo esclusione: **{len(df_sel)}**  
- Velocità selezionate: **{', '.join(map(str, velocita_selezionate))} km/h**
- Dev. standard diff%: **{dev_std:.2f}%**  
""")

    # 📈 Visualizzazioni
  # Dizionario per raccogliere tutti gli outlier boxplot



# 🧮 Calcolo IQR
var = "diff_percentuale"
st.subheader("📈 Distribuzione diff_percentuale con Outlier evidenziati")

# ✅ Converte i dati in numerico (e forza i NaN dove non coerenti)
var = "diff_percentuale"
df_filtrato[var] = pd.to_numeric(df_filtrato[var], errors="coerce")
df_sel[var] = pd.to_numeric(df_sel[var], errors='coerce')

# 🧮 Calcola IQR per outlier
Q1 = df_filtrato[var].quantile(0.25)
Q3 = df_filtrato[var].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# 🔍 Estrai outlier e dati validi
outliers = df_filtrato[(df_filtrato[var] < lower_bound) | (df_filtrato[var] > upper_bound)]
valori_validi = df_filtrato[var].dropna().values

fig, ax = plt.subplots()
ax.boxplot(valori_validi, vert=False, showfliers=False)
ax.scatter(outliers[var], np.ones(len(outliers)), color="red", label="Outlier")
ax.set_xlabel(var)
ax.set_title("Boxplot diff_percentuale con Outlier")
ax.legend()
st.pyplot(fig)

# 📋 Tabella riepilogativa degli outlier
st.markdown(f"""
**Totale outlier rilevati**: {len(outliers)}  
**Limiti IQR**: `{lower_bound:.2f}` → `{upper_bound:.2f}`
""")

if not outliers.empty:
    st.dataframe(outliers[["data", "luogo", "velocita", "manubrio", "sellino", var]])
else:
    st.info("✅ Nessun outlier rilevato secondo la regola IQR.")


for var in variabili_grafico:
    fig, ax = plt.subplots()
    ax.boxplot(df_filtrato[var].dropna(), vert=False)
    ax.set_title(f"Distribuzione - {var}")
    ax.set_xlabel(var)
    st.pyplot(fig)


   

    if "sellino" in variabili_grafico and "manubrio" in variabili_grafico:
        fig, ax = plt.subplots()
    ax.scatter(df_sel["sellino"], df_sel["manubrio"], alpha=0.6, color='purple', edgecolors='w')
    ax.set_xlabel("Sellino")
    ax.set_ylabel("Manubrio")
    ax.set_title("🔘 Scatterplot Manubrio vs Sellino")
    st.pyplot(fig)


   

    fig = px.bar(df_sel, x="data", y="diff_percentuale",
    color="velocita",
    title="Differenza % tra manubrio e sellino per sessione",
    labels={"diff_percentuale": "Differenza %", "data": "Data"},
    hover_data=["manubrio", "sellino"])
    st.plotly_chart(fig, use_container_width=True)

    

    fig = px.box(df_sel, x="velocita", y="diff_percentuale",
    title="Distribuzione differenza % per velocità")
    st.plotly_chart(fig, use_container_width=True)
# 📌 Filtri selezionati
superficie = st.selectbox("Superficie", df["superficie"].unique())
velocita_selezionate = st.multiselect("Velocità", df["velocita"].unique())

# 🎯 Filtraggio base
df_filtrato = df[
    (df["superficie"].str.lower() == superficie.lower()) &
    (df["velocita"].isin(velocita_selezionate))
].copy()

# ✅ Verifica presenza dati validi
if df_filtrato.empty:
    st.warning(f"⚠️ Nessun dato valido per superficie '{superficie}' e velocità {velocita_selezionate}")
else:
    # 🧠 Calcolo outlier (Z-score, IQR, ML)
    df_sel = calcola_outlier(
        df_filtrato.dropna(subset=features),
        colonna="manubrio",
        soglia_z=soglia_z,
        iqr_coef=iqr_coef,
        contamination=contamination
    )

    # ➕ Feature combinata
    if "manubrio+sellino" in variabili_grafico:
        df_sel["manubrio+sellino"] = df_sel["manubrio"] + df_sel["sellino"]

    # 🧼 Conversione numerica
    for col in ["manubrio", "sellino", "diff_percentuale"]:
        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce")

df_sel = calcola_outlier(
    df_filtrato.dropna(subset=features),
    colonna="manubrio",
    soglia_z=soglia_z,
    iqr_coef=iqr_coef,
    contamination=contamination
)


variabile_y = st.selectbox(
    "📊 Seleziona variabile da visualizzare",
    options=variabili_grafico,
    index=variabili_grafico.index("manubrio") if "manubrio" in variabili_grafico else 0
)

st.markdown(f"### 📈 Outlier su variabile: `{variabile_y}`")


    # 🎯 Titolo descrittivo
title_suffix = f"🛞 {superficie} | ⚡ velocità: {', '.join(map(str, velocita_selezionate))}"

# 📊 Colonne grafiche
colA, colB, colC = st.columns(3)

with colA:
        fig_z = px.scatter(df_sel, x=df_sel.index, y=variabile_y, color=df_sel["outlier_z"])
        st.plotly_chart(fig_z, use_container_width=True)

with colB:
        fig_iqr = px.scatter(df_sel, x=df_sel.index, y=variabile_y, color=df_sel["outlier_iqr"])
        st.plotly_chart(fig_iqr, use_container_width=True)

with colC:
        fig_ml = px.scatter(df_sel, x=df_sel.index, y=variabile_y, color=df_sel["outlier_label_ml"])
        st.plotly_chart(fig_ml, use_container_width=True)

    # 🧬 Analisi multivariata
st.subheader("🧬 Analisi Multivariata")
variabili = st.multiselect("Scegli variabili", ["manubrio", "sellino", "diff_percentuale"],
                            default=["manubrio", "sellino", "diff_percentuale"])
X_mv = df_sel[variabili].dropna()
if len(X_mv) > 0 and len(variabili) >= 2:
    model_mv = IsolationForest(contamination=contamination, random_state=42)
    X_mv["outlier_multi"] = model_mv.fit_predict(X_mv)
    fig_mv = px.scatter_matrix(X_mv, dimensions=variabili,
                                color=X_mv["outlier_multi"].map({-1: "Outlier", 1: "Normale"}))
    st.plotly_chart(fig_mv, use_container_width=True)
    out_multi = X_mv[X_mv["outlier_multi"] == -1]
    st.download_button("📥 Scarica Outlier Multivariati", out_multi.to_csv(index=False),
                        "outlier_multivariati.csv")
else:
        st.info("⚠️ Nessun dato disponibile per analisi multivariata.")


    

    # 📄 Referto PDF
st.subheader("📄 Referto PDF Diagnostico")

def crea_pdf():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    styles = getSampleStyleSheet()
    content = [
        Paragraph("📋 Report Diagnostico Vibrazioni", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Superficie: {superficie}", styles["Normal"]),
        Paragraph(f"Velocità selezionate: {', '.join(map(str, velocita_selezionate))} km/h", styles["Normal"]),
        Paragraph(f"Record totali analizzati: {len(df_sel)}", styles["Normal"]),
        Paragraph(f"Deviazione standard diff%: {dev_std:.2f}%", styles["Normal"]),
        Paragraph(f"Record esclusi manualmente: {len(da_escludere)}", styles["Normal"]),
        Paragraph("📦 Il boxplot evidenzia la distribuzione delle vibrazioni misurate sul manubrio.", styles["Normal"]),
        Paragraph("I valori fuori dal box (outlier) indicano sessioni con vibrazioni anomale.", styles["Normal"]),
        Paragraph(f"Soglia Z-score: ±{soglia_z}", styles["Normal"]),
        Paragraph(f"IQR coefficiente: {iqr_coef}", styles["Normal"]),
        Paragraph(f"Contamination ML: {contamination:.2%}", styles["Normal"]),
        Paragraph(f"Outlier multivariati: {len(out_multi) if 'out_multi' in locals() else 'N/D'}", styles["Normal"])
    ]
    doc.build(content)
    return buf.getvalue()  # ✅ Corretto

pdf = crea_pdf()
st.download_button(
    label="📥 Scarica Referto PDF",
    data=pdf,
    file_name="report_vibrazioni.pdf",
    mime="application/pdf"
)