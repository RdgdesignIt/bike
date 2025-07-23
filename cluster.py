import pandas as pd
df = pd.read_csv('all_superficie.csv')
df.dropna(inplace=True)  # rimuove righe con valori mancanti
