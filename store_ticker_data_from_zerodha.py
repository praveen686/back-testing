import time;
import calendar
from typing import List

import requests
import pandas as pd

from util import write_pickle_data, get_pickle_data

print("")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Authorization': 'enctoken D1tQVzvB7+qZJjrBVYiQHd8kA5htch1m1CjkFfAnldIA8hl22Tqj7e+mXK5hRsDspDTFNHjntF9fm+9ktb2uQXQGnHR/ammbN2JCTxfYVdJEujvSFgi5yQ=='
}

columns = ['date_time', 'open', 'high', 'low', 'close', 'year', 'month', 'day']


def read_kite_nifty_min_data(instrument_token, start_year, end_year):
    instrument_minute_candle_list = []
    for year in range(start_year, end_year):
        for month in range(1, 13, 1):
            next_month = month
            padded_start_month = '{:02d}'.format(month)
            padded_end_month = '{:02d}'.format(next_month)
            last_day_of_month = calendar.monthrange(year, next_month)[1]
            start = '{}-{}-01'.format(year, padded_start_month)
            end = '{}-{}-{}'.format(year, padded_end_month, last_day_of_month)
            kite_url = 'https://kite.zerodha.com/oms/instruments/historical/{}/minute?user_id=XQ9712&oi=1&from={}&to={}'.format(
                instrument_token, start, end)
            print(kite_url)
            response = requests.get(kite_url, headers=headers)
            kite_data = response.json()
            for candle in kite_data['data']['candles']:
                # print(candle)
                date = pd.to_datetime(candle[0])
                df_json = {"date_time": candle[0], "open": candle[1], "high": candle[2], "low": candle[3],
                           "close": candle[4], 'year': year, 'day': date.day}
                instrument_minute_candle_list.append(df_json)
            # df=pd.read_json(data)
            # print(response.json())
            print('before')
            time.sleep(5)
            print('after')
    return instrument_minute_candle_list


def read_day_data(instrument_token, start_year, end_year):
    india_vix_candle_list = []
    for year in range(start_year, end_year):
        kite_url = f'https://kite.zerodha.com/oms/instruments/historical/{instrument_token}/day?user_id=XQ9712&oi=1&from={year}-01-01&to={year}-12-31'
        print(kite_url)
        response = requests.get(kite_url, headers=headers)
        kite_data = response.json()
        for candle in kite_data['data']['candles']:
            # print(candle)
            date = pd.to_datetime(candle[0])
            df_json = {"date_time": candle[0], "open": candle[1], "high": candle[2], "low": candle[3],
                       "close": candle[4], 'year': year, 'day': date.day}
            india_vix_candle_list.append(df_json)
        # df=pd.read_json(data)
        # print(response.json())
        print('before')
        time.sleep(5)
        print('after')

    return india_vix_candle_list


def get_as_dic(candle_list):
    candle_dic = {}
    for index in range(0, len(candle_list)):
        date_time_key = candle_list[index]['date_time']
        if date_time_key not in candle_dic:
            candle_dic[date_time_key] = {
                'close': candle_list[index]['close']}
        else:
            raise Exception(f'duplicate entry present {date_time_key}')
    return candle_dic


def store_india_vix_day_data_from_zerodha():
    # india_vix_df = pd.DataFrame(columns=columns)
    india_vix_candle_list = read_day_data(264969, 2019, 2023)
    # india_vix_df = pd.DataFrame(india_vix_candle_list)
    india_vix_candle_dic = get_as_dic(india_vix_candle_list)
    # india_vix_df.append(india_vix_candle_list)
    # india_vix_df.to_csv("india-vix-minute-candle.csv")
    write_pickle_data('india-vix-day-candle', india_vix_candle_dic)


def store_nifty_min_candle_from_zerodha():
    # nifty_df = pd.DataFrame(columns=columns)
    nifty_candle_list = read_kite_nifty_min_data(256265, 2019, 2023)
    nifty_candle_dic = get_as_dic(nifty_candle_list)
    write_pickle_data(f'nifty-minute-candle', nifty_candle_dic)


def store_bnifty_min_candle_from_zerodha():
    # nifty_df = pd.DataFrame(columns=columns)
    nifty_candle_list = read_kite_nifty_min_data(260105, 2019, 2023)
    nifty_candle_dic = get_as_dic(nifty_candle_list)
    write_pickle_data(f'b-nifty-minute-candle', nifty_candle_dic)


# nifty_one_minute_candle_list=read_kite_data(256265)
# print(nifty_one_minute_candle_list)

vix_data_dic = get_pickle_data('india-vix-day-candle')
day_keys = list(vix_data_dic.keys())
day_keys = [date.replace("T00:00:00+0530", "") for date in day_keys]
start_date = '2019-01-06'
print('werewr'.replace('we', 'ttt'))
print(start_date in day_keys)
index = day_keys.index(f'{start_date}')
print(index)
