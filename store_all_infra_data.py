import datetime
from typing import List

import pandas as pd
import numpy as np

import constants
from back_testing_new_new import LegTrade
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

    minute_list = get_minute_list('%H:%M:%S', constants.EXCHANGE_START_TIME, constants.EXCHANGE_END_TIME)
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
        candle_start = millis()
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
                spot_price = get_nifty_spot_price(trading_date_str, "09:20:00", nifty_min_data_dic, 'close')
                strike_ticker_candles_for_trade_date_dic, expiry_date_str, ticker_prefix, ticker_file_name = \
                    get_ticker_data_by_expiry_and_strike(
                        strike_price, nearest_expiry_date, option_type, trade_date_in_option_format,
                        weekly_option_data_files, "BANKNIFTY")
                if len(strike_ticker_candles_for_trade_date_dic) == 0:
                    print(
                        f'strike ticker not present for {trading_date_str} ticker:{ticker_file_name} spot:{spot_price}')
                    continue
                # print("time taken s", (millis() - candle_start))
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
                    df_nifty_spot_price_list.append(nifty_spot_price)

                    day_ticker_symbols.append(strike_ticker_symbol)
                    count_of_strike_min = count_of_strike_min + 1
                    # print("time taken each minute>>>>", (millis() - candle_start), (millis() - start_of_loop))
                    # print(count_of_strike_min)
        print(f'strike for day:{trading_date_str}')
        print("time taken e", (millis() - candle_start))

    total_strike_count = sum([len(strike_list) for strike_list in strike_list_by_day])
    print("total_strikes>>>", total_strike_count, len(trading_days_list), len(minute_list),
          (total_strike_count * len(minute_list) * 2), len(df_day_list))

    option_strike_minute_ticker_df = pd.DataFrame(
        {'day': df_day_list, 'day_str': df_day_str_list, 'strike_price': df_strike_price_list,
         'strike_ticker_symbol': df_strike_ticker_symbol_list, 'minute': df_minute_list, 'value': df_value_list},
        df_day_list)

    if len(df_day_list) > 0:
        write_pickle_data('option_strike_minute_ticker_df', option_strike_minute_ticker_df)
    print("done with iteration")


def get_nearest_strikes_by_range(strike: int, offset_range: int, unit: int):
    strikes_with_offset = []
    for i in range(offset_range):
        positive_offset = ((i + 1) * unit)
        negative_offset = ((i + 1) * unit * -1)
        strikes_with_offset.append({"strike": positive_offset + strike, "offset": positive_offset})
        strikes_with_offset.append({"strike": negative_offset + strike, "offset": negative_offset})
    return strikes_with_offset


# get all the atm strike (34000) for every day and for every minute combination. Diff from spot price is, it will
# be rounded, also will be grouped by price to avoid duplicate strike price for the same day
def get_all_b_nifty_atm_strikes_by_min(file_name: str, leg_trade_file_name: str, end_date: str):
    df_base_min_list = []
    df_base_day_list = []
    df_base_day_str_list = []
    df_base_offset_list = []
    df_base_india_vix_list = []
    df_base_nifty_strike_price_list = []
    df_base_spot_price_list = []

    trading_minute_list = get_minute_list('%H:%M:%S', constants.EXCHANGE_START_TIME, constants.EXCHANGE_END_TIME)
    start = millis()
    nifty_spot_by_min_dic = load_nifty_min_data("BANKNIFTY")
    print(f'time:{millis() - start}')
    india_vix_day_dic = load_india_vix_day_data()
    print(f'time:{millis() - start}')
    trading_days_list = list(india_vix_day_dic.keys())
    print(f'time:{millis() - start}')
    trading_days_list = list(india_vix_day_dic.keys())
    # trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    expiry_df = pd.read_csv("expiry_df.csv")
    day_ticker_dic = {}
    for ticker_format_trade_date in trading_days_list:
        trading_date_str = ticker_format_trade_date.replace("T00:00:00+0530", "")
        if trading_date_str > end_date:
            break
        india_vix = round(float(india_vix_day_dic[ticker_format_trade_date]['close']))
        trading_date = get_date_from_str(trading_date_str)
        # day_time = start_time + (day * 86400000)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        nearest_expiry_date = get_nearest_expiry(trading_date_str, expiry_df)
        instrument_prefix = get_instrument_prefix(get_date_in_str(nearest_expiry_date, constants.DATE_FORMAT),
                                                  "BANKNIFTY")
        for minute in trading_minute_list:
            nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_spot_by_min_dic, 'close')
            nifty_spot_price = round(nifty_spot_price)
            nifty_strike_price = round_nearest(nifty_spot_price, 100)
            nearest_strikes = get_nearest_strikes_by_range(nifty_strike_price, 10, 100)
            nearest_strikes.append({"strike": nifty_strike_price, "offset": 0})
            # nearest_strikes = [nifty_strike_price]
            for strike_price in nearest_strikes:
                df_base_min_list.append(minute)
                df_base_day_list.append(date_time_in_secs)
                df_base_day_str_list.append(trading_date_str)
                df_base_nifty_strike_price_list.append(strike_price["strike"])
                df_base_offset_list.append(strike_price["offset"])
                df_base_spot_price_list.append(nifty_spot_price)
                df_base_india_vix_list.append(india_vix)
                for option_type in ["PE", "CE"]:
                    strike_ticker_symbol = f'{instrument_prefix}{strike_price["strike"]}{option_type}'
                    day_ticker_key = f'{trading_date_str}|{strike_ticker_symbol}'
                    if day_ticker_key in day_ticker_dic:
                        leg_trade = day_ticker_dic[day_ticker_key]
                        leg_trade.atm_minutes.append(f'{minute}|{strike_price["offset"]}')
                    else:
                        leg_trade = LegTrade(trading_date_str, strike_ticker_symbol,
                                             india_vix, nifty_spot_price, option_type)
                        leg_trade.atm_minutes.append(f'{minute}|{strike_price["offset"]}')
                        day_ticker_dic[day_ticker_key] = leg_trade
        print(">>>>", trading_date_str)
    nifty_strike_price_df = pd.DataFrame(
        {'day': df_base_day_list, 'day_str': df_base_day_str_list, 'minute': df_base_min_list,
         "strike": df_base_nifty_strike_price_list},
        df_base_day_list)

    nifty_strike_price_df = nifty_strike_price_df[nifty_strike_price_df.strike != -1]
    print(len(nifty_strike_price_df.groupby(['day'])))
    # nifty_spot_df['r_spot_price'] = nifty_spot_df['spot'].round()
    # nifty_spot_df['r_strike_price'] = (nifty_spot_df['r_spot_price']).apply(round_nearest, args=(100,))
    nifty_unique_strike_price_df = nifty_strike_price_df[['strike', 'day']].groupby(['day', 'strike'])['strike'].agg(
        ['min', 'count'])

    nifty_strike_index_values = nifty_unique_strike_price_df.index.values
    write_pickle_data(file_name, nifty_strike_index_values)
    write_pickle_data(leg_trade_file_name, day_ticker_dic)


def store_all_infra_data(get_option_files: bool, store_vix: bool, store_nifty_min_candle: bool,
                         store_strike_symbols: bool,
                         populate_strike_premium: bool):
    years = ['2019', '2020', '2021', '2022']
    if get_option_files:
        # get premium out of all the files that was downloaded.
        b_nifty_option_data_files_till_20 = get_all_nifty_weekly_option_files('BANKNIFTY', years)
        write_pickle_data('b_nifty_weekly_option_data_files_till_20', b_nifty_option_data_files_till_20)
    if store_vix:
        # get the india vix data, this will even be used to find the traded days along with vix data.
        store_india_vix_day_data_from_zerodha('india-vix-day-candle', 2019, 2023)
    if store_nifty_min_candle:
        # get the spot price for every minute
        store_bnifty_min_candle_from_zerodha(f'b-nifty-minute-candle', 2019, 2023)
    if store_strike_symbols:
        # get all the atm strike (34000) for every day and for every minute combination. Diff from spot price is, it will
        # be rounded, also will be grouped by price to avoid duplicate strike price for the same day
        get_all_b_nifty_atm_strikes_by_min('day_strike_index_list', 'leg_trades_by_date_strike_n_offset', "2022-04-28")
    if populate_strike_premium:
        # populating a dataframe with premium data for all the b nifty ticker which has been atm strike at some point. Here
        # please note that I am not getting all the ticker but just the ones that will help me with 'straddle' analysis
        populate_every_minute_df("2019-02-18", "2022-04-28")


store_all_infra_data(get_option_files=False, store_vix=False, store_nifty_min_candle=False, store_strike_symbols=False,
                     populate_strike_premium=True)
