import pandas as pd
from option_util import *
from util import write_pickle_data, get_pickle_data


def store_india_vix_data():
    fields = ['date_time', 'close']
    dt = pd.read_csv('india-vix-minute-candle.csv', index_col=0, usecols=fields, sep=',').T.to_dict()
    write_pickle_data(f'india-vix-minute-candle', dt)


