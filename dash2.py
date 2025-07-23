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
df = df[df["superficie"].str.lower() == superficie.lower()]
df_sel = df.copy()

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
        st.dataframe(sospetti[["data", "manubrio", "sellino", "diff_percentuale"]])
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

    
    # 📋 Riepilogo
    dev_std = df_sel["diff_percentuale"].std() * 100
    st.subheader("📋 Riepilogo Diagnostico")
    st.markdown(f"""
- Superficie: **{superficie}**  
- Record analizzati dopo esclusione: **{len(df_sel)}**  
- Dev. standard diff%: **{dev_std:.2f}%**  
""")

    # 📈 Visualizzazioni
    fig1, ax1 = plt.subplots()
    ax1.boxplot(df_sel["manubrio"].dropna(), vert=False)
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    ax2.scatter(df_sel["sellino"], df_sel["manubrio"], alpha=0.6)
    st.pyplot(fig2)

    fig3, ax3 = plt.subplots()
    ax3.plot(df_sel.index, df_sel["diff_percentuale"] * 100, marker="o", color="green")
    st.pyplot(fig3)

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
                                color=df_sel["outlier_ml"].map({-1: "Outlier", 1: "Normale"}),
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
        Paragraph(f"Record totali analizzati: {len(df_sel)}", styles["Normal"]),
        Paragraph(f"Deviazione standard diff%: {dev_std:.2f}%", styles["Normal"]),
        Paragraph(f"Record esclusi manualmente: {len(da_escludere)}", styles["Normal"]),
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
