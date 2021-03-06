# coding: utf-8

# DO NOT EDIT
# Autogenerated from the notebook statespace_cycles.ipynb.
# Edit the notebook and then sync the output with this file.
#
# flake8: noqa
# DO NOT EDIT

# # 失业趋势和周期
#
# 在这里，我们考虑三种方法来分解经济数据的趋势性和周期性。 假设我们有一个时间序列 $y_t$，将其分解为以下两个成分：
#
# $$
# y_t = \mu_t + \eta_t
# $$
#
# 其中 $\mu_t$ 代表趋势性或水平，而 $\eta_t$ 代表周期性成分。 在这个示例中，我们考虑一个 *stochastic* 趋势，
# 因此 $\mu_t$ 是随机变量，而不是时间的确定性函数。 两种方法属于“未观察到的组件”模型的标题，第三种是受大家欢迎
# 的 Hodrick-Prescott (HP) 过滤器。 与（示例）一致， Harvey 和 Jaeger (1993)，我们发现这些模型都产生相似的分解。
#
# 本笔记演示了如何应用这些模型将美国失业率的周期性与趋势性分开。


import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

from pandas_datareader.data import DataReader
endog = DataReader('UNRATE', 'fred', start='1954-01-01')

# ### Hodrick-Prescott (HP) 过滤器
#
# 第一种方法是 Hodrick-Prescott 过滤器，以一种直接了当的方法将其应用于数据序列。
# 这里我们指定参数 $\lambda=129600$ 是因为每月观察一次失业率。


hp_cycle, hp_trend = sm.tsa.filters.hpfilter(endog, lamb=129600)

# ### 未观测到组件 和 ARIMA 模型 (UC-ARIMA)
#
# 下一种方法是未观察的组件模型，其中趋势性建模是随机移动的，并使用 ARIMA 模型对周期进行建模-特别是在这里，我们使用AR（4）模型。 
# 时间序列可以写成：
#
# $$
# \begin{align}
# y_t & = \mu_t + \eta_t \\
# \mu_{t+1} & = \mu_t + \epsilon_{t+1} \\
# \phi(L) \eta_t & = \nu_t
# \end{align}
# $$
#
# 其中 $\phi(L)$ 是 AR(4) 滞后多项式，且 $\epsilon_t$ 和 $\nu_t$ 是白色噪音.

mod_ucarima = sm.tsa.UnobservedComponents(endog, 'rwalk', autoregressive=4)
# Here the powell method is used, since it achieves a
# higher loglikelihood than the default L-BFGS method
res_ucarima = mod_ucarima.fit(method='powell', disp=False)
print(res_ucarima.summary())

# ### 随机周期性未观察到的组件 (UC)
#
# 最后的一种方法是一个未观察到组件的模型，但是其中周期性是明确建模的。
#
# $$
# \begin{align}
# y_t & = \mu_t + \eta_t \\
# \mu_{t+1} & = \mu_t + \epsilon_{t+1} \\
# \eta_{t+1} & = \eta_t \cos \lambda_\eta + \eta_t^* \sin \lambda_\eta +
# \tilde \omega_t \qquad & \tilde \omega_t \sim N(0, \sigma_{\tilde
# \omega}^2) \\
# \eta_{t+1}^* & = -\eta_t \sin \lambda_\eta + \eta_t^* \cos \lambda_\eta
# + \tilde \omega_t^* & \tilde \omega_t^* \sim N(0, \sigma_{\tilde
# \omega}^2)
# \end{align}
# $$

mod_uc = sm.tsa.UnobservedComponents(
    endog,
    'rwalk',
    cycle=True,
    stochastic_cycle=True,
    damped_cycle=True,
)
# 在这里，powell 方法接近最优
res_uc = mod_uc.fit(method='powell', disp=False)

# 但是为了达到最高对数似然率，我们使用 L-BFGS 方法进行第二轮拟合。
res_uc = mod_uc.fit(res_uc.params, disp=False)
print(res_uc.summary())

# ### 图形比较
#
# 这些模型的每一个的输出是趋势性 $\mu_t$ 的估计和周期性 $\eta_t$ 的估计。从质量上来说，趋势性和周期性的估计非常相似，
# 尽管来自 H P过滤器的趋势性组件比来自未观察到的组件模型的趋势性组件更加可变。 这意味着失业率的相对波动模式是由于基本
# 趋势的变化，而不是暂时的周期性变化。
# 

fig, axes = plt.subplots(
    2, figsize=(13, 5))
axes[0].set(title='Level/trend component')
axes[0].plot(endog.index, res_uc.level.smoothed, label='UC')
axes[0].plot(endog.index, res_ucarima.level.smoothed, label='UC-ARIMA(2,0)')
axes[0].plot(hp_trend, label='HP Filter')
axes[0].legend(loc='upper left')
axes[0].grid()

axes[1].set(title='Cycle component')
axes[1].plot(endog.index, res_uc.cycle.smoothed, label='UC')
axes[1].plot(
    endog.index, res_ucarima.autoregressive.smoothed, label='UC-ARIMA(2,0)')
axes[1].plot(hp_cycle, label='HP Filter')
axes[1].legend(loc='upper left')
axes[1].grid()

fig.tight_layout()
