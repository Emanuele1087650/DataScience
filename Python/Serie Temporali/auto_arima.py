import pandas as pd
from pmdarima import auto_arima
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

# ==========================
# 1. CARICAMENTO DEL DATASSET
# ==========================
# Sostituisci 'daily_average236.csv' con il tuo file
# e 'AEP_MW' con la tua colonna che contiene la serie temporale.
data = pd.read_csv('weekly.csv')

# Se hai una colonna di date, assicurati di convertirla in datetime e impostarla come indice:
# data['Data'] = pd.to_datetime(data['Data'])
# data.set_index('Data', inplace=True)

serie_temporale = data['AEP_MW']

# ==========================
# 2. DECOMPOSIZIONE STAGIONALE
# ==========================
# Definisci 'period' in base alla frequenza dei tuoi dati:
# - Se hai dati giornalieri con stagionalità settimanale, period = 7
# - Se hai dati mensili con stagionalità annuale, period = 12
# - Se hai dati orari con stagionalità giornaliera, period = 24
# e così via...

period = 52  # Esempio: dati giornalieri con stagionalità settimanale

decomposition = seasonal_decompose(serie_temporale, model='additive', period=period)
fig = decomposition.plot()
fig.set_size_inches(10, 8)
plt.show()

# ==========================
# 3. MODELLAZIONE CON AUTO_ARIMA (STAGIONALE)
# ==========================
# Impostiamo seasonal=True e definiamo m=period, coerente con la decomposizione.
# Attiva trace=True per monitorare i tentativi di auto_arima.

model = auto_arima(
    serie_temporale,
    start_p=1, start_q=1,
    max_p=7, max_q=7,
    seasonal=True,
    m=period,              # Periodo di stagionalità
    start_P=1, start_Q=1,
    max_P=7, max_Q=7,
    trace=True,
    error_action='ignore',  # ignora gli errori per valori non validi
    suppress_warnings=True,
    stepwise=True           # se True, procede passo-passo riducendo il tempo di calcolo
)

# ==========================
# 4. RISULTATI DEL MODELLO
# ==========================
print("Miglior modello (ordine ARIMA): ", model.order)
print("Miglior modello (ordine stagionale): ", model.seasonal_order)
print("AIC del modello scelto:", model.aic())

# ==========================
# 5. DIAGNOSTICA DEL MODELLO
# ==========================
# Visualizza grafici utili per diagnosticare il fitting del modello
model.plot_diagnostics(figsize=(10, 6))
plt.show()
