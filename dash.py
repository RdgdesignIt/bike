import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from scipy.stats import zscore
import plotly.express as px
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Dashboard Vibrazioni", layout="wide")
st.title("🚴‍♂️ Dashboard Analisi Vibrazioni Sellino & Manubrio")

# 📥 Caricamento dati
df = pd.read_csv("dati.csv", sep=";")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.rename(columns={"superfice": "superficie"})
# df["data"] = pd.to_datetime(df["data"], errors="coerce")

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




if "manubrio+sellino" in variabili_grafico:
    df_sel["manubrio+sellino"] = df_sel["manubrio"] + df_sel["sellino"]






# 🧼 Conversione numerica
for col in ["manubrio", "sellino", "diff_percentuale"]:
    if col in df_sel.columns:
        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce")

# 📊 Calcolo outlier
if not df_sel.empty:
    df_sel["z_manubrio"] = zscore(df_sel["manubrio"])
    df_sel["z_sellino"] = zscore(df_sel["sellino"])
    out_z = df_sel[(df_sel["z_manubrio"].abs() > soglia_z) | (df_sel["z_sellino"].abs() > soglia_z)]

    Q1, Q3 = df_sel["manubrio"].quantile(0.25), df_sel["manubrio"].quantile(0.75)
    IQR = Q3 - Q1
    low_iqr = Q1 - iqr_coef * IQR
    high_iqr = Q3 + iqr_coef * IQR
    out_iqr = df_sel[(df_sel["manubrio"] < low_iqr) | (df_sel["manubrio"] > high_iqr)]

    X_ml = df_sel[["manubrio", "sellino"]].dropna()
    if len(X_ml) > 0:
        model_ml = IsolationForest(contamination=contamination, random_state=42)
        df_sel["outlier_ml"] = model_ml.fit_predict(X_ml)
        out_ml = df_sel[df_sel["outlier_ml"] == -1]
    else:
        df_sel["outlier_ml"] = pd.Series([None] * len(df_sel), index=df_sel.index)
        out_ml = pd.DataFrame()

    # 🚨 Record sospetti aggregati
    sospetti = pd.concat([out_z, out_iqr, out_ml]).drop_duplicates()
    st.subheader("🚨 Record Sospetti Identificati")
    if not sospetti.empty:
        st.dataframe(sospetti[["data","luogo", "manubrio", "sellino", "diff_percentuale"]])
    else:
        st.info("✅ Nessun record sospetto rilevato con i parametri correnti.")

    # 🧹 Esclusione manuale
    st.subheader("🧹 Escludi manualmente record sospetti")
    da_escludere = st.multiselect("Seleziona gli ID da escludere", sospetti.index.tolist())
    df_sel = df_sel.drop(index=da_escludere)
    st.success(f"{len(da_escludere)} record esclusi manualmente.")

    # 🧾 Costruisci tabella finale da esportare
    df_export = df_sel.copy()
    df_export["outlier_z"] = df_export.index.isin(out_z.index)
    df_export["outlier_iqr"] = df_export.index.isin(out_iqr.index)
    df_export["outlier_ml_flag"] = df_export["outlier_ml"].map({-1: "Outlier", 1: "Normale", None: "Non calcolato"})
    df_export["escluso_manual"] = df_export.index.isin(da_escludere)

    excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    # Foglio con tutti i dati + indicatori
    df_export.to_excel(writer, sheet_name="Analisi Completa", index=False)
    
    # Z-score
    if not out_z.empty:
        out_z.to_excel(writer, sheet_name="Outlier Z-score", index=False)
    
    # IQR
    if not out_iqr.empty:
        out_iqr.to_excel(writer, sheet_name="Outlier IQR", index=False)
    
    # ML
    if not out_ml.empty:
        out_ml.to_excel(writer, sheet_name="Outlier ML", index=False)

    # Esclusi manualmente
    if da_escludere:
        df_esclusi = df.loc[da_escludere]
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
import numpy as np
import matplotlib.pyplot as plt

st.subheader("📊 Distribuzione diff_percentuale + Outlier")

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





    # 📊 Outlier dinamici Plotly
    colA, colB, colC = st.columns(3)
    with colA:
        fig_z = px.scatter(df_sel, x=df_sel.index, y="manubrio", color=df_sel.index.isin(out_z.index),
                           title=f"Z-score ±{soglia_z}")
        st.plotly_chart(fig_z, use_container_width=True)
    with colB:
        fig_iqr = px.scatter(df_sel, x=df_sel.index, y="manubrio", color=df_sel.index.isin(out_iqr.index),
                             title=f"IQR coeff. {iqr_coef}")
        st.plotly_chart(fig_iqr, use_container_width=True)
    with colC:
        if not out_ml.empty:
            fig_ml = px.scatter(df_sel, x=df_sel.index, y="manubrio",
                                color=df_sel["outlier_ml"].map({-1: "Outlier", 1: "Normale", None: "N/D"}),
                                title="Isolation Forest")
            st.plotly_chart(fig_ml, use_container_width=True)

    # 🧬 Multivariata
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