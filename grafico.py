
import matplotlib.pyplot as plt

velocita = list(range(1, 11))
claudia = [0.69, 0.73, 0.82, 0.73, 1.27, 1.21, 1.55, 1.92, 2.57, 2.00]
filippo = [0.60, 0.83, 0.89, 1.52, 1.38, 2.02, 2.17, 1.62, 2.35, 1.97]
vuoto = [0.40, 0.58, 0.91, 1.04, 0.89, 1.50, 1.51, 1.94, 2.15, 2.12]

plt.figure(figsize=(10, 6))
plt.plot(velocita, claudia, marker='o', label="Claudia")
plt.plot(velocita, filippo, marker='o', label="Filippo")
plt.plot(velocita, vuoto, marker='--', color='gray', label="Sistema Vuoto")
plt.title("Risposta Vibrazionale Segmentale (Claudia vs Filippo vs Vuoto)")
plt.xlabel("Velocità della macchina")
plt.ylabel("Valore risposta (arbitraria)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
