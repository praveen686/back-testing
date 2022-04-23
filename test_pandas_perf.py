import datetime
import random

import numpy as np
import pandas as pd

from option_util import get_minute_list, millis
from util import get_pickle_data, write_pickle_data

minute_list = get_minute_list('%H:%M:%S')

vix_data_dic = get_pickle_data('india-vix-day-candle')
day_keys = list(vix_data_dic.keys())
# print(len(strike_prices) * len(day_keys) * len(minute_list))
# print(len(strike_prices), len(day_keys), len(minute_list))
trade_intervals = ["0920", "0940", "1000", "1020", "1040",
                   "1100", "1120", "1140", "1200", "1220", "1240", "1300", "1320", "1340", "1400"]
df_minute_list = []
df_day_list = []
df_strike_list = []
df_value_list = []
df_index_list = []

df_other_day_list = []
df_other_time_intervals = []
df_other_atm_strike_list = []
df_other_atm_premium_list = []


def populate_list():
    count = 0
    start_time = 1546300800000
    start_strike_price = 34500
    for day in range(750):
        day_time = start_time + 86400000
        strike_list = []
        for strike_index in range(6):
            in_date_format = datetime.datetime.fromtimestamp(day_time / 1000.0)
            strike_price = get_nearest_thursday(in_date_format, "PE" if strike_index % 2 == 0 else "CE")
            strike_list.append(strike_price)
            for minute in minute_list:
                # print(random.randrange(100, 300, 3))
                df_value_list.append(random.randrange(100, 300, 3))
                df_day_list.append(day_time)
                df_strike_list.append(strike_price)
                df_minute_list.append(minute)
                df_index_list.append(count)
                count = count + 1
                # print(count)
        for trade_interval in trade_intervals:
            atm_strike = strike_list[random.randrange(0, 5)]
            atm_premium = random.randrange(100, 300, 3)
            df_other_day_list.append(day_time)
            df_other_time_intervals.append(trade_interval)
            df_other_atm_strike_list.append(atm_strike)
            df_other_atm_premium_list.append(atm_premium)

    every_minute_df = pd.DataFrame(
        {'day': df_day_list, 'strike': df_strike_list, 'minute': df_minute_list, 'value': df_value_list},
        df_strike_list)

    all_atm_df = pd.DataFrame(
        {'day': df_other_day_list, 'interval': df_other_time_intervals, 'atm_strike': df_other_atm_strike_list,
         'atm_premium': df_other_atm_premium_list},
        df_other_day_list)

    write_pickle_data('every_minute_df', every_minute_df)
    write_pickle_data('all_atm_df', all_atm_df)
    print("done with iteration")


def test_data():
    compare_df = pd.DataFrame(
        {'day': [1, 2, 3]},
        ['BANKNIFTYJAN34500PE', 'BANKNIFTYJAN34500PE', 'BANKNIFTYJAN34500PE'])
    start = millis()
    my_test_df = get_pickle_data('my_test_df')
    print(len(my_test_df))
    start = millis()
    # print(len(my_test_df))
    # print(my_test_df.loc[1750000])Ω
    # df_out_1 = my_test_df.query(
    #     'index == 0 or index==1 or index == 3 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1 or index == 0 or index==1')
    # df_out = my_test_df.query('index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530" or '
    #                           'index == "2022-02-16T00:00:00+0530" or index == "2022-02-17T00:00:00+0530"'
    #                           )

    # print(my_test_df.index)
    # my_test_df['flag'] = np.where(
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530") |
    #     (my_test_df.index == "2022-02-16T00:00:00+0530")
    #     , 'Y', '0')

    hellons = my_test_df[(my_test_df.index == 'BANKNIFTYJAN34500PE') |
                         # (my_test_df.index == 'BANKNIFTYAPR34000CE') |
                         # (my_test_df.index == 'BANKNIFTYAPR34000CE') |
                         # (my_test_df.index == 'BANKNIFTYAPR34000CE') |
                         (my_test_df.index == 'BANKNIFTYMAR34500CE')
                         ]
    print("length", compare_df.iloc[1].day == 2)
    # test_df = my_test_df[compare_df.loc[my_test_df.index].day == 1]
    # print(my_test_df.iloc[1].index)
    # print(my_test_df.iloc[True].index)
    # check_diff = compare_df[my_test_df.iloc[1].day.values[0] == 1]
    check_diff = compare_df[(True)]
    print(("time taken to read first", (millis() - start)))

    my_test_df['check'] = my_test_df['value'] + 1
    print(("time taken to read first", (millis() - start)))
    # print(my_test_df)
    # helloons = df_out.values
    print("to filter by query", (millis() - start))

    print("to filter by query", (millis() - start))
    # for i in range(len(my_test_df)):
    for i in []:
        # start = millis()
        # df_row = my_test_df[my_test_df.day == "2022-02-16T00:00:00+0530"]
        df_row = my_test_df.loc[i]
        # print(("time taken to read file", (millis() - start)))
        print(i)
    print("done")
    start = millis()
    print(("time taken to read file", (millis() - start)))


def get_nearest_thursday(curr_date, option_type):
    # start_time = datetime.datetime.strptime('2022-12-23', '%Y-%m-%d')
    # print(start_time.strftime('%a'), start_time.strftime('%Y'))
    d = curr_date.weekday()
    days_to_thursday = 3 - d if (3 - d) >= 0 else 7 - (d - 3)
    expiry_day = curr_date + datetime.timedelta(days=days_to_thursday)
    expiry_year = expiry_day.strftime('%Y')[-2:]
    expiry_month = int(expiry_day.strftime("%m"))
    expiry_day = expiry_day.strftime("%d")
    formatted_expiry_month = expiry_month if expiry_month < 10 else "O" if expiry_month == 10 else "N" if expiry_month == 11 else "D"
    strike_price = 34000 + random.randrange(1, 1000)
    banknifty_ticker_symbol = f'BANKNIFTY{expiry_year}{formatted_expiry_month}{expiry_day}{strike_price}{option_type}'
    return banknifty_ticker_symbol


def new_test_data():
    every_minute_df = get_pickle_data('every_minute_df')
    all_atm_df = get_pickle_data('all_atm_df')
    df_only_9_20 = all_atm_df[all_atm_df.interval == "0920"]


# test_data()
populate_list()
# get_nearest_thursday()
# print("done!!!", random.random())
