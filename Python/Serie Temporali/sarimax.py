import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error

# 1. Lettura e preparazione dei dati
df = pd.read_csv('weekly.csv', parse_dates=['Date'])

# Assicuriamoci che i dati siano ordinati in base alla colonna Datetime
df = df.sort_values(by='Date')

# Se vuoi, imposta 'Datetime' come indice (fortemente consigliato per modelli di serie temporali)
df.set_index('Date', inplace=True)

# Rimuovi eventuali valori NaN nella colonna che ti interessa (ad es. 'AEP_MW')
df.dropna(subset=['AEP_MW'], inplace=True)

# 2. Divisione in training (80%) e test (20%)
serie = df['AEP_MW']
nobs = len(serie)
n_init_training = int(nobs * 0.8)  # 80%

train = serie.iloc[:n_init_training]
test = serie.iloc[n_init_training:]

print("Dimensione serie totale:", nobs)
print("Dimensione training set:", len(train))
print("Dimensione test set:", len(test))

# 3. Creazione e fitting del modello SARIMAX (6,3,4)(2,1,2,12)
model = SARIMAX(
    train,
    order=(2,1,1),
    seasonal_order=(1,1,1,52),
    enforce_stationarity=False,
    enforce_invertibility=False
)

results_80 = model.fit()
print(results_80.summary())

# 4. Previsione sul periodo di test
forecast_steps = len(test)
predictions = results_80.forecast(steps=forecast_steps)

# 5. Calcolo delle metriche di errore
rmse = np.sqrt(mean_squared_error(test, predictions))
mae = mean_absolute_error(test, predictions)

# MAPE (Mean Absolute Percentage Error) definita come media di (abs(errore relativo))*100
def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

mape = mean_absolute_percentage_error(test, predictions)

# 6. Calcolo di R² (R-quadrato)
ss_residual = np.sum((test - predictions) ** 2)  # Somma dei residui al quadrato
ss_total = np.sum((test - np.mean(test)) ** 2)  # Somma totale dei quadrati
r2 = 1 - (ss_residual / ss_total)

print("\nValutazione del modello SARIMAX(2,1,1)(1,1,1,52)")
print(f"RMSE:  {rmse:.2f}")
print(f"MAE:   {mae:.2f}")
print(f"MAPE:  {mape:.2f}%")
print(f"R²:    {r2:.4f}")

# 7. Grafico di confronto
plt.figure(figsize=(12,6))
plt.plot(train, label='Training (80%)', color='limegreen')
plt.plot(test, label='Test (20%)', color='deepskyblue')
plt.plot(predictions, label='Previsione SARIMAX', color='red', linestyle='--')
plt.title('Confronto Training, Test e Previsione - SARIMAX(2,1,1)(1,1,1,52)')
plt.legend()
plt.show()
