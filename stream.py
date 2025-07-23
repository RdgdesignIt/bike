import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

# 📥 Dati simulati (da integrare con i tuoi dataset reali)
df = pd.read_csv("dati.csv", sep=";")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df = df.rename(columns={"superfice": "superficie"})
df['diff_percentuale'] = pd.to_numeric(df['diff_percentuale'], errors='coerce')

# 👉 Personalizza questi valori con quelli reali dalla dashboard
superficie = "asfalto"
soglia_z = 2.5
iqr_coef = 1.5
contamination = 0.05

# 📊 Conteggio outlier simulato
n_z = 12
n_iqr = 8
n_ml = 15
dev_std = df[df["superficie"] == superficie]["diff_percentuale"].std() * 100

# 🩺 Riepilogo PDF
doc = SimpleDocTemplate("report_diagnostico_vibrazioni.pdf", pagesize=A4)
elements = []
styles = getSampleStyleSheet()

elements.append(Paragraph("📋 Report Diagnostico Vibrazioni", styles["Title"]))
elements.append(Spacer(1, 12))
elements.append(Paragraph(f"<b>Superficie analizzata:</b> {superficie.capitalize()}", styles["Normal"]))
elements.append(Paragraph(f"<b>Soglia Z-score ±</b>: {soglia_z}", styles["Normal"]))
elements.append(Paragraph(f"<b>Coefficiente IQR</b>: {iqr_coef}", styles["Normal"]))
elements.append(Paragraph(f"<b>Contamination ML (%)</b>: {contamination:.2%}", styles["Normal"]))
elements.append(Spacer(1, 12))

# 📊 Tabella metodi
table_data = [
    ["Metodo", "Outlier rilevati"],
    ["Z-score", n_z],
    ["IQR", n_iqr],
    ["Isolation Forest", n_ml]
]
table = Table(table_data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
    ('GRID', (0,0), (-1,-1), 1, colors.black),
    ('ALIGN', (0,0), (-1,-1), 'CENTER')
]))
elements.append(Paragraph("📊 Conteggio Outlier", styles["Heading2"]))
elements.append(table)
elements.append(Spacer(1, 12))

# 📈 Stato vibrazioni
elements.append(Paragraph("📈 Differenza Percentuale:", styles["Heading2"]))
elements.append(Paragraph(f"Deviazione standard: {dev_std:.2f}%", styles["Normal"]))
elements.append(Paragraph("Stato: " + ("🟢 Costante" if dev_std < 1 else "🔴 Variabile"), styles["Normal"]))
elements.append(Spacer(1, 12))

# 📉 Grafici salvati in cartella (da codice precedente)
for grafico in [
    "boxplot_manubrio.png",
    "scatter_manubrio_sellino.png",
    "zscore_scatter.png",
    "iqr_scatter.png",
    "ml_scatter.png",
    "differenza_percentuale.png"
]:
    path = os.path.join("grafici_export", grafico)
    if os.path.exists(path):
        elements.append(Image(path, width=400, height=250))
        elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph(f"⚠️ Immagine mancante: {grafico}", styles["Normal"]))

doc.build(elements)
print("✅ PDF generato: report_diagnostico_vibrazioni.pdf")
