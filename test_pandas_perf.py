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
df_base_min_list = []
df_base_day_list = []

df_minute_list = []
df_day_list = []
df_strike_list = []
df_value_list = []
df_index_list = []

df_other_day_list = []
df_other_time_intervals = []
df_other_atm_option_strike_list = []
df_other_atm_premium_list = []
df_other_option_type_list = []


def populate_list():
    count = 0
    start_time = 1546300800000
    start_strike_price = 34500
    for day in range(750):
        day_time = start_time + (day * 86400000)
        strike_list = []
        for minute in minute_list:
            df_base_min_list.append(minute)
            df_base_day_list.append(day_time)
        for strike_index in range(6):
            in_date_format = datetime.datetime.fromtimestamp(day_time / 1000.0)
            strike_price = get_nearest_thursday(in_date_format, "PE" if strike_index % 2 == 0 else "CE", strike_index)
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
            for option_type in ["PE", "CE"]:
                atm_option_type_strike = [strike for strike in strike_list if option_type in strike][
                    random.randrange(0, 3)]
                atm_premium = random.randrange(100, 300, 3)
                df_other_day_list.append(day_time)
                df_other_time_intervals.append(trade_interval)
                df_other_atm_option_strike_list.append(atm_option_type_strike)
                df_other_atm_premium_list.append(atm_premium)
                df_other_option_type_list.append(option_type)

    print(f'len of other day list:{len(df_other_day_list)}')

    base_minute_df = pd.DataFrame(
        {'day': df_base_day_list, 'minute': df_base_min_list},
        df_base_min_list)

    every_minute_df = pd.DataFrame(
        {'day': df_day_list, 'strike': df_strike_list, 'minute': df_minute_list, 'value': df_value_list},
        df_strike_list)

    all_atm_df = pd.DataFrame(
        {'day': df_other_day_list, 'interval': df_other_time_intervals,
         'atm_option_strike': df_other_atm_option_strike_list,
         'atm_premium': df_other_atm_premium_list, "option_type": df_other_option_type_list},
        df_other_day_list)

    write_pickle_data('every_minute_df', every_minute_df)
    write_pickle_data('all_atm_df', all_atm_df)
    write_pickle_data('base_minute_df', base_minute_df)
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


def get_nearest_thursday(curr_date, option_type, strike_index):
    # start_time = datetime.datetime.strptime('2022-12-23', '%Y-%m-%d')
    # print(start_time.strftime('%a'), start_time.strftime('%Y'))
    d = curr_date.weekday()
    days_to_thursday = 3 - d if (3 - d) >= 0 else 7 - (d - 3)
    expiry_day = curr_date + datetime.timedelta(days=days_to_thursday)
    expiry_year = expiry_day.strftime('%Y')[-2:]
    expiry_month = int(expiry_day.strftime("%m"))
    expiry_day = expiry_day.strftime("%d")
    formatted_expiry_month = expiry_month if expiry_month < 10 else "O" if expiry_month == 10 else "N" if expiry_month == 11 else "D"
    strike_price = 34000 + random.randrange(100 * strike_index, 100 * (strike_index + 1))
    banknifty_ticker_symbol = f'BANKNIFTY{expiry_year}{formatted_expiry_month}{expiry_day}{strike_price}{option_type}'
    return banknifty_ticker_symbol


def new_test_data():
    start = millis()
    all_strike_df = get_pickle_data('every_minute_df')
    base_minute_df = get_pickle_data('base_minute_df')
    all_atm_df = get_pickle_data('all_atm_df')

    df_only_9_20_pe = all_atm_df[(all_atm_df.interval == "0920") & (all_atm_df.option_type == "PE")]
    df_only_9_20_ce = all_atm_df[(all_atm_df.interval == "0920") & (all_atm_df.option_type == "CE")]
    print(len(df_only_9_20_pe), len(df_only_9_20_pe))
    _0920_pe_strike_df = pd.merge(all_strike_df, df_only_9_20_pe, how='inner', left_on=['day', 'strike'],
                                  right_on=['day', 'atm_option_strike'])
    _0920_ce_strike_df = pd.merge(all_strike_df, df_only_9_20_ce, how='inner', left_on=['day', 'strike'],
                                  right_on=['day', 'atm_option_strike'])
    print(len(_0920_ce_strike_df), len(_0920_ce_strike_df))
    _0920_straddle_df = pd.merge(base_minute_df, _0920_pe_strike_df, how='left', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'])
    _0920_straddle_df = pd.merge(_0920_straddle_df, _0920_ce_strike_df, how='inner', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'])
    print(len(_0920_straddle_df), len(_0920_straddle_df))

    # df_0920_atm_strike.to_csv("df_0920.csv")
    write_pickle_data('_0920_straddle_df', _0920_straddle_df)
    print(f'time:{millis() - start}')
    values = _0920_straddle_df.values
    # df_0920_atm_strike = df_0920_atm_strike[
    #     (df_0920_atm_strike.minute >= "09:15:00") & (df_0920_atm_strike.minute <= "14:30:00")]
    # base_df = base_df.join(day_premium_change_df)
    # base_df[premium_change_col_name] = base_df[premium_change_col_name].replace(np.nan, 0)
    # base_df[premium_change_col_name] = base_df[premium_change_col_name].cumsum()
    # base_df['profit'] = base_df['profit'] + base_df[premium_change_col_name]
    # print(values)
    done_days = []
    day_profit = 0
    day_profit_list = []
    for i in range(len(values)):
        day = values[i][0]
        if day not in done_days:
            day_profit = 0
            done_days.append(day)
            day_profit_list.append(day_profit)
        else:
            day_profit = day_profit + 9
        # print()
    print(f'time:{millis() - start}', len(day_profit_list))
    # merge = pd.merge(trade_df_list[0], trade_df_list[1], how='inner', left_index=True, right_index=True)


# test_data()
# populate_list()
new_test_data()
# print(len(minute_list))
# get_nearest_thursday()
# print("done!!!", random.random())
