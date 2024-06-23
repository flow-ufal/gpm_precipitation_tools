import time
inicio = time.perf_counter()


#Inserindo caminho da pasta onde estão os modulos que utilizaremos
import sys
import geopandas as gpd
sys.path.insert(0, r"C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\LIB INPE\modulos_tratamento_dados\modulos_tratamento_dados\modulos")

#Importando os módulos
import modulo3_stations_virtual as modulo3
import modulo1_station_processing as modulo1 
import modulo2_statistics as modulo2

#Importanddo função para unir diversas geometrias 
from shapely.ops import cascaded_union, unary_union

#Leitura rquivo região de interesse (semiarido)
semiarido = gpd.read_file(r"C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\semiarido_2021\semiarido_2021.shp", crs='EPSG:4326')

#Vamos excluir os municípios que não fazem parte do Semiárido e unir a geometria ds demais, para termos uma única
semiarido_union = unary_union(semiarido[semiarido.Situacao != 'Excluído - Em contestação'].geometry)
semiarido_union = gpd.GeoDataFrame(geometry = [semiarido_union], crs='EPSG:4326')

#Caminho da pasta na qual o arquivo de interesse está localizado
#path = r"C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\LIB INPE\modulos_tratamento_dados\modulos_tratamento_dados\dados\DAILY_RAIN\MERGE_CPTEC_20100604.grib2"

path = r'C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\LIB INPE\modulos_tratamento_dados\modulos_tratamento_dados\dados\MONTHLY_ACCUM_MANUAL\MERGE_CPTEC_acum_jul_2020.nc'
#Realizando leitura do arquivo
df_prec = modulo3.read_file_precipitation_grib(path, temporal_scaling="monthly_accum_manual") 

#Buscando por um ponto (com dados de satélite) mais próximo possível da estação de interesse
# Coordenadas estação de Traipu
coords =  modulo3.Point((-37.0033, -9.9728))
station_real = gpd.GeoDataFrame(geometry=[coords]) 
stations_virtual = modulo3.find_station_virtual(df_prec, station_real.geometry[0])


import numpy as np
#Lendo arquivo de uma estação qualquer, neste caso, de Traipú
path = r'C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\Dados_estações\TRAIPU (1).xlsx'
df_traipu = modulo1.read_station(path)

#Selecionando lista com estações e ponto de interesse (estação Traipu)
list_stations = modulo3.organizing_stations(stations_virtual)
point_coords = (-37.00330, -9.97280)

#Calculando interpolação bilinear para as coordenadas da estação de Traipu
prec_interpolation = modulo3.bilinear_interpolation(point_coords, list_stations)

#Verificando valor de precipitação na estação de Traipu
prec_traipu = df_traipu[df_traipu.Data == "2020-02-04"]['Precipitação (mm)'].to_list()[0]


#importando funções
import os
import glob
from shapely import Point

#============================================================================================================
#                               FUNÇÕES PARA EXTRAIR NOMES DOS ARQUIVOS (SATÉLITE) 
#============================================================================================================


def filter_annual_path(path, year=2019, name_extension_file='grib2'):
    ''' Seleciona o nome das pastas com dados diários para um ano especificado '''

    list_path = glob.glob(os.path.join(path, "*." + str(name_extension_file))) 
    list_path = [path for path in list_path if str(year) in path]

    return list_path

def filter_range_annual_path(path, year_start=2019, year_end=2020, name_extension_file='grib2'):
    ''' Seleciona o nome das pastas com dados para um intervalo de anos especificado '''
    
    list_path = [path_name for year in range(year_start, year_end + 1) 
                 for path_name in filter_annual_path(path, year, name_extension_file)]
    
    return list_path

def filter_month_path(path, month=202001, name_extension_file='grib2'):
    ''' Seleciona um mês de um ano específico '''

    list_path = glob.glob(os.path.join(path, "*." + str(name_extension_file))) 
    list_path = [path for path in list_path if str(month) in path]

    return list_path

#============================================================================================================
#                             FUNÇÕES PARA EXTRAIR SÉRIES TEMPORAIS DE UM ÚNICO PIXEL
#============================================================================================================

def prec_series_grib(x_point, y_point, list_path, temporal_scaling='dailly_rain'):

    ''' Gera uma série de dados para um ponto específico do arquivo grib
    x_point: coodenada x do ponto de interesse dos dados de setélite
    y_point: coordenada y do ponto de interesse
    list_path: lista com a pasta de cada arquivo que desejamos realizar a leitura '''

    #Criando dataframe para armazenar dados
    df_prec = gpd.GeoDataFrame(columns=['prec', 'Date'])

    #Apenas criando duas listas, cada uma para armazenar valores de precipitação e a data
    list_prec, list_date = [], []
        
    #Lendo arquivo com dados de cada dia, porém em diversos pontos 
    list_prec_day = [modulo3.read_file_precipitation_grib(path, temporal_scaling=temporal_scaling) for path in list_path]

    #Selecionando o valor de um ponto específico
    list_filter_point = [prec_day[(np.around(prec_day.geometry.x, 2) == x_point) & (np.around(prec_day.geometry.y, 2) == y_point)] for prec_day in list_prec_day]

    #Adicionando a lista os valores de precipitação e a data
    prec = [filter_point.prec.to_list()[0] for filter_point in list_filter_point]
    list_prec.append(prec)

    date = [filter_point.time.to_list()[0] for filter_point in list_filter_point]
    list_date.append(date)

    #Acrescentando ao dataframe
    df_prec['prec'], df_prec['Date'] = list_prec, list_date

    return df_prec 


#============================================================================================================
#                         FUNÇÕES PARA CALCULAR INTERPOLAÇÃO BILINEAR DOS ARQUIVOS (SATÉLITE) 
#                                           (comparação PIXEL Ponto)
#============================================================================================================

def calc_interpolation_series(coords_station, list_name_files, df_station, temp_scale='dailly_rain'):

    #Guardando em uma lista os valores
    values_station = df_station['Precipitação (mm)'].to_list()

    #Armazenando coordenadas da estação
    station_real = gpd.GeoDataFrame(geometry=[Point(coords_station)]) 

    #Lista para guardar resultado dos valores interpolados
    values_interpolation = [] 

    #Realizando leitura do arquivo
    list_df_prec = [modulo3.read_file_precipitation_grib(path_data, temporal_scaling=temp_scale) for path_data in list_name_files]
    
    #Procurando as 4 estaçõs virtuais mais próximas
    list_stations_virtual = [modulo3.find_station_virtual(df_prec, station_real.geometry[0]) for df_prec in list_df_prec]
    
    #Selecionando lista com estações e ponto de interesse (estação Traipu)
    list_stations = [modulo3.organizing_stations(stations_virtual) for stations_virtual in list_stations_virtual]

    #Calculando interpolação bilinear para as coordenadas da estação de Traipu
    prec_interpolation = [modulo3.bilinear_interpolation(coords_station, stations) for stations in list_stations]
    
    return values_station, prec_interpolation 

#Filtrando os dados da estação para uma data específica
range_data = df_traipu[(df_traipu.Data >= "2001-01-01") & (df_traipu.Data <= "2002-12-31")]

#Calculando acumulados mensais para um único ano
traipu_month_accum = modulo2.month_statistics(range_data, opc=0)
traipu_month_accum = traipu_month_accum[traipu_month_accum.index != '2009-06-30']


import multiprocessing

def test_paralelism():
    path = r'C:\Users\Ari\Documents\UFAL\Pesquisa\PIBIC 23-24\Dados\LIB INPE\modulos_tratamento_dados\modulos_tratamento_dados\dados\MONTHLY_ACCUM_MANUAL'

    files = filter_range_annual_path(path, year_start=2001, year_end=2002, name_extension_file='nc')

    coords_station = (-37.00330, -9.97280)

    interpolation = calc_interpolation_series(coords_station, files, traipu_month_accum, temp_scale='monthly_accum_manual')

    print(interpolation[1])
    print('=========================================')

if __name__ == '__main__':

    cod = multiprocessing.Process(target=test_paralelism)
    cod.start()
    cod.join()

    fim = time.perf_counter()
    print('Tempo execução:', round(fim-inicio), 2)
