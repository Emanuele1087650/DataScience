import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

# 1. Carica il file CSV e converte la colonna 'Date' in formato data
df = pd.read_csv('weekly.csv', parse_dates=['Date'])

# 2. Imposta la colonna 'Date' come indice
df.set_index('Date', inplace=True)

# 3. Traccia il grafico dell'andamento di AEP_MW nel tempo
plt.figure(figsize=(10, 5))
plt.plot(df.index, df['AEP_MW'], label='AEP_MW')
plt.title('Andamento AEP_MW nel tempo')
plt.xlabel('Data')
plt.ylabel('AEP_MW')
plt.legend()
plt.grid(True)
plt.show()

# 4. Rimuovi eventuali NaN nella colonna AEP_MW
df.dropna(subset=['AEP_MW'], inplace=True)

# 5. Calcola l'Augmented Dickey-Fuller test
#    L'opzione autolag='AIC' fa scegliere automaticamente il numero di lag sulla base del criterio AIC
result = adfuller(df['AEP_MW'], autolag='AIC')

# 6. Estrai i risultati
adf_stat = result[0]     # ADF statistic
p_value = result[1]      # p-value
crit_values = result[4]  # Valori critici (1%, 5%, 10%)

print("=== Augmented Dickey-Fuller Test ===")
print(f"ADF statistic: {adf_stat}")
print(f"p-value: {p_value}")
print("Critical values:")
for key, val in crit_values.items():
    print(f"   {key}: {val}")

# 7. Interpretazione semplice (usando una soglia di significatività al 5%)
if p_value < 0.05:
    print("\nLa serie è probabilmente stazionaria (p-value < 0.05).")
else:
    print("\nLa serie NON è stazionaria (p-value >= 0.05).")

# 8. (Opzionale) Se i dati sono orari e vuoi ottenere una serie giornaliera media
df_daily = df['AEP_MW'].resample('D').mean().dropna()

# 9. Esegui la differenza sulla serie per renderla più vicina a uno stato stazionario
serie_diff = df_daily.diff().dropna()

# 10. Creazione dei grafici ACF e PACF fianco a fianco
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ACF
sm.graphics.tsa.plot_acf(
    serie_diff,
    lags=20,
    alpha=0.05,   # Bande di confidenza al 95%
    ax=axes[0]
)
axes[0].set_title("Autocorrelazione (ACF)")

# PACF
sm.graphics.tsa.plot_pacf(
    serie_diff,
    lags=20,
    method="ywm",  # Yule-Walker modificato (opzionale, puoi scegliere anche altri metodi)
    alpha=0.05,    # Bande di confidenza al 95%
    ax=axes[1]
)
axes[1].set_title("Autocorrelazione Parziale (PACF)")

plt.tight_layout()
plt.show()
