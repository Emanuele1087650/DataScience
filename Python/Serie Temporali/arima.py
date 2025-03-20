import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from statsmodels.tsa.arima.model import ARIMA  # oppure SARIMAX
from sklearn.metrics import mean_absolute_error, r2_score  # per MAE, R^2

# 1. Lettura dataset
df = pd.read_csv("weekly.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)

# Se i dati sono orari e vuoi media giornaliera (opzionale):
# df = df["AEP_MW"].resample("D").mean().dropna()

# 2. Estrai la colonna e rimuovi NaN
forNo = df["AEP_MW"].dropna()

# 3. Split 80% training, 20% test
nobs = len(forNo)
n_init_training = int(nobs * 0.8)

init_training_forNo = forNo[:n_init_training]
test_forNo = forNo[n_init_training:]

# 4. Definizione modello ARIMA con stagionalità settimanale: (p,d,q)x(P,D,Q,m)
model = ARIMA(
    init_training_forNo,
    order=(2,0,1),
    seasonal_order=(2,0,0,52)  
)

# 5. Fit sul training set
results_80 = model.fit()

# -------------------------------------------------------------------------
# GRAFICO 1: Confronto Training vs Fitted Values + Test Set
# -------------------------------------------------------------------------
fig = plt.figure(figsize=(20, 8))
ax = plt.gca()

# Training set
plt.plot(forNo[:n_init_training], color='limegreen', label='Training Set')

# Test set
plt.plot(forNo[n_init_training-1:], color='deepskyblue', label='Test Set')

# Fitted values (sul training)
plt.plot(results_80.fittedvalues, color='hotpink', label='Fitted (Training)')

ax.legend()
plt.title("Modello ARIMA con Stagionalità - Training & Test")
plt.xlabel("Data")
plt.ylabel("AEP_MW")
plt.show()

# Stampa sommario del modello
print(results_80.summary())

# -------------------------------------------------------------------------
# GRAFICO 2 + PREVISIONE SUL TEST SET
# -------------------------------------------------------------------------
fig = plt.figure(figsize=(20, 8))
ax = plt.gca()

# Previsione dal training set per l'intervallo del test
pred_frame = results_80.get_prediction(
    start=test_forNo.index[0],
    end=test_forNo.index[-1]
).summary_frame()  # summary_frame() ti dà anche gli intervalli di confidenza

# Plot di un subset di training (solo se vuoi zoomare un po' l'ultimo periodo)
plt.plot(init_training_forNo[-300:], color='limegreen', label='Training (zoom)')

# Plot test set (valori reali)
plt.plot(test_forNo, color='deepskyblue', label='Test Set')

# Previsione (media)
plt.plot(pred_frame['mean'], color='hotpink', label='Forecast')

# Intervalli di confidenza
plt.fill_between(
    pred_frame.index,
    pred_frame['mean_ci_lower'],
    pred_frame['mean_ci_upper'],
    color='hotpink',
    alpha=0.3
)

plt.legend()
plt.title("Forecast ARIMA con Stagionalità - Confronto con Test")
plt.xlabel("Data")
plt.ylabel("AEP_MW")
plt.show()

# -------------------------------------------------------------------------
# CALCOLO METRICHE DI VALUTAZIONE (MAPE, MAE, R^2, RSE) SUL TEST
# -------------------------------------------------------------------------
y_true = test_forNo
y_pred = pred_frame['mean']  # medie previste dal modello

# 1. MAE (Mean Absolute Error)
mae = mean_absolute_error(y_true, y_pred)

# 2. MAPE (Mean Absolute Percentage Error)
#    Attenzione se y_true può contenere valori zero o molto bassi
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

# 3. R² (coefficiente di determinazione)
r2 = r2_score(y_true, y_pred)

# 4. RSE (Residual Standard Error)
#    RSE = sqrt( SSE / (n - k) ), come stima semplificata usiamo (n - 1).
residuals = y_true - y_pred
SSE = np.sum(residuals**2)
n = len(y_true)
RSE = np.sqrt(SSE / (n - 1))

print("\n===== METRICHE SUL TEST SET =====")
print(f"MAE  = {mae:.2f}")
print(f"MAPE = {mape:.2f}%")
print(f"R^2  = {r2:.3f}")
print(f"RSE  = {RSE:.2f}")
