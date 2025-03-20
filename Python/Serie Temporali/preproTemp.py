import pandas as pd

# Carica il CSV
df = pd.read_csv('../Datasets/Hourly_Energy_Consuption/AEP_hourly.csv')

# 1. Verifica le prime righe per controllare il formato delle date
print(df['Date'].head())  # Stampa le prime righe della colonna 'Date'
print(df['Date'].unique())  # Stampa le date uniche nella colonna 'Date'

# 2. Assicuriamoci che la colonna 'Datetime' sia nel formato corretto
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

# 3. Verifica che la conversione in datetime sia avvenuta correttamente
print(df['Date'].dtype)  # Controlla il tipo della colonna Datetime
print(df['Date'].head())  # Stampa le prime righe per verificare il risultato

# 4. Estraiamo solo l'anno e il mese (senza giorno)
df['Date'] = df['Date'].dt.date

# 5. Raggruppiamo per mese e calcoliamo la media
daily_avg = df.groupby('Date')['AEP_MW'].mean().reset_index()

# 6. Stampa il risultato
print(daily_avg)

# Salviamo il DataFrame monthly_avg in un nuovo file CSV
daily_avg.to_csv('daily.csv', index=False)

print("Il file CSV è stato creato con successo.")
