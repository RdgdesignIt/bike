from sklearn.ensemble import IsolationForest

features = df_sel[["manubrio", "sellino", "diff_percentuale"]]
model = IsolationForest(contamination=0.05)
df_sel["outlier_multi"] = model.fit_predict(features)
