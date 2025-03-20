import pandas as pd
import numpy as np

# Carica i dataset
df1 = pd.read_excel('../Datasets/owid-energy-data.xlsx')
df2 = pd.read_excel('../Datasets/enerdata_energy_statistical_yearbook_2023-.xlsx', sheet_name='Average CO2 emission factor')

# Filtra i dati in base ai paesi presenti nel secondo dataset
df1_filtered = df1[df1['country'].isin(df2['Unnamed: 1'])]

# Filtra gli anni tra 1990 e 2022
df1_filtered = df1_filtered[(df1_filtered['year'] >= 1990) & (df1_filtered['year'] <= 2022)]

# Riorganizza df2: le colonne da 'Unnamed: 2' in poi rappresentano gli anni
df2 = df2.loc[:, 'Unnamed: 1':'Unnamed: 34']
df2_long = df2.set_index('Unnamed: 1')
df2_long.columns = range(1990, 1990 + len(df2.columns) - 1)
df2_long = df2_long.reset_index().melt(id_vars='Unnamed: 1', var_name='year', value_name='emission_factor')
df2_long.rename(columns={'Unnamed: 1': 'country'}, inplace=True)
df2_long['year'] = df2_long['year'].astype(int)

# Merge dei dataset in base a 'country' e 'year'
df1_merged = df1_filtered.merge(df2_long, how='left', on=['country', 'year'])

# Sposta la colonna 'emission_factor' dopo 'gdp' se presente
if 'gdp' in df1_merged.columns:
    col_order = df1_merged.columns.tolist()
    gdp_index = col_order.index('gdp')
    col_order.insert(gdp_index + 1, col_order.pop(-1))  # Sposta l'ultima colonna (emission_factor) dopo 'gdp'
    df1_merged = df1_merged[col_order]

# Salva il dataset filtrato e unito
df1_merged.to_excel('energy_prod_def.xlsx', index=False)

# Ricarica il dataset modificato
df = pd.read_excel('energy_prod_def.xlsx')

# Visualizza un'anteprima
df_preview = df.iloc[:5, :10]
print(df_preview)

# Info sulle dimensioni del dataset
num_rows, num_cols = df.shape
print(f"Il dataset contiene {num_rows} righe e {num_cols} colonne.")

# Conta i valori nulli e li sostituisce con 0
df.fillna(0, inplace=True)
print("Valori nulli per colonna:")
print(df.isnull().sum())

# Conta le celle con valore 0 per colonna
zeros_per_column = df.apply(lambda col: (col == 0).sum())
print("Celle con valore 0 per colonna:")
print(zeros_per_column)

# Filtra gli anni tra 2000 e 2022
df = df[(df['year'] >= 2000) & (df['year'] <= 2022)]

# Rimuove la colonna 'iso_code' se presente
if 'iso_code' in df.columns:
    df.drop(columns=['iso_code'], inplace=True)

# Salva il dataset finale
df.to_excel('energy_prod_def.xlsx', index=False)
