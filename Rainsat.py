from mergedownloader.inpeparser import INPEParsers, INPETypes
from mergedownloader.downloader import Downloader
from shapely import Point
import geopandas as gpd
import pandas as pd
import xarray as xr
import logging
import glob


class Gpm:
    def __init__(self, download_folder, start, end):
        """
        Create instance of class Gpm

        download_folder: Folder to download rain files
        start: start period of rain
        end: end period of rain
        """
        self.download_folder = download_folder
        self.start = start
        self.end = end

    def download_data(self):
        """
        Download the grib2 daily data with rainfall values in the download_folder

        return: cube (longitude, latitude, rainfall) of data
        """

        downloader = Downloader(
            server=INPEParsers.FTPurl,
            parsers=INPEParsers.parsers,
            local_folder=self.download_folder
        )
        cube = downloader.create_cube(
            start_date=self.start,
            end_date=self.end,
            datatype=INPETypes.DAILY_RAIN
        )

        print("Download completed successfully!")
        return cube

    def to_pandas(self, engine):
        """
        Create dataframe with precipitation values

        engine: Engine to use when reading files

        returns: DataFrame with rainfall across Brazil
        """
        filename = glob.glob(f"{self.download_folder}/DAILY_RAIN/*.grib2")

        final_df = pd.DataFrame()

        # Set the logging to cfgrib
        logging.getLogger("cfgrib").setLevel(logging.ERROR)

        for file in filename:
            ds = xr.open_dataset(file, engine=engine)
            ds = ds.get("prec")
            df = ds.to_dataframe()
            final_df = pd.concat([final_df, df])

        return final_df


def convert_longitude(dataframe):
    """
    Convert range of longitude values for default CRS

    dataframe: Pandas Dataframe with rainfall values

    Returns: Pandas Dataframe with converted longitudes
    """
    latitudes = dataframe.index.get_level_values('latitude')
    longitudes = dataframe.index.get_level_values("longitude")
    remapped_longitudes = []

    for lon in longitudes:
        if lon > 180:
            lon = lon - 360
            remapped_longitudes.append(lon)
        else:
            remapped_longitudes.append(lon)

    dataframe["latitude"] = latitudes
    dataframe["longitude"] = remapped_longitudes
    dataframe = dataframe.reset_index(drop=True)

    return dataframe


def local_filter(dataframe, mask_layer, crs_reprojected, crs_geographic):
    """
    Clip the data from the mask layer

    dataframe: DataFrame to be clipped
    mask_layer: mask layer
    crs_reprojected: CRS in UTM
    crs_geographic: CRS in lat/long system

    Returns: clipped DataFrame for region of interest
    """
    gdf_shp = gpd.read_file(filename=mask_layer)
    s = gpd.GeoSeries(data=gdf_shp.geometry)
    s_reprojected = s.to_crs(crs=crs_reprojected)
    s_buffered = s_reprojected.buffer(distance=15000)
    s_geographic = s_buffered.to_crs(crs=crs_geographic)

    geometry = [Point(coords) for coords in zip(dataframe["longitude"], dataframe["latitude"])]
    gdf_rain = gpd.GeoDataFrame(data=dataframe, geometry=geometry)

    gdf_rain.set_crs(crs_geographic, inplace=True)
    rain_clipped = gpd.clip(gdf=gdf_rain, mask=s_geographic)
    rain_clipped.reset_index(drop=True, inplace=True)

    return rain_clipped


def create_id(dataframe):
    """
    Create an ID column for dataframe. The same geometry has same ID and otherwise

    dataframe: The DataFrame from which the ID column is created

    Returns: DataFrame with ID column
    """
    dataframe.loc[:, "ID"] = -99

    geom_unique = list(set(dataframe.geometry.values))

    for row in range(len(dataframe)):
        for i in range(len(geom_unique)):
            if geom_unique[i] == dataframe.iloc[row]["geometry"]:
                dataframe.loc[row, "ID"] = i

    return dataframe
