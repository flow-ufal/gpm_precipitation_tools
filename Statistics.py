import pandas as pd
import geopandas as gpd
from shapely import Point


def compatibility_coords(filename_xlsx, encoding, filename, crs):
    """
    Export the dataframe containing gauges in a compatible format with GIS software.
    
        Parameters:
            filename_xlsx (string): Filename containing gauges in xlsx format
            encoding (string): Enconding used to read the file
            filename (string): Name of the file to be exported
            crs (string): CRS of the file to be exported
        
        Returns:
            gauges_geo (GeoDataFrame): File in a compatible format with SIG software
    """
    # Read gauges
    gauges = gpd.read_file(filename_xlsx, encoding=encoding)

    # Put latitude and longitude data in a compatible format
    lati = []
    long = []

    for row in gauges.itertuples(index=False, name=None):
        lat = float(row[2].replace(',', '.'))
        lon = float(row[3].replace(',', '.'))
        lati.append(lat)
        long.append(lon)

    gauges['Latitude'] = lati
    gauges['Longitude'] = long

    geometry = [Point(xy) for xy in zip(gauges['Longitude'], gauges['Latitude'])]
    gauges_geo = gpd.GeoDataFrame(gauges, geometry=geometry)

    # Export GeoDataFrame into shapefile
    return gauges_geo.to_file(filename=filename, crs=crs)


def annual_accum(filename):
    """
    Returns annual accumulated rainfall.

        Parameters:
            filename (string): Full filename of file

        Returns:
            annual_accum_f (DataFrame): DataFrame with annual accumulated rainfall
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    annual_accum_r = data['Precipitação'].resample('YE').sum()
    annual_accum_r.index = annual_accum_r.index.year
    annual_accum_r.index.name = 'Ano'
    annual_accum_f = annual_accum_r.loc[annual_accum_r.index >= 2000]

    return annual_accum_f


def month_mean(filename):
    """
    Returns monthly mean rainfall.

        Parameters:
            filename (string): Full filename of file

        Returns:
            annual_accum_f (DataFrame): DataFrame with monthly mean rainfall
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    month_mean_r = data.resample('ME').sum()
    month_mean_l = month_mean_r.loc[month_mean_r.index.year >= 2000]
    month_mean_f = month_mean_l.groupby(month_mean_l.index.month).mean()

    return month_mean_f
