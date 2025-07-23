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
df["data"] = pd.to_datetime(df["data"], errors="coerce")

# 🎛️ Sidebar
st.sidebar.header("🔍 Filtri")
superfici = df["superficie"].dropna().unique()
superficie = st.sidebar.selectbox("🌍 Superficie", superfici)

velocita_disponibili = sorted(df["velocita"].dropna().unique())
velocita_selezionate = st.sidebar.multiselect("🚴‍♂️ Velocità", velocita_disponibili, default=velocita_disponibili)

soglia_z = st.sidebar.slider("🎯 Z-score ±", 1.5, 3.5, 2.5)
iqr_coef = st.sidebar.slider("📐 IQR coefficiente", 1.0, 3.0, 1.5)
contamination = st.sidebar.slider("🤖 Contamination ML", 0.01, 0.20, 0.05)

# 🔍 Filtro principale
df = df[
    (df["superficie"].str.lower() == superficie.lower()) &
    (df["velocita"].isin(velocita_selezionate))
]
df_sel = df.copy()

# 🧼 Conversioni
for col in ["manubrio", "sellino", "diff_percentuale"]:
    if col in df_sel.columns:
        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce")
df_sel["mese"] = df_sel["data"].dt.month_name()

# 📊 Outlier
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

    # 🧾 Tabella finale
    df_sel = df_sel.dropna(subset=["data"])
    da_escludere = st.multiselect("🧹 Escludi record (ID)", df_sel.index.tolist())
    df_sel = df_sel.drop(index=da_escludere)
    df_export = df_sel.copy()
    df_export["outlier_z"] = df_export.index.isin(out_z.index)
    df_export["outlier_iqr"] = df_export.index.isin(out_iqr.index)
    df_export["outlier_ml_flag"] = df_export["outlier_ml"].map({-1: "Outlier", 1: "Normale", None: "Non calcolato"})
    df_export["escluso_manual"] = df_export.index.isin(da_escludere)

    # 🚨 Sospetti + media sessione
    sospetti = pd.concat([out_z, out_iqr, out_ml]).drop_duplicates()
    st.subheader("🚨 Record Sospetti Identificati")
    if not sospetti.empty:
        sospetti["mese"] = sospetti["data"].dt.month_name()
        sospetti["media_sessione"] = sospetti.apply(
            lambda row: df_export[
                (df_export["velocita"] == row["velocita"]) &
                (df_export["mese"] == row["mese"])
            ]["manubrio"].mean(),
            axis=1
        )
        sospetti["scostamento_dalla_media"] = (
            sospetti["manubrio"] - sospetti["media_sessione"]
        ).round(2)
        st.dataframe(sospetti[[
            "data", "velocita", "manubrio", "sellino", "diff_percentuale",
            "media_sessione", "scostamento_dalla_media"
        ]])
    else:
        st.info("✅ Nessun record sospetto rilevato.")

    # 📋 Riepilogo
    dev_std = df_sel["diff_percentuale"].std() * 100
    st.subheader("📋 Riepilogo Diagnostico")
    st.markdown(f"""
- Superficie: **{superficie}**
- Velocità: **{', '.join(map(str, velocita_selezionate))} km/h**
- Record analizzati: **{len(df_sel)}**
- Dev. standard diff%: **{dev_std:.2f}%**
""")

    # 📈 Visualizzazioni
    fig = px.bar(df_sel, x="data", y="diff_percentuale", color="velocita",
                 title="Differenza % tra manubrio e sellino per sessione")
    st.plotly_chart(fig, use_container_width=True)

    # 🧬 Multivariata
    st.subheader("🧬 Analisi Multivariata")
    variabili = st.multiselect("Variabili", ["manubrio", "sellino", "diff_percentuale"],
                               default=["manubrio", "sellino"])
    X_mv = df_sel[variabili].dropna()
    if len(X_mv) >= 2:
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