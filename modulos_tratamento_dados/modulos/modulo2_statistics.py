#==================================================================================================
#                                        MÓDULO 2: Funções de estatística
#==================================================================================================

#Importando funções
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import scipy


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
    new_index = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    for df in list_statistics[:4]:
        df.index = new_index

    return list_statistics[opc]


def plot_statistics(list_statistics, list_names_titles):
    '''  Com esta função, plotamos gráficos para visualizar as estatísticas das funções anteriores
    ENTRADA:
        - list_statistics: lista contendo os dataframes de interesse, resultantes das funções acima
        - list_names_titles: lista contendo o nome do título que queremos em cada gráfico  '''

    for i in range(len(list_statistics)): 

        plt.figure()

        #Selecionando os valores de x e y a serem plotados
        x_values = list_statistics[i].index.to_list()
        y_values = list_statistics[i]['Precipitação (mm)']

        #Verificando se vamos plotar os dados na escala mensal

        index = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        if x_values == index: #vamos identificar pelo índice sendo os meses
            #Tamanho das barras
            width_bar = 0.5

            #Selecionando o que irá aparecer no eixo x do gráfico
            x_names = index
            x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            plt.xticks(x_values, x_names, size=12)

        else:
            #Tamanho das barras
            width_bar = 200

            #Selecionando o que irá aparecer no eixo x do gráfico
            x_names = False
            x_values = list_statistics[i].index

        plt.bar(x_values, y_values, color='darkblue', width=width_bar)
        name_title = list_names_titles[i]

        plt.title(name_title, size=15, color='black')
        plt.ylabel('Precipitação (mm)', size=15)
        plt.xticks(size=12)
        plt.yticks(size=12) 

        plt.show() 

def empirical_dist(data):
    '''  Gera distribuição empírica (CDF) e tempo de retorno 
    - data: lista com os dados'''

   
    #Crianddo dataframe, atribuindo valores dso dados a coluna 'prec'
    df_empirical = pd.DataFrame(columns=['prec', 'prob_cdf', 'prob_pdf', 'tr'])
    df_empirical['prec'] = data

    #Organizando em ordem crescente e redefinindo o índice
    df_empirical.sort_values(by='prec', inplace=True)
    df_empirical.reset_index(inplace=True)
    df_empirical.drop(columns=['index'], inplace=True)

    #Calculando e armazenando CDF e tempo de retorno
    df_empirical['prob_cdf'] = [i  / len(df_empirical) for i in range(1, len(df_empirical)+1)]
    df_empirical['tr'] = 1 / (1 - df_empirical['prob_cdf'])

    return df_empirical

def gev_dist(data):
    ''' Gera distribuições PDF, CDF e tempo de retorno para distribuçãi GEV
    - data: lista com os dados'''

    #obtendo parâmetros para distribuição GEV
    param_gev = scipy.stats.genextreme.fit(data)

    #forma da distribuição, localzação e escala 
    alpha, loc, scale = param_gev[0], param_gev[1], param_gev[2]

    #Dataframe para armazenar valores
    df_gev = pd.DataFrame(columns=['prec', 'prob_cdf', 'prob_pdf', 'tr'])
    df_gev['prec'] = data

    #Organizando em ordem crescente
    df_gev.sort_values(by='prec', inplace=True)

    #Gerando valores de probabilidad acumulada
    dist = scipy.stats.genextreme(c= alpha, loc=loc, scale=scale)
    
    x = df_gev['prec']
    #Obtendo distribuições
    df_gev['prob_pdf'] = dist.pdf(x)
    df_gev['prob_cdf'] = dist.cdf(x)
    df_gev['tr'] = 1 / (1 - df_gev['prob_cdf'])

    return df_gev



def gumbel_dist(data):
    ''' Gera distribuições PDF, CDF e tempo de retorno para distribuçãi Gumbel
    - data: lista com os dados'''

    #obtendo parâmetros para distribuição gumbel
    param_gumbel = scipy.stats.gumbel_r.fit(data)
    mean_gumbel, std_gumbel = param_gumbel[0], param_gumbel[1]

    #Dataframe para armazenar valores
    df_gumbel = pd.DataFrame(columns=['prec', 'prob_cdf', 'prob_pdf', 'tr'])
    df_gumbel['prec'] = data

    #Organizando em ordem crescente
    df_gumbel.sort_values(by='prec', inplace=True)

    #Gerando valores de probabilidade acumulada
    dist = scipy.stats.gumbel_r(loc=mean_gumbel, scale=std_gumbel)
    
    x = df_gumbel['prec']
    #Obtendo distribuições
    df_gumbel['prob_pdf'] = dist.pdf(x)
    df_gumbel['prob_cdf'] = dist.cdf(x)
    df_gumbel['tr'] = 1 / (1 - df_gumbel['prob_cdf'])

    return df_gumbel

def lognorm_dist(data):
    ''' Gera distribuições PDF, CDF e tempo de retorno para distribuçãi LogNorm
    - data: lista com os dados'''

    #obtendo parâmetros para distribuição gumbel
    param_lognorm = scipy.stats.lognorm.fit(data)
    s, loc, scale = param_lognorm[0], param_lognorm[1], param_lognorm[2]

    #Dataframe para armazenar valores
    df_lognorm = pd.DataFrame(columns=['prec', 'prob_cdf', 'prob_pdf', 'tr'])
    df_lognorm['prec'] = data

    #Organizando em ordem crescente
    df_lognorm.sort_values(by='prec', inplace=True)

    #Gerando valores de probabilidade acumulada
    dist = scipy.stats.lognorm(s=s, loc=loc, scale=scale)

    x = df_lognorm['prec']
    #Obtendo distribuições
    df_lognorm['prob_pdf'] = dist.pdf(x)
    df_lognorm['prob_cdf'] = dist.cdf(x)
    df_lognorm['tr'] = 1 / (1 - df_lognorm['prob_cdf'])

    return df_lognorm


def plot_dist_theorical(list_df_dist, list_dist_names):

    ''' Plota PDF, CDF e tempo de retorno para distribuições teóricas calculadas
        list_df_dist: uma lista contendo os dataframes da distribuições desejadam calculadas com as funções acima
        list_dist_names: uma lista com nome de cada respectiva distribuição
        '''
    #Gerando figura e eixo com três linha e 1 única coluna
    fig, ax = plt.subplots(3, figsize=(8, 20))

    #Iterando os dataframes das distribuiçõs
    for df in list_df_dist:
        #Valores que irão no eixo x
        x = df['prec']

        #Plotando pdf
        ax[0].plot(x, df['prob_pdf'], linewidth=3)
        ax[0].set_title('Função de densidade probabilidade (PDF)', weight='bold')
        ax[0].set_xlabel('Precipitação (mm)', weight='bold')
        ax[0].set_ylabel('Probabilidade', weight='bold')
        ax[0].legend(list_dist_names)
        ax[0].grid(True)

        #Plotando cdf
        ax[1].plot(x, df['prob_cdf'], linewidth=3)
        ax[1].set_title('Função de densidade probabilidade acumulada (CDF)', weight='bold')
        ax[1].set_xlabel('Precipitação (mm)', weight='bold')
        ax[1].set_ylabel('Probabilidade cumulativa', weight='bold')
        ax[1].legend(list_dist_names)
        ax[1].grid(True)

        #Plotando tempo de retorno
        ax[2].plot(df['tr'], x, linewidth=3)
        ax[2].set_title('Tempo de Retorno', weight='bold')
        ax[2].set_xlabel('Anos', weight='bold')
        ax[2].set_ylabel('Precipitação (mm)', weight='bold')
        ax[2].legend(list_dist_names)
        ax[2].grid(True)
    

def plot_dist_empirical(df_empirical, nbins=20, widthbar=50):
    ''' Plota histograma, CDF e tempo de retorno para uma única distribuição empirica
        df_empirical: dataframe com os dados empíricos
        '''
    #Gerando figura e eixo com três linha e 1 única coluna
    fig, ax = plt.subplots(3, figsize=(8, 20))

    #Valores que irão no eixo x
    x = df_empirical['prec']

    #Plotando histograma
    ax[0].hist(x, bins=nbins, density=True, width=widthbar, color='darkblue', edgecolor='black')
    ax[0].set_title('Função de densidade probabilidade (PDF)', weight='bold')
    ax[0].set_xlabel('Precipitação (mm)', weight='bold')
    ax[0].set_ylabel('Probabilidade', weight='bold')
    ax[0].legend(['Empirical'])
    ax[0].grid(True)

    #Plotando cdf
    ax[1].scatter(x, df_empirical['prob_cdf'], color='darkblue', linewidth=3)
    ax[1].set_title('Função de densidade probabilidade acumulada (CDF)', weight='bold')
    ax[1].set_xlabel('Precipitação (mm)', weight='bold')
    ax[1].set_ylabel('Probabilidade cumulativa', weight='bold')
    ax[1].legend(['Empirical'])
    ax[1].grid(True)

    #Plotando tempo de retorno
    ax[2].scatter(df_empirical['tr'], x, color='darkblue', linewidth=3)
    ax[2].set_title('Tempo de Retorno', weight='bold')
    ax[2].set_xlabel('Anos', weight='bold')
    ax[2].set_ylabel('Precipitação (mm)', weight='bold')
    ax[2].legend(['Empirical'])
    ax[2].grid(True)


def plot_all_dist(list_df_dist, list_dist_names, nbins=20, widthbar=3):
    ''' Esta função plota:
            - histograma de uma distribuição empírica junto da PDF de cada distribuição teórica
            - CDF de todas as distribuições
            - Tempo de retorno de todas as distribuições 
            
        - list_df_dist: lista com as distribuições. Ex: [df_empirica, df_gev, df_gumbel]
        ======================================  IMPORTANTE   ================================

            Em list_df_dist, o dataframe da distribuição empírica SEMPRE deve ser o PRIMEIRO 

        ======================================  IMPORTANTE   ================================
        - list_dist_names: lista com nome das distribuições. Ex: ['Empírica', 'Gev', 'Gumbel]'''

    #Gerando figura e eixo com três linha e 1 única coluna
    fig, ax = plt.subplots(3, figsize=(8, 20))

    #Iterando os dataframes das distribuiçõs
    for i in range(len(list_df_dist)):
        #Apenas guardando o datafram e o valor que irá no eixo x
        df = list_df_dist[i]
        x = df['prec']

        #Plotando gráficos referentes a distribuição empírica, que é o primeiro elemento da lista
        if i == 0:        
            #Na sequência histograma, CDF e tempo de retorno
            ax[0].hist(x, density=True, bins=nbins, width=widthbar, color='darkblue', edgecolor='white', label='Empirical')
            ax[1].scatter(x, df['prob_cdf'], color='darkblue', linewidth=3)
            ax[2].scatter(df['tr'], x, color='darkblue', linewidth=3)
            ax[0].legend(list_dist_names)

        #Plotando para as distribuições teóricas
        else:
            #Na sequência PDF, CDF e tempo de retorno
            ax[0].plot(x, df['prob_pdf'], linewidth=3)
            ax[1].plot(x, df['prob_cdf'], linewidth=3)
            ax[2].plot(df['tr'], x, linewidth=3)
            ax[0].legend(list_dist_names)


        #Confugurando legendas dos gráficos
        #PDF
        ax[0].set_title('Função de densidade probabilidade (PDF)', weight='bold')
        ax[0].set_xlabel('Precipitação (mm)', weight='bold')
        ax[0].set_ylabel('Probabilidade', weight='bold')
        ax[0].grid(True)

        #CDF
        ax[1].set_title('Função de densidade probabilidade acumulada (CDF)', weight='bold')
        ax[1].set_xlabel('Precipitação (mm)', weight='bold')
        ax[1].set_ylabel('Probabilidade cumulativa', weight='bold')
        ax[1].legend(list_dist_names)
        ax[1].grid(True)

        #Tempo de retorno
        ax[2].set_title('Tempo de Retorno', weight='bold')
        ax[2].set_xlabel('Anos', weight='bold')
        ax[2].set_ylabel('Precipitação (mm)', weight='bold')
        ax[2].legend(list_dist_names)
        ax[2].grid(True)