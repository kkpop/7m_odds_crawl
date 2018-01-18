# -*- coding: utf-8 -*-
import pdb
import matplotlib.pyplot as plt
from pylab import *
import pandas as pd

mpl.rcParams['font.sans-serif'] = ['SimHei']    #支持中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号

ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
ts = ts.cumsum()
ts.plot()

df = pd.DataFrame(np.random.randn(1000, 4), index=ts.index, columns=list('ABCD'))

df = df.cumsum()

plt.figure()
df.plot()
