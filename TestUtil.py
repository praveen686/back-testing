from datetime import timedelta

import pandas as pd
from option_util import *
from util import write_pickle_data, get_pickle_data
from datetime import datetime, timedelta


# fields = ['date_time', 'close']
# nifty_prefix = 'nifty' if "BANKNIFTY" == "NIFTY" else "b-nifty"
# filename = f'{nifty_prefix}-minute-candle.csv'
# start = millis()
# dt = pd.read_csv(filename, index_col=0, usecols=fields, sep=',').T.to_dict()
# print(f'read csv>>> {(millis() - start)}')
# write_pickle_data(f'{nifty_prefix}-minute-candle', dt)
# print(f'write data>>> {(millis() - start)}')
# new_dt = get_pickle_data(f'{nifty_prefix}-minute-candle')
# print(f'read data {(millis() - start)}')

# store_trading_days('NIFTY')
# store_trading_days('BANKNIFTY')

class Laptop:

    def __init__(self, name, processor, hdd, ram, cost):
        self.name = name
        self.processor = processor
        self.hdd = hdd
        self.ram = ram
        self.cost = cost

    def details(self):
        print('The details of the laptop are:')
        print('Name         :', self.name)
        print('Processor    :', self.processor)
        print('HDD Capacity :', self.hdd)
        print('RAM          :', self.ram)
        print('Cost($)      :', self.cost)


def test_time():
    # date_time_obj = datetime.datetime.strptime("2019-04-18T12:30:00+0530", '%Y-%m-%d')
    date_time_obj = datetime.datetime.strptime("2019-04-18T12:30:00+0530", '%Y-%m-%dT%H:%M:%S+0530')
    print(date_time_obj)
    final_time = date_time_obj + timedelta(minutes=10)
    final_time_str = final_time.strftime('%Y-%m-%dT%H:%M:%S+0530')
    print(final_time_str)


def test_cum_prod():
    import pandas as pd
    df1 = pd.DataFrame({'close': [1, 2, 3, 4]})
    df1['dreturn'] = df1['close'].pct_change() + 1
    df1['creturn'] = df1['dreturn'].cumprod() - 1

    df2 = pd.DataFrame({'close': [1, 2, 3, 4]})
    df2['dreturn'] = df2['close'].pct_change() + 1
    df2['creturn'] = df2['dreturn'].cumprod() - 1

    df3 = pd.concat([df1, df2])
    df3 = df3.dropna()
    df3['creturn'] = df3['dreturn'].cumprod() - 1
    df3.dropna()
    print(df2)


def test_str_replace(time_part: str, sl: float):
    time_part = time_part.replace(":00", "").replace(":", "")
    file_name = f'trade_data_{time_part}_{sl}'
    print(file_name)


def get_minutes():
    start_time = datetime.strptime('2021-01-01 09:20:00', '%Y-%m-%d %H:%M:%S')
    # considering its going till 11:30
    minute_diff = 130
    minute_list = [start_time + timedelta(minutes=it) for it in range(0, int(minute_diff + 1), 10)]
    minute_list_str = [minute.strftime("%H:%M:%S") for minute in minute_list]
    return minute_list_str


def write_to_file():
    file_name = f'trade_data/trade_data_{"44"}_{".4"}.data'
    f = open(file_name, "w")
    f.write("hello")


# test_str_replace("09:20:00", .4)
# get_minutes()
write_to_file()
