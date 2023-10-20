import pandas as pd
import geopandas as gpd
from shapely import Point
import matplotlib.pyplot as plt

def compatibility_Coords(filepath, encoding, filename, crs):
    """
    Export the dataframe containing gauges in a compatible format with SIG softwares.
    
        Parameters:
            filepath (string): Filepath containing gauges
            encoding (string): Enconding used to read the file
            filename (string): Name of the file to be exported
            crs (string): CRS of the file to be exported
        
        Returns:
            gauges_geo (GeoDataFrame): File in a compatible format with SIG softwares
    """
    # Read gauges
    gauges = gpd.read_file(filepath, encoding=encoding)

    # Put latitude and longitude data in a compatible format
    LAT = []
    LON = []

    for row in gauges.itertuples(index=False, name=None):
        lat = float(row[2].replace(',', '.'))
        lon = float(row[3].replace(',', '.'))
        LAT.append(lat)
        LON.append(lon)

    gauges['Latitude'] = LAT
    gauges['Longitude'] = LON

    geometry = [Point(xy) for xy in zip(gauges['Longitude'], gauges['Latitude'])]
    gauges_geo = gpd.GeoDataFrame(gauges, geometry=geometry)

    # Export GeoDataFrame into shapefile
    return gauges_geo.to_file(filename=filename, crs=crs)

# Example
# compatibility_Coords(r"C:\Users\pedro\Downloads\estacoes.csv", 'latin-1', 'teste.shp', 'EPSG:4326')

def annual_accum(filename):
    """
    Returns annual accumulated rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    annual_accum = data['Precipitação'].resample('Y').sum()
    annual_accum.index = annual_accum.index.year
    annual_accum.index.name = 'Ano'

    return annual_accum

# Example
delmiro = "D:\Pesquisa\PIBIC 23-24\Estacoes\Estacoes_SIGA\Filtro_GPM\DELMIRO GOUVÉIA.xlsx"
aa_delmiro = annual_accum(delmiro)

def month_mean(filename):
    """
    Returns monthly mean rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    month_mean = data.resample('M').sum()
    month_mean = month_mean.groupby(month_mean.index.month).mean()

    return month_mean

# Example
mm_delmiro = month_mean(delmiro)

# Plotagem
station = 'Delmiro Gouveia'
n_rows = 1
n_cols = 2
fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols)

aa_delmiro.plot(ax=axes[0], kind='bar', color='blue', edgecolor='black', alpha=0.7)
mm_delmiro.plot(ax=axes[1], kind='bar', legend=False, color='blue', edgecolor='black', alpha=0.7)

axes[0].set_ylabel('Chuva (mm)',  weight='bold')
axes[0].set_xlabel('Ano', weight='bold')
axes[0].set_title('Acumulado Anual', weight='bold')
axes[1].set_ylabel('Chuva (mm)', weight='bold')
axes[1].set_xlabel('Mês', weight='bold')
axes[1].set_title('Acumulado Mensal', weight='bold')

plt.tight_layout()
plt.show()
