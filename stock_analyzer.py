from typing import Dict, Any, Union

import yfinance as yf
import time
import pandas as pd
from pandas import DataFrame, Series
from util import write_pickle_data, get_pickle_data


def download_ticker_data(stock_file_name):
    ticker_json = pd.read_csv(stock_file_name)
    ticker_data_dic: Dict[Any, Union[Union[DataFrame, Series], Any]] = {}
    index = 0
    for symbol in ticker_json.Symbol:
        ticker_data_dic[symbol] = {"data": yf.download(symbol + '.NS', start="2015-01-01"),
                                   "sector": ticker_json.Sector[index],
                                   "count": ticker_json.Count[index]}
        time.sleep(1)
        print(f'done symbol {symbol}')
        index += 1
    return ticker_data_dic


# ticker_data_dic = download_ticker_data('nifty-500.csv')
ticker_data_dic = download_ticker_data('my-top-list.csv')
write_pickle_data('my-top-list-historical-data', ticker_data_dic)
