import datetime
import random
from typing import List

import numpy as np
import pandas as pd

from option_util import get_minute_list, millis, load_nifty_min_data, load_india_vix_day_data, get_nifty_spot_price, \
    get_nearest_thursday, get_india_vix, round_nearest, get_nearest_expiry, get_instrument_prefix
from util import get_pickle_data, write_pickle_data, get_date_from_str

minute_list = get_minute_list('%H:%M:%S', "09:15:00", "15:30:00")

vix_data_dic = get_pickle_data('india-vix-day-candle')
day_keys = list(vix_data_dic.keys())
# print(len(strike_prices) * len(day_keys) * len(minute_list))
# print(len(strike_prices), len(day_keys), len(minute_list))
trade_intervals = ["0920", "0940", "1000", "1020", "1040",
                   "1100", "1120", "1140", "1200", "1220", "1240", "1300", "1320", "1340", "1400"]
df_base_min_list = []
df_base_day_list = []
df_base_day_str_list = []
df_base_india_vix_list = []
df_nifty_spot_price_list = []

df_minute_list = []
df_day_list = []
df_day_str_list = []
df_strike_list = []
df_value_list = []
df_index_list = []

df_other_day_list = []
df_other_day_str_list = []
df_other_time_intervals = []
df_other_atm_option_strike_list = []
df_other_atm_premium_list = []
df_other_option_type_list = []


def populate_list():
    count = 0
    start_time = 1546300800000
    start_strike_price = 34500
    expiry_df = pd.read_csv("expiry_df.csv")
    day_strike_index_list = get_pickle_data("day_strike_index_list")
    start = millis()
    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    print(f'time:{millis() - start}')
    india_vix_day_dic = load_india_vix_day_data()
    print(f'time:{millis() - start}')
    trading_days_list = list(india_vix_day_dic.keys())
    print(f'time:{millis() - start}')
    trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    for trading_date_str in trading_days_list:
        trading_date = get_date_from_str(trading_date_str)
        # day_time = start_time + (day * 86400000)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        strike_list = get_strikes_by_day(day_strike_index_list, date_time_in_secs)
        nearest_expiry_date = get_nearest_expiry(trading_date_str, expiry_df)
        for minute in minute_list:
            df_base_min_list.append(minute)
            df_base_day_list.append(date_time_in_secs)
            df_base_day_str_list.append(trading_date_str)
            df_base_india_vix_list.append(get_india_vix(trading_date_str, india_vix_day_dic))
            nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_min_data_dic, 'close')
            df_nifty_spot_price_list.append(nifty_spot_price)
        #     get strike for the day
        for strike_price in strike_list:
            strike_ticker_pe_symbol = generate_ticker_symbol(nearest_expiry_date, strike_price, "PE")
            strike_ticker_ce_symbol = generate_ticker_symbol(nearest_expiry_date, strike_price, "CE")
            for ticker in [strike_ticker_pe_symbol, strike_ticker_ce_symbol]:
                # strike_price = get_nearest_thursday(trading_date, "PE" if strike_index % 2 == 0 else "CE", strike_index)
                # strike_list.append(strike_price)
                for minute in minute_list:
                    # print(random.randrange(100, 300, 3))
                    df_value_list.append(random.randrange(100, 300, 3))
                    df_day_list.append(date_time_in_secs)
                    df_day_str_list.append(trading_date_str)
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
                df_other_day_list.append(date_time_in_secs)
                df_other_day_str_list.append(trading_date_str)
                df_other_time_intervals.append(trade_interval)
                df_other_atm_option_strike_list.append(atm_option_type_strike)
                df_other_atm_premium_list.append(atm_premium)
                df_other_option_type_list.append(option_type)

    print(f'len of other day list:{len(df_other_day_list)}')

    base_minute_df = pd.DataFrame(
        {'day': df_base_day_list, 'day_str': df_base_day_str_list, 'minute': df_base_min_list,
         "vix": df_base_india_vix_list, "spot": df_nifty_spot_price_list},
        df_base_day_list)

    every_minute_df = pd.DataFrame(
        {'day': df_day_list, 'day_str': df_day_str_list, 'strike': df_strike_list, 'minute': df_minute_list,
         'value': df_value_list},
        df_day_list)

    all_atm_df = pd.DataFrame(
        {'day': df_other_day_list, 'day_str': df_other_day_str_list, 'interval': df_other_time_intervals,
         'atm_option_strike': df_other_atm_option_strike_list,
         'atm_premium': df_other_atm_premium_list, "option_type": df_other_option_type_list},
        df_other_day_list)

    write_pickle_data('every_minute_df', every_minute_df)
    write_pickle_data('all_atm_df', all_atm_df)
    write_pickle_data('base_minute_df', base_minute_df)
    print("done with iteration")


def generate_ticker_symbol(expiry_date, strike_price, option_type):
    expiry_date_diff_format = expiry_date.strftime("%Y-%m-%d")
    prefix = get_instrument_prefix(expiry_date_diff_format, "BANKNIFTY")
    return f'{prefix}{strike_price}{option_type}'


def new_test_data():
    start = millis()

    print(f'time after trading days:{millis() - start}')
    all_strike_df = get_pickle_data('every_minute_df')
    base_minute_df = get_pickle_data('base_minute_df')
    all_atm_df = get_pickle_data('all_atm_df')
    print(f'time after getting pickle data:{millis() - start}')
    df_only_9_20_pe = all_atm_df[(all_atm_df.interval == "0920") & (all_atm_df.option_type == "PE")]
    df_only_9_20_ce = all_atm_df[(all_atm_df.interval == "0920") & (all_atm_df.option_type == "CE")]
    print(f'time after getting 920 strike symbol:{millis() - start}')
    print(len(df_only_9_20_pe), len(df_only_9_20_pe))
    _0920_pe_strike_df = pd.merge(all_strike_df, df_only_9_20_pe, how='inner', left_on=['day', 'strike'],
                                  right_on=['day', 'atm_option_strike'])
    _0920_ce_strike_df = pd.merge(all_strike_df, df_only_9_20_ce, how='inner', left_on=['day', 'strike'],
                                  right_on=['day', 'atm_option_strike'])
    print(f'time after getting 920 strike ticker:{millis() - start}')
    print(len(_0920_ce_strike_df), len(_0920_ce_strike_df))
    _0920_straddle_df = pd.merge(base_minute_df, _0920_pe_strike_df, how='left', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'])
    _0920_straddle_df = pd.merge(_0920_straddle_df, _0920_ce_strike_df, how='inner', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'])
    print(len(_0920_straddle_df), len(_0920_straddle_df))
    print(f'time after merging strike ticker to base:{millis() - start}')
    # df_0920_atm_strike.to_csv("df_0920.csv")
    # write_pickle_data('_0920_straddle_df', _0920_straddle_df)
    print(f'time before loop:{millis() - start}')
    values = _0920_straddle_df.values
    done_days = []
    day_profit = 0
    day_profit_list = []
    for i in range(len(values)):
        date_time = values[i][0]
        if date_time not in done_days:
            day_profit = 0
            done_days.append(date_time)
            day_profit_list.append(day_profit)
        else:
            # in_date_format = datetime.datetime.fromtimestamp(date_time / 1000.0)
            # get_nifty_spot_price(, close_candle['time'],
            #                      self.day_tracker.nifty_min_data_dic,
            #                      self.day_tracker.config.column_to_consider)
            day_profit = day_profit + 9
        # print()
    print(f'time:{millis() - start}', len(day_profit_list))
    # merge = pd.merge(trade_df_list[0], trade_df_list[1], how='inner', left_index=True, right_index=True)


def get_all_nifty_strikes():
    trading_minute_list = get_minute_list('%H:%M:%S', "09:20:00", "14:30:00")
    start = millis()
    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    print(f'time:{millis() - start}')
    india_vix_day_dic = load_india_vix_day_data()
    print(f'time:{millis() - start}')
    trading_days_list = list(india_vix_day_dic.keys())
    print(f'time:{millis() - start}')
    trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    for trading_date_str in trading_days_list:
        trading_date = get_date_from_str(trading_date_str)
        # day_time = start_time + (day * 86400000)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        strike_list = []
        for minute in trading_minute_list:
            df_base_min_list.append(minute)
            df_base_day_list.append(date_time_in_secs)
            df_base_day_str_list.append(trading_date_str)
            nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_min_data_dic, 'close')
            df_nifty_spot_price_list.append(nifty_spot_price)

    nifty_spot_df = pd.DataFrame(
        {'day': df_base_day_list, 'day_str': df_base_day_str_list, 'minute': df_base_min_list,
         "spot": df_nifty_spot_price_list},
        df_base_day_list)
    nifty_spot_df = nifty_spot_df[nifty_spot_df.spot != -1]
    print(len(nifty_spot_df.groupby(['day'])))
    nifty_spot_df['r_spot_price'] = nifty_spot_df['spot'].round()
    nifty_spot_df['r_strike_price'] = (nifty_spot_df['r_spot_price']).apply(round_nearest, args=(100,))
    nifty_strike_df = nifty_spot_df[['r_strike_price', 'day']].groupby(['day', 'r_strike_price'])['r_strike_price'].agg(
        ['min', 'max', 'first', 'count'])

    nifty_strike_index_values = nifty_strike_df.index.values
    write_pickle_data('day_strike_index_list', nifty_strike_index_values)


def get_strikes_by_day(day_strike_index_list: List, day: int):
    strikes = [entry[1] for entry in day_strike_index_list if day == entry[0]]
    return strikes


# test_data()
populate_list()
# new_test_data()
# get_all_nifty_strikes()
# print(len(minute_list))
# get_nearest_thursday()
# print("done!!!", random.random())
