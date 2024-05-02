#==================================================================================================
#                                        MÓDULO 03: 

#       - Leitura e tratamento inicial de arquivo hierárquico (.grib2, .nc)
#       - Dada a localização de uma estação de interesse, procura pontos (GPM) próximos
#       - Visualização das estações reais e virtuais na região de interesse
#==================================================================================================

#Importando algumas bibliotecas
import pandas as pd
import geopandas as gpd 
from shapely import Point, geometry
import os
import glob 
import matplotlib.pyplot as plt
import datetime as dt
from operator import itemgetter
import xarray as xr
import geopandas as gpd
import pyproj
import shapely
import numpy as np

def read_file_precipitation_grib(path, temporal_scaling="D"):

    '''  Esta função realiza um tratamento inicial dos dados diários, ajusta as coordenadas
    path: caminho da pasta no qual o arquivo (em formato grib2) está localizado 
    temporal_scaling: informar se estamos com arquivos de dados diários, mensais ou anuais
        Diário: escrever "D",
        Mensal: escrever "M"
        Anual: escrever "Y"'''
    
    #Lendo dado hierárquico
    ds = xr.open_dataset(path)

    #Filtrando variábel de interesse
    if temporal_scaling == 'D':
        df = ds.get('prec').to_dataframe()  #por padrão, arquivos diários, a coluna de precipitaçao vem nomeada com "pre"
        df.reset_index(inplace=True)

    else:
        df = ds.get('pacum').to_dataframe() #em arquivos de acumulado mensal ou anual, a coluna de precipitação é nomeada com "pacum"
        df.reset_index(inplace=True)
        df = df.rename({'lon': 'longitude', 'lat':'latitude'}, axis = 1)

    # Convertendo para dataframe
    df.reset_index(inplace=True)

    #Salvando geometrias
    df = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude-360, df.latitude)) #In hemisferic South, subtrair 360 in long coordinates

    # Removendo colunas "latitude" and "longitude" porque a coluna  "geometry" já mostra a informação
    df.drop(['latitude', 'longitude'], axis=1, inplace=True)
    df.set_crs(4326, allow_override=True, inplace=True) 

    return df

def find_station_virtual(df, point_station):

    '''  Esta função procura o ponto mais próximo (pertencente ao arquivo grib2)  
    da nossa estação de interesse.

    Recebe:
        df: dataframe do conjunto de pontos (oriundo do grib2) dos dados de precipitação
        point_station: coordenadas da estação de interesse, no formato Point(x, y)

    Retorna:
        df_satation_virtual: dataframe de linha única, contendo a estação virtual mais próxima da estação real
        df_sation_buffer: buffer da estação real, apenas como recurso de visualização
    '''

    #station Traipu
    geometry_station = len(df)*[point_station]
    df_station = gpd.GeoDataFrame(geometry=geometry_station, crs='EPSG:4326') 

    #Calculando distancias entre cada ponto de satélite e a estação de interesse
    df['distances'] = df.distance(df_station)

    #armazenaremos os pontos (dados satélites) mais próximos da estação real
    #chameremos esses pontos de estações virtuais
    df.sort_values(by='distances', inplace=True)
    df_stations_virtual = df[:4]

    return df_stations_virtual


def find_points_extreme_region(df_region):
    '''  Recebe o dataframe contendo a geometria (em uma coluna geometry) da região de interesse e
    retorna uma lista com os dois pontos extremos da geometria da região'''

    start = dt.datetime.now()

    bounds = df_region.geometry.apply(lambda x: x.bounds).tolist()

    minx, miny, maxx, maxy = min(bounds, key=itemgetter(0))[0], min(bounds, key=itemgetter(1))[1], max(bounds, key=itemgetter(2))[2], max(bounds, key=itemgetter(3))[3] #https://stackoverflow.com/questions/13145368/find-the-maximum-value-in-a-list-of-tuples-in-python
    
    return [Point((minx, miny)), Point((maxx, maxy))]

def map_stations(shape_region, df_station_real, df_stations_virtual, df_prec, name_region='', name_station_real=''):

    #Definindo subplots
    fig, ax = plt.subplots(figsize=(20, 20))

    #Região ambiental de interesse
    shape_region.plot(ax=ax, color='moccasin', edgecolor='black')

    #Estação real de interesse
    df_station_real.plot(ax=ax, color='black', linewidth=5)

    #Plotando algumas estações "virtuais próximas a de interesse"
    df_stations_virtual.plot(ax=ax, color='green', linewidth=5)

    # "Estação oriunda do satélite" mais próxima da estação real de interesse
    station_virtual = df_stations_virtual[:1]
    station_virtual.plot(ax=ax, color='blue', linewidth=5)

    #Calculando pontos limites da região
    limits_region = find_points_extreme_region(shape_region)

    #Configurando mapa
    ax.set_title("Mapeando 'estações virtuais'", size=40) 
    ax.set_xlabel('Longitude (°)', size=20)
    ax.set_ylabel('Latitude (°)', size=20)

    ax.xaxis.set_tick_params(labelsize=15)
    ax.yaxis.set_tick_params(labelsize=15)
    
    # Definindo texto e legenda
    ax.legend(['Estação ' + name_station_real, 'Estações virtuais no entorno', 'Estação Virtual mais próxima'], fontsize=25)
    ax.text(shape_region.centroid[0].x, shape_region.centroid[0].y, name_region, fontsize=50)

    x_min, x_max = limits_region[0].x, limits_region[1].x
    y_min, y_max = limits_region[0].y, limits_region[1].y

    # add minor ticks with a specified sapcing (deg)
    deg = 0.1
    ax.set_xticks(np.arange(np.ceil(x_min), np.ceil(x_max), deg), minor=False)
    ax.set_yticks(np.arange(np.ceil(y_min), np.ceil(y_max), deg), minor=False)

    ax.grid(which="major", color='black', linestyle='--', alpha=0.8)
    #plt.grid()

    #Definindo limites de valores para cada eixo
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    fig.show() 

def organizing_stations(stations_virtual):

    ''' Esta função organiza a ordem na qual as estações devem aparecer na lista: 
            - Primeira estação: de menor longitude e menor latitude
            - Segunda estação: de maior longitude e menor latitude
            - Terceira estação: de menor longitude e maior latitude
            - Quarta estação: de maior longitude e maior latitude
        Entrada:
            - statins_virtual: dataframe resultante da função "find_station_virtual" do módulo 3
        Saída:
            - Lista com 4 tuplas de 3 coordenadas (representando cada "estação virtual"), com 
                [(long, lat, precipitation), ..., (long, lat, precipitation)]
     '''

    #Organizando (em ordem crescente) os valores de x e de y
    x_values = np.sort(stations_virtual.geometry.x.unique())
    y_values = np.sort(stations_virtual.geometry.y.unique())

    #Criando lista para armazenar coordenadas e respectivos valores de precipitação
    list_stations = []

    #Iternado os valores
    for y in y_values:
        for x in x_values:
            #Apenas gerando coordenadas
            coord = Point(x, y)

            #Procurando o valor de precipitação para o ponto do satélite 
            prec = stations_virtual[stations_virtual.geometry == coord].prec.to_list()[0]

            #Apenas armazenando os três valores e adicionando na lista
            p = (x, y, prec)
            list_stations.append(p)

    return list_stations


def bilinear_interpolation(point, stations):
    ''' Esta função realiza interpolação bilinear.
    Entrada:
        - point: coordenadas (x, y) do ponto que queremos interpolar
        - stations: lista contendo coordenadas e precipitação das 4 "estações virtuais".
            esta lista pode ser obtida automaticamente com a função organizing_statins '''

    #Coordenadas dos pontos e seus valores de precipitação
    x, y = point[0], point[1]
    x1, y1, f1 = stations[0][0], stations[0][1], stations[0][2]
    x2, y1, f2 = stations[1][0], stations[1][1], stations[1][2]
    x1, y2, f3 = stations[2][0], stations[2][1], stations[2][2]
    x2, y2, f4 = stations[3][0], stations[3][1], stations[3][2]

    #Interpolando no eixo x
    fR1 = (f1*(x2 - x)/(x2 - x1)) + (f2*(x - x1)/(x2 - x1))
    fR2 = (f3*(x2 - x)/(x2 - x1)) + (f4*(x - x1)/(x2 - x1))

    #Interpolando em y e em x
    fp = (fR1*(y2 - y)/(y2 - y1)) + (fR2*(y - y1)/(y2 - y1))

    return fp