#==================================================================================================
#                                        MÓDULO 2: Funções de estatística
#==================================================================================================

#Importando funções
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

def annual_statistics(df_station, opc=0):
    ''' Recebe df_station gerado com a função read_station e retorna um dataframe 
    com os valores acumulados em cada ano ou os máximos diários de cada ano
    ENTRADA:
        df_station: dataframe da estação, gerador pela função "read_station
        0: Acumulado anual
        1: Máximo diário no ano'''

    station_acum_anual = df_station.groupby(pd.Grouper(key='Data', freq='Y'))['Precipitação (mm)'].sum()
    station_acum_anual = pd.DataFrame(station_acum_anual)

    max_dailly_annual = df_station.groupby(pd.Grouper(key='Data', freq='Y'))['Precipitação (mm)'].max()
    max_dailly_annual = pd.DataFrame(max_dailly_annual)

    list_statistics = [station_acum_anual, max_dailly_annual]

    return list_statistics[opc]
             
def month_statistics(df_station, opc=0):
    ''' Retorna algumas estatísticas relacionadas aos dados acumulados mensais.

    - ENTRADA: 
        - df_station: dataframe da estação de interesse, gerado pela função "read_station" do módulo 1
        - scale: 
            0: Acumulado 
            1: Média
            2: Máximo
            3: Mínimo 
            4: Calcula tudo e retorna em uma lista '''

    #Primeiro, vamos selecionar o acumulado em cada mês de cada ano
    station_acum_month = df_station.groupby(pd.Grouper(key='Data', freq='M'))['Precipitação (mm)'].sum()
    station_acum_month = pd.DataFrame(station_acum_month)

    #Acumulado mensal somando os valores de meses de anos diferentes. Ex: jan/2000, jan/2001, jan/2002 ...
    acum_month = station_acum_month.groupby(station_acum_month.index.month).sum()

    #Para a média entre um mesmo mês, porém em anos diferentes.
    month_mean = station_acum_month.groupby(station_acum_month.index.month).mean()

    #De forma análoga, para o máximo
    month_max = station_acum_month.groupby(station_acum_month.index.month).max()

    #Para o mínimo, vamos desconsiderar os valores iguais a zero
    station_acum_month = station_acum_month[station_acum_month['Precipitação (mm)'] != 0]
    month_min = station_acum_month.groupby(station_acum_month.index.month).min()

    #Guardando em uma lista
    list_statistics = [acum_month, month_mean, month_max, month_min, [acum_month, month_mean, month_max, month_min]]

    #Mudando o índice dos dataframes
    new_index = ['Jan', 'Fev', 'Mar', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    for df in list_statistics[:4]:
        df.index = new_index

    return list_statistics[opc]


def plot_statistics(list_statistics, list_names_titles):
    '''  Com esta função, plotamos gráficos para visualizar as estatísticas das funções anteriores
    ENTRADA:
        - list_statistics: lista contendo os dataframes de interesse, resultantes das funções acima
        - list_names_titles: lista contendo o nome do título que queremos em cada gráfico  '''

    for i in range(len(list_statistics)): 
        if i == 0:
            width_bar = 300
        else:
            width_bar = 250 

        plt.figure()

        plt.bar(list_statistics[i].index, list_statistics[i], color='darkblue', width=width_bar)
        name_title = list_names_titles[i]
        plt.title(name_title, size=15, color='black')
        plt.ylabel('Precipitação (mm)', size=15)
        plt.xticks(size=12, rotation=30)
        plt.yticks(size=12) 

        plt.show() 
