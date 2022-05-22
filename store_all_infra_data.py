import datetime
from typing import List

import pandas as pd
import numpy as np

import constants
from grab_weekly_option_fies import get_all_nifty_weekly_option_files_for_2022, get_all_nifty_weekly_option_files
from option_util import get_minute_list, millis, load_nifty_min_data, load_india_vix_day_data, get_nifty_spot_price, \
    round_nearest, get_nearest_expiry, get_instrument_prefix, get_ticker_data_by_expiry_and_strike
from store_ticker_data_from_zerodha import store_bnifty_min_candle_from_zerodha, store_india_vix_day_data_from_zerodha

from util import write_pickle_data, get_date_from_str, get_date_in_str, get_pickle_data


def get_strikes_by_day(day_strike_index_list: List, day: int):
    strikes = [entry[1] for entry in day_strike_index_list if day == entry[0]]
    return strikes


# 1. get the pickle data that has the option files that has premium for every strike
# 2. loop through the trading days
# 3. get the all the atm strikes for the day
# 4. get the dic from the option file that has premium for the selected strike
# 5. loop through each minute and get the data corresponding each minute from the dic and populate the list
# 6. use the above list to populate every minute df.
def populate_every_minute_df(start_date: str, end_date: str):
    df_minute_list = []
    df_day_list = []
    df_day_str_list = []
    df_strike_price_list = []
    df_strike_ticker_symbol_list = []
    df_value_list = []
    df_index_list = []
    df_nifty_spot_price_list = []

    minute_list = get_minute_list('%H:%M:%S', "09:15:00", "15:30:00")
    # to hold strike list by day, just for temp purpose
    strike_list_by_day = []
    count_of_strike_min = 0
    start_time = 1546300800000
    start_strike_price = 34500
    expiry_df = pd.read_csv("expiry_df.csv")
    day_strike_index_list = get_pickle_data("day_strike_index_list")
    weekly_option_data_files = get_pickle_data(f'b_nifty_weekly_option_data_files_till_20')
    start = millis()
    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    print(f'time:{millis() - start}')
    india_vix_day_dic = load_india_vix_day_data()
    print(f'time:{millis() - start}')
    trading_days_list = list(india_vix_day_dic.keys())
    print(f'time:{millis() - start}')
    trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    for trading_date_str in trading_days_list:
        if trading_date_str < start_date or trading_date_str > end_date:
            continue
        day_spot_price_list = []
        day_ticker_symbols = []
        trading_date = get_date_from_str(trading_date_str)
        # day_time = start_time + (day * 86400000)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        # 'day strike index list' has the atm strike for every minute,
        strike_list = get_strikes_by_day(day_strike_index_list, date_time_in_secs)
        strike_list_by_day.append(strike_list)
        nearest_expiry_date = get_nearest_expiry(trading_date_str, expiry_df)
        instrument_prefix = get_instrument_prefix(get_date_in_str(nearest_expiry_date, constants.DATE_FORMAT),
                                                  "BANKNIFTY")

        for strike_price in strike_list:
            # for strike_price in []:
            for option_type in ["PE", "CE"]:
                # strike_price = get_nearest_thursday(trading_date, "PE" if strike_index % 2 == 0 else "CE", strike_index)
                # strike_list.append(strike_price)
                trade_date_in_option_format = get_date_in_str(trading_date, "%m/%d/%Y")
                candle_start = millis()
                strike_ticker_candles_for_trade_date_dic, expiry_date_str, ticker_prefix, ticker_file_name = \
                    get_ticker_data_by_expiry_and_strike(
                        strike_price, nearest_expiry_date, option_type, trade_date_in_option_format,
                        weekly_option_data_files, "BANKNIFTY")
                if len(strike_ticker_candles_for_trade_date_dic) == 0:
                    print(
                        f'strike ticker not present for {trading_date_str} ticker:{strike_price} option:{option_type}')
                print("time taken s", (millis() - candle_start))
                # print("time taken for strike data>>>>", (millis() - candle_start), (millis() - start_of_loop))
                # if len(strike_ticker_candles_for_trade_date_dic) < 300:
                #     print(
                #         f'>>>>>>< 300 for strike:{ticker_prefix}:{strike_price}:{trading_date_str} '
                #         f'size:{len(strike_ticker_candles_for_trade_date_dic)}')
                strike_ticker_symbol = f'{ticker_prefix}{strike_price}{option_type}'
                for minute in minute_list:
                    nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_min_data_dic, 'close')
                    if minute in strike_ticker_candles_for_trade_date_dic:
                        ticker_premium = strike_ticker_candles_for_trade_date_dic[minute]['close']
                    else:
                        ticker_premium = np.nan
                    df_value_list.append(ticker_premium)
                    df_day_list.append(date_time_in_secs)
                    df_day_str_list.append(trading_date_str)
                    df_strike_price_list.append(strike_price)
                    df_strike_ticker_symbol_list.append(strike_ticker_symbol)
                    df_minute_list.append(minute)
                    df_index_list.append(count_of_strike_min)
                    df_nifty_spot_price_list.append(round_nearest(nifty_spot_price, 100))

                    day_ticker_symbols.append(strike_ticker_symbol)
                    count_of_strike_min = count_of_strike_min + 1
                    # print("time taken each minute>>>>", (millis() - candle_start), (millis() - start_of_loop))
                    # print(count_of_strike_min)
                print(f'strike for day:{trading_date_str} is :{strike_price}:{option_type}')
                print("time taken e", (millis() - candle_start))

    total_strike_count = sum([len(strike_list) for strike_list in strike_list_by_day])
    print("total_strikes>>>", total_strike_count, len(trading_days_list), len(minute_list),
          (total_strike_count * len(minute_list) * 2), len(df_day_list))

    every_minute_df = pd.DataFrame(
        {'day': df_day_list, 'day_str': df_day_str_list, 'strike_price': df_strike_price_list,
         'strike_ticker_symbol': df_strike_ticker_symbol_list, 'minute': df_minute_list, 'value': df_value_list},
        df_day_list)

    if len(df_day_list) > 0:
        write_pickle_data('every_minute_df', every_minute_df)
    print("done with iteration")


# get all the atm strike (34000) for every day and for every minute combination. Diff from spot price is, it will
# be rounded, also will be grouped by price to avoid duplicate strike price for the same day
def get_all_b_nifty_atm_strikes_by_min(file_name: str):
    df_base_min_list = []
    df_base_day_list = []
    df_base_day_str_list = []
    df_base_india_vix_list = []
    df_base_nifty_spot_price_list = []

    trading_minute_list = get_minute_list('%H:%M:%S', "09:20:00", "14:30:00")
    start = millis()
    nifty_spot_by_min_dic = load_nifty_min_data("BANKNIFTY")
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
            nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_spot_by_min_dic, 'close')
            df_base_nifty_spot_price_list.append(nifty_spot_price)

    nifty_spot_df = pd.DataFrame(
        {'day': df_base_day_list, 'day_str': df_base_day_str_list, 'minute': df_base_min_list,
         "spot": df_base_nifty_spot_price_list},
        df_base_day_list)
    nifty_spot_df = nifty_spot_df[nifty_spot_df.spot != -1]
    print(len(nifty_spot_df.groupby(['day'])))
    nifty_spot_df['r_spot_price'] = nifty_spot_df['spot'].round()
    nifty_spot_df['r_strike_price'] = (nifty_spot_df['r_spot_price']).apply(round_nearest, args=(100,))
    nifty_strike_df = nifty_spot_df[['r_strike_price', 'day']].groupby(['day', 'r_strike_price'])['r_strike_price'].agg(
        ['min', 'max', 'first', 'count'])

    nifty_strike_index_values = nifty_strike_df.index.values
    write_pickle_data(file_name, nifty_strike_index_values)


def store_all_infra_data():
    # india vix data

    # nifty_option_data_files_till_20 = get_all_nifty_weekly_option_files('NIFTY',years)
    # write_pickle_data('nifty_weekly_option_data_files_till_20', nifty_option_data_files_till_20)

    years = ['2019', '2020', '2021', '2022']
    # get premium out of all the files that was downloaded.
    b_nifty_option_data_files_till_20 = get_all_nifty_weekly_option_files('BANKNIFTY', years)
    write_pickle_data('b_nifty_weekly_option_data_files_till_20', b_nifty_option_data_files_till_20)
    # get the india vix data, this will even be used to find the traded days along with vix data.
    store_india_vix_day_data_from_zerodha('india-vix-day-candle', 2019, 2023)
    # get the spot price for every minute
    store_bnifty_min_candle_from_zerodha(f'b-nifty-minute-candle', 2019, 2023)
    # get all the atm strike (34000) for every day and for every minute combination. Diff from spot price is, it will
    # be rounded, also will be grouped by price to avoid duplicate strike price for the same day
    get_all_b_nifty_atm_strikes_by_min('day_strike_index_list')

    # 2022 data
    # nifty_option_data_files_2022 = get_all_nifty_weekly_option_files_for_2022('NIFTY')
    # b_nifty_option_data_files_2022 = get_all_nifty_weekly_option_files_for_2022('BANKNIFTY')
    #
    # write_pickle_data('nifty_weekly_option_data_files_2022', nifty_option_data_files_2022)
    # write_pickle_data('b_nifty_weekly_option_data_files_2022', b_nifty_option_data_files_2022)

    # trading days
    # store_india_vix_data_from_zerodha()
    # store_nifty_trading_data_from_zerodha()
    # store_bnifty_min_candle_from_zerodha()


# store_all_infra_data()

# populating a dataframe with premium data for all the b nifty ticker which has been atm strike at some point. Here
# please note that I am not getting all the ticker but just the ones that will help me with 'straddle' analysis
populate_every_minute_df("2019-01-01", "2022-04-28")
