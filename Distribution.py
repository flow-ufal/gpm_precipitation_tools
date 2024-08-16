import numpy as np
import pandas as pd
from math import isnan
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from scipy.stats import lognorm, genextreme, chi2, gumbel_r


def annual_maximum(filename):
    """
    Returns annual maximum rainfall.
    """
    data = pd.read_excel(filename, header=6)

    del data['Unnamed: 0']
    data.index = pd.to_datetime(data['Data'])
    del data['Data']

    annual_accum = data['Precipitação'].resample('YE').max()
    annual_accum.index = annual_accum.index.year
    annual_accum.index.name = 'Ano'

    return annual_accum


# Máxima anual de uma estação
station = "D:\Pesquisa\PIBIC_23-24\Estacoes\Estacoes_SIGA\PÃO DE AÇÚCAR.xlsx"
station_max = annual_maximum(station)

# Ajustar os dados da chuva máxima anual diária
rainfall_max_decreasing = station_max.to_list()
rainfall_max_decreasing = [data for data in rainfall_max_decreasing if isnan(data) == False]
rainfall_max_decreasing.sort(reverse=True)


# Criar distribuição empírica
def empirical_Dist(data):
    """
    Returns empirical distribution of annual maximum rainfall.
    """
    empirical_Distribution = pd.DataFrame(data=data, columns=['QuantisP'])
    empirical_Distribution['Prob'] = [(i + 1) / len(empirical_Distribution) for i in empirical_Distribution.index.to_list()]
    empirical_Distribution['Return_Period_(Years)'] = 1 / empirical_Distribution['Prob']

    return empirical_Distribution


# Criar dataframe da distribuição log normal
def logNormal_Dist(data):
    """
    Returns LogNormal Distribution of annual maximum rainfall
    """
    lnPmax = list(map(np.log, data))
    media_lnPmax = sum(lnPmax) / len(lnPmax)
    std = np.std(lnPmax)

    logNormal_Distribution = pd.DataFrame(data=np.linspace(1.01, 100, len(rainfall_max_decreasing)), columns=['TR'])
    logNormal_Distribution['Prob'] = 1 / logNormal_Distribution['TR']
    logNormal_Distribution['QuantisP'] = [
        lognorm.ppf(1 - prob, std, loc=0, scale=np.exp(media_lnPmax)) for prob in logNormal_Distribution['Prob'].to_list()
        ]

    return logNormal_Distribution


# Elaborar distribuição GEV
def gev_Dist(data):
    """
    Returns GEV (Generalized Extreme Value) distribution of annual maximum rainfall
    """
    params = genextreme.fit(rainfall_max_decreasing, method='MLE')
    tr = np.linspace(1.01, 100, len(rainfall_max_decreasing))
    quantis = [genextreme.ppf(1 - 1/(ano), *params) for ano in tr]

    df = pd.DataFrame(tr, columns=['TR'])
    df['QuantisP'] = quantis

    return df


# Elaborar distribuição Gumbell
def gumbel_Dist(data):
    params = gumbel_r.fit(data)
    loc, scale = params
    tr = np.linspace(1.01, 100, len(rainfall_max_decreasing))
    quantis = [gumbel_r.ppf(1 - 1/(ano), loc=loc, scale=scale) for ano in tr]

    df = pd.DataFrame(tr, columns=['TR'])
    df['QuantisP'] = quantis

    return df


# Carregar dados
df1 = empirical_Dist(rainfall_max_decreasing)
df2 = logNormal_Dist(rainfall_max_decreasing)
df3 = gev_Dist(rainfall_max_decreasing)
df4 = gumbel_Dist(rainfall_max_decreasing)

# Teste de Aderência
def goodness_of_fit_test(df_empirical, df_theory, intervals):
    """
    Returns the chi-squared score for a theorical distribution.
    """
    data1 = df_empirical['QuantisP']
    freq_obs, bins = np.histogram(data1, bins=intervals)
    dist_theory = df_theory['QuantisP']
    freq_theory, _ = np.histogram(dist_theory, bins=bins)

    chi2_obs = np.sum((freq_obs - freq_theory) ** 2 / freq_theory)

    degree_freedom = len(dist_theory) - 1

    alpha = 0.05
    chi2_critic = chi2.ppf(1 - alpha, degree_freedom)

    return {'chi2_obs': chi2_obs, 'chi2_critic': chi2_critic}


chi2_logNormal, chi2_crit = goodness_of_fit_test(df1, df2, 5).values()
chi2_GEV, _ = goodness_of_fit_test(df1, df3, 5).values()
chi2_gumbel, _ = goodness_of_fit_test(df1, df4, 5).values()

x2 = {'LogNormal': chi2_logNormal, 'GEV': chi2_GEV, 'Gumbel': chi2_gumbel}
k_better = [chave for chave, valor in x2.items() if valor == min(x2.values())][0]
label_validate = f'A distribuição que melhor representa os dados é a {k_better}'

# Plotagem dos gráficos
fig, ax = plt.subplots()

df1.plot.scatter(ax=ax, x='Return_Period_(Years)', y='QuantisP', label='Empírica', c='blue', alpha=0.6, edgecolor='black')
df2.plot(ax=ax, x='TR', y='QuantisP', c='darkorange', label='LogNormal')
df3.plot(ax=ax, x='TR', y='QuantisP', c='red', label='GEV')
df4.plot(ax=ax, x='TR', y='QuantisP', c='purple', label='Gumbel')

ax.set_xlabel('Tempo de Retorno (anos)', weight='bold')
ax.set_ylabel('Precipitação Máxima (mm)', weight='bold')
ax.set_title('Distribuições da Chuva - Pão de Açucar', weight='bold')

# text = fig.text(0.5, 0.5, label_validate, color='lime', ha='center', va='center', size=10)
# text.set_path_effects([path_effects.Stroke(linewidth=3, foreground='black'), path_effects.Normal()])

plt.grid(linestyle='-')
plt.legend()
plt.show()
