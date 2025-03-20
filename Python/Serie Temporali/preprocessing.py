import pandas as pd

# Prima parte: Carica e processa il file 'AEP_hourly.csv'

# 1. Carica il CSV
df = pd.read_csv('../Datasets/Hourly_Energy_Consuption/AEP_hourly.csv')

# 2. Verifica le prime righe per controllare il formato delle date
print("Prime righe della colonna 'Date' nel file 'AEP_hourly.csv':")
print(df['Date'].head())  # Stampa le prime righe della colonna 'Date'
print(df['Date'].unique())  # Stampa le date uniche nella colonna 'Date'

# 3. Assicuriamoci che la colonna 'Date' sia nel formato corretto
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

# 4. Verifica che la conversione in datetime sia avvenuta correttamente
print("Tipo della colonna 'Date' dopo la conversione:")
print(df['Date'].dtype)  # Controlla il tipo della colonna Datetime
print(df['Date'].head())  # Stampa le prime righe per verificare il risultato

# 5. Estraiamo solo l'anno e il mese (senza giorno)
df['Date'] = df['Date'].dt.date

# 6. Raggruppiamo per giorno e calcoliamo la media di 'AEP_MW'
daily_avg = df.groupby('Date')['AEP_MW'].mean().reset_index()

# 7. Stampa il risultato
print("Media giornaliera di AEP_MW:")
print(daily_avg)

# Salviamo il DataFrame 'daily_avg' in un nuovo file CSV
daily_avg.to_csv('daily.csv', index=False)

print("Il file 'daily.csv' è stato creato con successo.")

# Seconda parte: Carica e processa il file 'daily.csv' per resample settimanale

# 1. Leggiamo il CSV
df_daily = pd.read_csv('daily.csv')

# 2. Convertiamo la colonna 'Date' in formato datetime
df_daily['Date'] = pd.to_datetime(df_daily['Date'], format='%Y-%m-%d', errors='coerce')

# 3. Impostiamo 'Date' come indice
df_daily.set_index('Date', inplace=True)

# 4. Eseguiamo un resample settimanale (calcolando la media di 'AEP_MW')
df_weekly = df_daily.resample('W')['AEP_MW'].mean().reset_index()

# 5. Visualizziamo le prime righe del DataFrame settimanale
print("Media settimanale di AEP_MW:")
print(df_weekly.head())

# 6. (Opzionale) Salviamo il DataFrame settimanale in un nuovo file CSV
df_weekly.to_csv('weekly.csv', index=False)

print("Il file 'weekly.csv' è stato creato con successo.")
