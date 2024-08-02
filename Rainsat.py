from mergedownloader.inpeparser import INPEParsers, INPETypes
from mergedownloader.downloader import Downloader
from shapely import Point
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

    @staticmethod
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


# TEMPORARY EXAMPLES
# Create object
_data = Gpm('D:/Pesquisa/PIBIC_23-24/Dados_GPM/Test', '2022-01-01', '2022-01-31')

# Download the data in local machine
_data.download_data()

# Converts data into a DataFrame
_df = _data.to_pandas(engine="cfgrib")

# Remapped Longitudes
_df_formatted = _data.convert_longitude(_df)
# -----------------------------------------------------------------------------------------------------------#


def local_filter(shapefile, epsg):
    """
    Filter rainfall data for region of interest

    shapefile: Shapefile of the region of interest
    epsg: epsg of the region in geographic coordinates

    Returns: DataFrame with rainfall data in region of interest
    """
    return None
