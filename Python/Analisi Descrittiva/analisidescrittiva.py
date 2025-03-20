import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd

# Caricamento del file Excel
file_path = '../energy_prod_def.xlsx'  # Sostituisci con il percorso del tuo file
data = pd.read_excel(file_path)

# 1. Grafico a barre impilate per le energie rinnovabili (per "World")
country_data = data[data['country'] == 'World']
plt.figure(figsize=(10, 6))
plt.bar(country_data['year'], country_data['solar_share_energy'], label='Solar Share')
plt.bar(country_data['year'], country_data['wind_share_energy'], bottom=country_data['solar_share_energy'], label='Wind Share')
plt.bar(country_data['year'], country_data['hydro_share_energy'], bottom=country_data['solar_share_energy'] + country_data['wind_share_energy'], label='Hydro Share')
plt.title('Renewable Energy Share in Total Energy Consumption for World')
plt.xlabel('Year')
plt.ylabel('Share of Renewable Energy')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
plt.grid(True)
plt.show()

# 2. Confronto tra Fonti Fossili e Rinnovabili nella Generazione di Elettricità (Top 10 Paesi)
top_electricity = data[['country', 'electricity_generation', 'fossil_share_elec', 'renewables_share_elec']].dropna()
top_electricity = top_electricity[top_electricity['country'] != 'World']  # Escludi "World"
top_electricity = top_electricity.groupby('country').mean().sort_values(by='electricity_generation', ascending=False).head(10)
plt.figure(figsize=(12, 8))
top_electricity[['fossil_share_elec', 'renewables_share_elec']].plot(kind='bar', stacked=True, alpha=0.8, color=['#d62728', '#2ca02c'])
plt.title('Confronto tra Fonti Fossili e Rinnovabili nella Generazione di Elettricità (Top 10 Paesi)')
plt.xlabel('Paese')
plt.ylabel('Quota (%)')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y')
plt.legend(['Fonti Fossili', 'Fonti Rinnovabili'])
plt.show()

# 3. Grafico a linee per ogni fonte di energia (per "World")
plt.figure(figsize=(10, 6))
plt.plot(country_data['year'], country_data['coal_consumption'], label='Coal Consumption')
plt.plot(country_data['year'], country_data['gas_consumption'], label='Gas Consumption')
plt.plot(country_data['year'], country_data['hydro_consumption'], label='Hydro Consumption')
plt.plot(country_data['year'], country_data['nuclear_consumption'], label='Nuclear Consumption')
plt.plot(country_data['year'], country_data['oil_consumption'], label='Oil Consumption')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
plt.title('Energy Consumption by Source for World')
plt.xlabel('Year')
plt.ylabel('Energy Consumption (TWh)')
plt.grid(True)
plt.show()

# 4. Top 5 Paesi per Consumo di Biofuel (grafico a torta)
biofuel_top5 = data[['country', 'biofuel_share_elec']].dropna()
biofuel_top5 = biofuel_top5[~biofuel_top5['country'].isin(['World', 'Asia'])]  # Escludi "World" e "Asia"
biofuel_top5 = biofuel_top5.groupby('country').sum().sort_values(by='biofuel_share_elec', ascending=False).head(5)
biofuel_top5['percentage'] = (biofuel_top5['biofuel_share_elec'] / biofuel_top5['biofuel_share_elec'].sum()) * 100
plt.figure(figsize=(10, 6))
plt.pie(biofuel_top5['percentage'], labels=biofuel_top5.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
plt.title('Top 5 Paesi per Consumo di Biofuel (%)')
plt.show()

# 5. Mappa di Calore del fattore di emissione
shapefile_path = 'C:/Users/marco/Desktop/codici/data science/progetto 1/analisi descrittiva/countries/ne_110m_admin_0_countries.shp'
gdf_world = gpd.read_file(shapefile_path)

data_grouped = data.groupby('country')['emission_factor'].mean().reset_index()
gdf_world = gdf_world.merge(data_grouped, left_on='ADMIN', right_on='country', how='left')

fig, ax = plt.subplots(figsize=(12, 8))
gdf_world.plot(column='emission_factor', cmap='YlOrRd', ax=ax, legend=True, edgecolor='black')

ax.set_xlabel('Longitudine')
ax.set_ylabel('Latitudine')

legend = ax.get_legend()
if legend:
    legend.set_bbox_to_anchor((1, 0.3))
    legend.set_orientation('horizontal')

plt.show()

# 6. Mappa di Calore della Domanda di Elettricità per Paese (Media 2000-2022)
shapefile_path = 'C:/Users/marco/Desktop/codici/data science/progetto 1/analisi descrittiva/countries/ne_110m_admin_0_countries.shp'
gdf_world = gpd.read_file(shapefile_path)

data_grouped = data.groupby('country')['electricity_demand'].mean().reset_index()
gdf_world = gdf_world.merge(data_grouped, left_on='ADMIN', right_on='country', how='left')

fig, ax = plt.subplots(figsize=(12, 8))
gdf_world.plot(column='electricity_demand', cmap='YlOrRd', ax=ax, legend=True, edgecolor='black')

ax.set_xlabel('Longitudine')
ax.set_ylabel('Latitudine')

legend = ax.get_legend()
if legend:
    legend.set_bbox_to_anchor((1, 0.3))
    legend.set_orientation('horizontal')

plt.show()
