#==================================================================================================
#                     MÓDULO 01: Pré-processamento dos dados das estações  
#==================================================================================================

#Importando bibliotecas
import pandas as pd
import geopandas as gpd
import os
import glob
from shapely import Point

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
    point_station = [Point(long, lat)]

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
        falha_range = -99
        
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
