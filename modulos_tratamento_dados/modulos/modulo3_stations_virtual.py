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

def read_file_precipitation_grib(path, temporal_scaling="daily_rain"):

    '''  Esta função realiza um tratamento inicial dos dados diários, ajusta as coordenadas
    path: caminho da pasta no qual o arquivo (em formato grib2) está localizado 
    temporal_scaling: informar se estamos com arquivos de dados diários, mensais ou anuais
        Diário: escrever "daily_rain",
        Mensal: escrever "monthly_accum_manual"
        Anual: escrever "yearly_accum" '''
    
    #Lendo dado hierárquico
    ds = xr.open_dataset(path)

    #Opções que o usuário irá selecionar para filtrarmos nome de variáveis
    options_scaling = {'daily_rain':['prec', 'longitude', 'latitude', 360], 'monthly_accum_manual':['monthacum', 'longitude', 'latitude', 0], 'yearly_accum':['pacum', 'lon', 'lat', 0]}

    #Filtrando nome da variável para cada escala temporal (cada uma vez com um nome diferente de coluna indicando precipitação)
    name_precipitation = options_scaling[temporal_scaling][0]
    name_coordinates = [options_scaling[temporal_scaling][1], options_scaling[temporal_scaling][2]]
    long_factor = options_scaling[temporal_scaling][3]

    #Filtrando variável de interesse
    df = ds.get(name_precipitation).to_dataframe()  
    df.reset_index(inplace=True)

    #Organizando nomes das colunas
    df = df.rename({name_coordinates[0]: 'longitude', name_coordinates[1]:'latitude', name_precipitation:'prec'}, axis = 1)

    #Salvando geometrias
    df = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude-long_factor, df.latitude)) #In hemisferic South, subtrair 360 in long coordinates

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
    df_station = gpd.GeoDataFrame(geometry=geometry_station, crs='EPSG:4326') #crs=4326

    # Convertendo para um sistema de referência cuja unidade está em metros
    df_station.to_crs('EPSG:3857', inplace=True) 
    df.to_crs('EPSG:3857', inplace=True)

    #Calculando distancias entre cada ponto de satélite e a estação de interesse
    df['distances'] = df.distance(df_station)

    #armazenaremos os 4 pontos (dados satélites) mais próximos da estação real
    #chameremos esses pontos de estações virtuais
    df.sort_values(by='distances', inplace=True)
    df_stations_virtual = (df[:4]).to_crs('EPSG:4326')

    return df_stations_virtual


def find_points_extreme_region(df_region):
    '''  Recebe o dataframe contendo a geometria (em uma coluna geometry) da região de interesse e
    retorna uma lista com os dois pontos extremos da geometria da região'''

    bounds = df_region.bounds
    #Cálculo apoximado do centroide da figura
    x_center = (bounds.maxx[0] + bounds.minx[0])/2
    y_center = (bounds.maxy[0] + bounds.miny[0])/2

    return [Point((bounds.minx[0], bounds.miny[0])), Point((bounds.maxx[0], bounds.maxy[0])), Point(x_center, y_center)]

def map_stations(shape_region, df_station_real, df_stations_virtual, df_prec, name_region='', name_station_real=''):
    ''' Esta função plota um mapa da região de interesse, assim como as estações virtuais e a estação real  '''
    #Definindo subplots
    fig, ax = plt.subplots(figsize=(10, 8))

    #Região ambiental de interesse
    shape_region.plot(ax=ax, color='green', alpha=0.7, edgecolor='black') #color=moccasin

    #Estação real de interesse
    df_station_real.plot(ax=ax, color='black', linewidth=3)

    #Plotando algumas estações "virtuais próximas a de interesse"
    df_stations_virtual.plot(ax=ax, color='red', linewidth=3)

    # "Estação oriunda do satélite" mais próxima da estação real de interesse
    station_virtual = df_stations_virtual[:1]
    station_virtual.plot(ax=ax, color='blue', linewidth=3)

    #Calculando pontos limites da região
    limits_region = find_points_extreme_region(shape_region)

    #Configurando mapa 
    ax.set_title("Mapeando 'estações virtuais'", size=20, weight='bold') 
    ax.set_xlabel('Longitude (°)', size=12, weight='bold')
    ax.set_ylabel('Latitude (°)', size=12, weight='bold')
    
    #Definindo texto e legenda
    ax.legend(['Estação ' + name_station_real, 'Estações virtuais no entorno', 'Estação Virtual mais próxima'], fontsize=13)
    ax.text(limits_region[2].x, limits_region[2].y, name_region, fontsize=40, color='white', weight='bold')

    x_min, x_max = limits_region[0].x,  limits_region[1].x
    y_min, y_max = limits_region[0].y, limits_region[1].y

    #Adicionando os valores das coordenadas 
    deg = 0.1
    ax.set_xticks(np.arange(np.ceil(x_min), np.ceil(x_max), deg), minor=False)
    ax.set_yticks(np.arange(np.ceil(y_min), np.ceil(y_max), deg), minor=False)

    #Definindo tamanho das legendas em cada eixo
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)

    #Restringindo a apenas duas casas decimais as coordenadas e definindo inclinação da legenda
    list_ticks = [np.around(tick, 2) for tick in ax.get_xticks()]
    ax.set_xticklabels(list_ticks, rotation = 45)

    ax.grid(which="major", color='black', linestyle='-', alpha=1)
    #plt.grid()

    #Definindo limites de valores para cada eixo
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

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

    coords = [(point.x, point.y) for point in stations_virtual.geometry]
    prec = [p for p in stations_virtual.prec]
    lista_points = [(coords[index][0], coords[index][1], prec[index])  for index in range(len(coords))]

    return lista_points

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





'''
    ADAPTAR CÓDIGO PRA ESSE FUNÇÃO
def bilinear(x, y, points):
    points = sorted(points)
    (x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

    if x1 != _x1 or x2 != _x2 or y1 != _y1 or y2 != _y2:
        raise ValueError('points do not form a retangle')
    if not x1 <= x <= x2 or not y1 <= y <= y2:
        raise ValueError('(x, y) not within the retangle')
    
    return (q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1)) / ((x2 - x1) * (y2 - y1) + 0.0)'''
