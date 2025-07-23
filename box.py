import pandas as pd
import matplotlib.pyplot as plt
import os

# 📂 Cartella di esportazione
os.makedirs("output_surface_outliers", exist_ok=True)

# 📥 Caricamento CSV
df = pd.read_csv('dati.csv', sep=';')
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
df['manubrio'] = pd.to_numeric(df['manubrio'], errors='coerce')

# ✨ Superfici da analizzare
superfici = ['asfalto', 'sterrato', 'mattonellato']  # Puoi aggiungere altre

# 🎯 Analisi per ciascuna superficie
for superficie in superfici:
    subset = df[df['superficie'].str.strip().str.lower() == superficie]
    if subset.empty:
        print(f"⚠️ Nessun dato per superficie '{superficie}'")
        continue

    Q1 = subset['manubrio'].quantile(0.25)
    Q3 = subset['manubrio'].quantile(0.75)
    IQR = Q3 - Q1
    low = Q1 - 1.5 * IQR
    high = Q3 + 1.5 * IQR

    subset['outlier'] = 'normale'
    subset.loc[subset['manubrio'] < low, 'outlier'] = 'basso'
    subset.loc[subset['manubrio'] > high, 'outlier'] = 'alto'

    outliers = subset[subset['outlier'] != 'normale']
    print(f"\n🌍 {superficie.upper()} → outlier trovati: {len(outliers)}")

    # 📤 Esporta in Excel
    file_excel = f"output_surface_outliers/outlier_{superficie}.xlsx"
    with pd.ExcelWriter(file_excel) as writer:
        subset.to_excel(writer, sheet_name="Tutti i dati", index=False)
        outliers.to_excel(writer, sheet_name="Solo outlier", index=False)

    # 📊 Boxplot visuale
    plt.figure(figsize=(8, 4))
    plt.boxplot(subset['manubrio'].dropna(), vert=False)
    plt.title(f"Boxplot Manubrio - Superficie: {superficie}")
    plt.xlabel("Valore Manubrio")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"output_surface_outliers/boxplot_{superficie}.png")
    plt.close()

