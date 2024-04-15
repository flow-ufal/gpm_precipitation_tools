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


#==================================================================================================
#          MÓDULO 01: Leitura, tratamento e testes estatísticos dos dados das estações
#==================================================================================================

def read_station(path):

    '''  Esta função recebe o caminho do arquivo e realiza um tratamento prévio dos dados:
        - Extrai a latitude, longitude e o identificador da estação (orgão responsável e código)
        - Reune todas as informações acima em um geodataframe.
       '''

    #Realizando leitura do arquivo
    df = pd.read_excel(path)

    #obtendo latitue e longitude da estação, além do seu ID
    ''' - O cabeçalho do arquivo é constituido por 4 partes, conforme o exemplo a seguir:

            Secretaria de Estado do Meio Ambiente e dos Recursos Hídricos - SEMARH/AL
            Superintendência de Prevenção em Desastres Naturais - SPDEN
            Banco de Dados Hidrometeorológicos - BDHM
            Estação ANA_937013 Lat: -9.3928 Lng: -37.9942
            Download
            ------------------------------------------------												
        - Quando realizamos a leitura do arquito, todo o cabeçalho vem no formato de string, onde cada linha é separada por "\n";
            - Então, vamos separar essa string, ir até a linha de interesse e selecionar as informações '''

    #3 corresponde a posição da linha onde estão os dados de interesse, 0 por ser a primeira coluna do arquivo
    list_info_header = df.columns[0].split('\n')[3].split(' ')  

    #id da estação sempre na posição 1 
    id_station = list_info_header[1]

    #latitude sempre está na posição 3 da lista e longitude na posição 5
    lat = float(list_info_header[3])
    long = float(list_info_header[5]) 
    point_station = [Point(lat, long)]

    #Excluindo coluna com os índices 
    df.drop(df.columns[0], axis=1, inplace=True)

    #Excluindo as 6 linhas do cabeçalho e redefinindo o nome das colunas
    df = df.loc[6:]
    df.columns = ['Data', 'Precipitação (mm)']

    #Convertendo para os formatos adequados dos dados (datetime e float)
    df['Precipitação (mm)'] = pd.to_numeric(df['Precipitação (mm)'])
    df['Data'] = pd.to_datetime(df['Data'])

    #Apenas adicionando o id da estação e a sua localização
    df['ID'] = [id_station]*len(df)
    df['geometry'] = point_station*len(df)

    #Definindo ID e geometry sendo os índices
    df.set_index(['ID', 'geometry'], inplace=True)

    return df

def data_availability_station(df, date_1='2000-06-01', date_2='2020-06-30'):

    '''  Esta função calcula a porcentagem de falha nos dados para toda a série e para um intervalo de data especificado
         df: DataFrame com a série histórica;
         data_1: primeira data do intervalo que desejamos conhecer a disponibilidade dos dados, por padrão 2000-06-01
         data_2: segunda data do intervalo que desejamos conhecer a disponibilidade dos dados, por padrão 2020-30-06
       '''

    #Armazenando a menor e maior data
    date_start = min(df['Data'])
    date_end = max(df['Data'])

    #Calculando quantidade de dias para que a série esteja completa
    qtd_days_full = 1 + (date_end - date_start).days #+1 porque (date_end - date_start).days calcula em intervalo aberto e queremos contabilizar desde o dia inicial

    #Calculando efetivamente quantos dias a série tem
    qtd_days_true = len(df) #cada linha corresponde a um dia

    #porcentagem de falha de toda a série
    falha_full = 100*(1-(qtd_days_true/qtd_days_full))

    #verificando se a série histórica contém dados para o intervalo especificado
    date_inf = pd.to_datetime(date_1)
    date_sup = pd.to_datetime(date_2)

    if (date_inf >= date_start) and (date_sup <= date_end):
        #Filtrando os dados
        df_range = df[ (df['Data'] >= date_inf) & (df['Data'] <= date_sup) ]

        #calculando a disponibilidade dos dados 
        qtd_days_full = 1 + (date_sup - date_inf).days
        qtd_days_true = len(df_range)

        #porcentagem de falha para o intervalo especificado
        falha_range = 100*(1-(qtd_days_true/qtd_days_full))

    else:
        #indica que o intervalo especificado não está compreendido naquela série histórica
        falha_range = 'Out_of_range'
        
    return [falha_full, falha_range]

def data_info(path, date_1='2000-06-01', date_2='2020-06-30'):

    df = read_station(path)
    falha = data_availability_station(df, date_1=date_1, date_2=date_2)
    
    #Criando GeoDataFrame para armanezar algumas informações acerca da estação de interesse
    df_info = gpd.GeoDataFrame(columns=['Orgão', 'Nome_esta', 'Data_start', 'Data_end', '%_falha_full', '%_falha_range', 'geometry'])

    #Temos o formato orgão_código. Ex: ANA_937013. Vamos separa em diferentes colunas essas informações
    df_info['Orgão'] = [df.index[0][0].split('_')[0]]
    df_info.index = [df.index[0][0].split('_')[1]] 
    df_info.index.name = 'Code'

    #Vamos utilizar o próprio nome do arquivo sendo o da estação. Ex: DELMIRO GOLVEIA.xlsx
    df_info['Nome_esta'] = path.split('\\')[len(path.split('\\'))-1][:-5] #[:-5] é para returar o "xlsx"
    df_info['Data_start'] = [min(df['Data'])]
    df_info['Data_end'] = [max(df['Data'])]
    df_info['%_falha_full'] = [falha[0]]
    df_info['%_falha_range'] = [falha[1]]
    df_info['geometry'] = [df.index[0][1]]

    #Definindo um sistema de referênciaa
    df_info.set_crs('EPSG:4674')
    return df_info

def read_full_stations(path, date_1='2000-06-01', date_2='2020-06-30'):

    ''' Como dado de entrada, o caminho para uma pasta que contenha o arquivo de cada estação de interesse.
       Esta função realiza a leitura e tratamento prévio dos dados de cada estação e calcula as porcentagens
       de falha da série.'''

    # glob procura todos os arquivos na pasta especificada e retorna os endereços, neste caso, com o critério "*.xlsx"
    list_path = glob.glob(os.path.join(path, "*.xlsx")) 

    list_df = []
    for path_station in list_path: 
        #obtendo as informações acerca da estação e armazenando em uma lista
        df = read_station(path_station)
        info_station = data_info(path_station, date_1=date_1, date_2=date_2)
        list_df.append(info_station)

    df_info_stations = pd.concat(list_df) 

    return df_info_stations
#==================================================================================================



#==================================================================================================
#                                        MÓDULO 02: 

#       - Leitura e tratamento inicial de arquivo hierárquico (.grib2, .nc)
#       - Dada a localização de uma estação de interesse, procura pontos (GPM) próximos
#       - Visualização das estações reais e virtuais na região de interesse
#==================================================================================================

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

    #chamaremos o ponto (dado de satélite) mais próx. da estação real de "estação virtual"
    df_station_virtual = gpd.GeoDataFrame(df[df['distances'] == min(df['distances'])])

    return df_station_virtual


def find_points_extreme_region(df_region):
    '''  Recebe o dataframe contendo a geometria (em uma coluna geometry) da região de interesse e
    retorna uma lista com os dois pontos extremos da geometria da região'''

    start = dt.datetime.now()

    bounds = df_region.geometry.apply(lambda x: x.bounds).tolist()

    minx, miny, maxx, maxy = min(bounds, key=itemgetter(0))[0], min(bounds, key=itemgetter(1))[1], max(bounds, key=itemgetter(2))[2], max(bounds, key=itemgetter(3))[3] #https://stackoverflow.com/questions/13145368/find-the-maximum-value-in-a-list-of-tuples-in-python
    
    return [Point((minx, miny)), Point((maxx, maxy))]

def map_stations(shape_region, df_station_real, df_station_virtual, df_prec, name_region='', name_station_real=''):

    #Definindo subplots
    fig, ax = plt.subplots(figsize=(20, 20))

    #Região ambiental de interesse
    shape_region.plot(ax=ax, color='moccasin', edgecolor='black')

    # Estação real de interesse
    df_station_real.plot(ax=ax, color='black', linewidth=5)

    # Bucanso e plotando algumas estações "virtuais próximas a de interesse"
    esta_proximas = df_prec[df_prec['distances'] <= 0.15]
    esta_proximas.plot(ax=ax, color='green', linewidth=5)

    # "Estação oriunda do satélite" mais próxima da estação real de interesse
    df_station_virtual.plot(ax=ax, color='blue', linewidth=5)

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
