import geopandas as gpd
from shapely import Point
import pandas as pd

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

    return annual_accum

# Example
# delmiro = "D:\PIBIC 23-24\Estacoes\Estacoes_SIGA\DELMIRO GOUVÉIA.xlsx"
# aa_delmiro = annual_accum(delmiro)

def month_accum(filename):
    """
    Returns monthly accumulated rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    month_accum = data['Precipitação'].resample('M').sum()
    month_accum.index = month_accum.index.strftime('%Y-%m')

    return month_accum

# Example
# delmiro = "D:\PIBIC 23-24\Estacoes\Estacoes_SIGA\DELMIRO GOUVÉIA.xlsx"
# ma_delmiro = month_accum(delmiro)

def annual_mean(filename):
    """
    Returns annual mean rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    annual_mean = data['Precipitação'].resample('Y').mean()
    annual_mean.index = annual_mean.index.year

    return annual_mean

# Example
# delmiro = "D:\PIBIC 23-24\Estacoes\Estacoes_SIGA\DELMIRO GOUVÉIA.xlsx"
# am_delmiro = annual_mean(delmiro)

def month_mean(filename):
    """
    Returns monthly mean rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    month_mean = data['Precipitação'].resample('M').mean()
    month_mean.index = month_mean.index.strftime('%Y-%m')

    return month_mean

# Example
# delmiro = "D:\PIBIC 23-24\Estacoes\Estacoes_SIGA\DELMIRO GOUVÉIA.xlsx"
# mm_delmiro = month_mean(delmiro)
