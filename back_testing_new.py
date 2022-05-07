import datetime
import random
from itertools import groupby
from typing import List, Dict

import numpy as np
import pandas as pd

import constants
from option_util import get_minute_list, millis, load_nifty_min_data, load_india_vix_day_data, get_nifty_spot_price, \
    get_nearest_thursday, get_india_vix, round_nearest, get_nearest_expiry, get_instrument_prefix, \
    get_ticker_data_by_expiry_and_strike
from util import get_pickle_data, write_pickle_data, get_date_from_str, get_date_in_str

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
df_base_nifty_spot_price_list = []

df_minute_list = []
df_day_list = []
df_day_str_list = []
df_strike_price_list = []
df_strike_ticker_symbol_list = []
df_value_list = []
df_index_list = []
df_nifty_spot_price_list = []


def populate_list():
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
        day_spot_price_list = []
        day_ticker_symbols = []
        trading_date = get_date_from_str(trading_date_str)
        # day_time = start_time + (day * 86400000)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        strike_list = get_strikes_by_day(day_strike_index_list, date_time_in_secs)
        strike_list_by_day.append(strike_list)
        nearest_expiry_date = get_nearest_expiry(trading_date_str, expiry_df)
        instrument_prefix = get_instrument_prefix(get_date_in_str(nearest_expiry_date, constants.DATE_FORMAT),
                                                  "BANKNIFTY")
        for minute in minute_list:
            df_base_min_list.append(minute)
            df_base_day_list.append(date_time_in_secs)
            df_base_day_str_list.append(trading_date_str)
            df_base_india_vix_list.append(get_india_vix(trading_date_str, india_vix_day_dic))
            nifty_spot_price = get_nifty_spot_price(trading_date_str, minute, nifty_min_data_dic, 'close')
            df_base_nifty_spot_price_list.append(nifty_spot_price)
            day_spot_price_list.append(nifty_spot_price)
        #     get strike for the day
        start_of_loop = millis()

        # for strike_price in strike_list:
        for strike_price in []:
            # strike_ticker_pe_symbol = generate_ticker_symbol(nearest_expiry_date, strike_price, "PE")
            # strike_ticker_ce_symbol = generate_ticker_symbol(nearest_expiry_date, strike_price, "CE")
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
                # for minute_key in strike_ticker_candles_for_trade_date_dic:
                #     nifty_spot_price = get_nifty_spot_price(trading_date_str, minute_key, nifty_min_data_dic, 'close')
                #
                #     # print(random.randrange(100, 300, 3))
                #     df_value_list.append(strike_ticker_candles_for_trade_date_dic[minute_key]['close'])
                #     df_day_list.append(date_time_in_secs)
                #     df_day_str_list.append(trading_date_str)
                #     df_strike_price_list.append(strike_price)
                #     df_strike_ticker_symbol_list.append(strike_ticker_symbol)
                #     df_minute_list.append(minute_key)
                #     df_index_list.append(count_of_strike_min)
                #     df_nifty_spot_price_list.append(round_nearest(nifty_spot_price, 100))
                #
                #     day_ticker_symbols.append(strike_ticker_symbol)
                #     count_of_strike_min = count_of_strike_min + 1
                #     # print("time taken each minute>>>>", (millis() - candle_start), (millis() - start_of_loop))
                #     print(count_of_strike_min)
        # for trade_interval in []:
        # every_minute_df = get_pickle_data("every_minute_df")
        # every_min_values = every_minute_df.values
        # df_day_list = every_minute_df.day.values
        # df_strike_ticker_symbol_list = every_minute_df.strike_ticker_symbol.values
        # value_length = len(every_min_values)
        # for trade_interval in trade_intervals:
        #     minute_reformatted = f'{trade_interval[0:2]}:{trade_interval[2:4]}:00'
        #     spot_price = get_nifty_spot_price(trading_date_str, minute_reformatted, nifty_min_data_dic, 'close')
        #     spot_price_nearest = round_nearest(spot_price, 100)
        #     for option_type in ["PE", "CE"]:
        #         # atm_premium = random.randrange(100, 300, 3)
        #         df_other_day_list.append(date_time_in_secs)
        #         df_other_day_str_list.append(trading_date_str)
        #         df_other_time_intervals.append(trade_interval)
        #         strike_ticker_symbol = f'{instrument_prefix}{spot_price_nearest}{option_type}'
        #         df_other_atm_option_strike_list.append(strike_ticker_symbol)
        #         hello = every_minute_df.loc[(every_minute_df.index == date_time_in_secs) & (
        #                 every_minute_df.strike_ticker_symbol == strike_ticker_symbol)]
        #         # index_strike_ticker = [index for index in range(value_length) if
        #         #                        every_min_values[index][0] == date_time_in_secs and every_min_values[index][
        #         #                            3] == strike_ticker_symbol]
        #
        #         # print("index strike ticker", index_strike_ticker[0])
        #         # if len([]) == 0:
        #         #     print("candle dic empty", strike_ticker_symbol, trading_date_str, option_type, trade_interval)
        #         # df_other_index_strike_ticker.append(index_strike_ticker[0] if len(index_strike_ticker) > 0 else -1)
        #
        #         # df_other_atm_premium_list.append(atm_premium)
        #         df_other_option_type_list.append(option_type)
        #     print("done for the interval", trading_date_str, trade_interval)

    total_strike_count = sum([len(strike_list) for strike_list in strike_list_by_day])
    print("total_strikes>>>", total_strike_count, len(trading_days_list), len(minute_list),
          (total_strike_count * len(minute_list) * 2), len(df_day_list))
    base_minute_df = pd.DataFrame(
        {'day': df_base_day_list, 'day_str': df_base_day_str_list, 'minute': df_base_min_list,
         "vix": df_base_india_vix_list, "spot": df_base_nifty_spot_price_list},
        df_base_day_list)

    every_minute_df = pd.DataFrame(
        {'day': df_day_list, 'day_str': df_day_str_list, 'strike_price': df_strike_price_list,
         'strike_ticker_symbol': df_strike_ticker_symbol_list, 'minute': df_minute_list, 'value': df_value_list},
        df_day_list)

    # all_atm_df = pd.DataFrame(
    #     {'day': df_other_day_list, 'day_str': df_other_day_str_list, 'interval': df_other_time_intervals,
    #      'atm_option_strike': df_other_atm_option_strike_list, "option_type": df_other_option_type_list,
    #      'index_strike_ticker': df_other_index_strike_ticker},
    #     df_other_day_list)

    if len(df_day_list) > 0:
        write_pickle_data('every_minute_df', every_minute_df)

    if len(df_base_day_list) > 0:
        write_pickle_data('base_minute_df', base_minute_df)
    print("done with iteration")


def test_looping():
    every_minute_df = get_pickle_data('every_minute_df')
    start = millis()
    values = every_minute_df.values
    for value in values:
        x = 3
    print('time', millis() - start)


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
    _0920_pe_strike_df = pd.merge(all_strike_df, df_only_9_20_pe[['day', 'atm_option_strike']], how='inner',
                                  left_on=['day', 'strike_ticker_symbol'],
                                  right_on=['day', 'atm_option_strike'])
    _0920_ce_strike_df = pd.merge(all_strike_df, df_only_9_20_ce[['day', 'atm_option_strike']], how='inner',
                                  left_on=['day', 'strike_ticker_symbol'],
                                  right_on=['day', 'atm_option_strike'])
    print(f'time after getting 920 strike ticker:{millis() - start}')
    print(len(_0920_ce_strike_df), len(_0920_pe_strike_df))
    # write_pickle_data('_0920_pe_strike_df', _0920_pe_strike_df)
    # write_pickle_data('_0920_ce_strike_df', _0920_ce_strike_df)
    _0920_straddle_df = pd.merge(base_minute_df,
                                 _0920_pe_strike_df[['day', 'minute', 'strike_price', 'value', 'strike_ticker_symbol']],
                                 how='left', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'])
    _0920_straddle_df = pd.merge(_0920_straddle_df,
                                 _0920_ce_strike_df[['day', 'minute', 'strike_price', 'value', 'strike_ticker_symbol']],
                                 how='left', left_on=['day', 'minute'],
                                 right_on=['day', 'minute'], suffixes=('_pe', '_ce'))
    print(len(_0920_straddle_df), len(_0920_straddle_df))
    print(f'time after merging strike ticker to base:{millis() - start}')
    # df_0920_atm_strike.to_csv("df_0920.csv")
    write_pickle_data('_0920_straddle_df', _0920_straddle_df)
    print(f'time before loop:{millis() - start}')

    # print()
    print(f'time:{millis() - start}')
    # merge = pd.merge(trade_df_list[0], trade_df_list[1], how='inner', left_index=True, right_index=True)


def test_all_strike_df_perf():
    all_strike_df = get_pickle_data('every_minute_df')
    start_time = millis()
    all_values = all_strike_df.values
    for all in all_values:
        x = all
    print((millis() - start_time))


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


class LegProfit:
    def __init__(self):
        # self.start_premium = None
        # self.profit_list = []
        self.minutes = []
        self.premium_list = []
        self.is_sl_hit = False

    def get_profit(self):
        if len(self.premium_list) > 0:
            profit = float(self.premium_list[0]) - float(self.premium_list[-1])
        else:
            profit = 0
        return profit

    def check_sl(self, sl: float):
        if len(self.premium_list) > 0:
            sl_value = float(self.premium_list[0]) * sl * -1
            if self.get_profit() < sl_value:
                self.is_sl_hit = True


class DayProfit:

    def __init__(self):
        self.pe_leg: LegProfit = None
        self.ce_leg: LegProfit = None
        self.profit = None
        self.date_str = None
        self.profit_list = []
        self.is_target_profit_reached = False
        self.is_trailing_sl_hit = False
        self.week_day = -1

    def get_profit(self):
        return self.pe_leg.get_profit() + self.ce_leg.get_profit()

    def append_leg_profit(self, leg_profit: LegProfit, curr_premium: float, minute: str, sl: float):
        if leg_profit.is_sl_hit:
            return
        if curr_premium == curr_premium:
            leg_profit.premium_list.append(curr_premium)
            leg_profit.minutes.append(minute)
            leg_profit.check_sl(sl)
        else:
            return False


def analyze_profit(start_date: str, end_date: str, sl: float, target_profit: int, day_trailing_sl: int, week_day: int):
    start_analyze_time = millis()

    _0920_straddle_df = get_pickle_data("_0920_straddle_df")
    values = _0920_straddle_df.values
    print("fetching file", (millis() - start_analyze_time))
    day_profit_dic = {}
    day_profit_list: [DayProfit] = []
    curr_day_profit: DayProfit = None
    nan_count = 0
    index_start_date = [row[1] for row in values].index(start_date)
    index_end_date = [row[1] for row in values].index(end_date)
    start_minute = "09:20:00"
    end_minute = "14:30:00"
    for i in range(index_start_date, index_end_date):

        ticker_row = values[i]
        date_time = ticker_row[0]
        ticker_minute = ticker_row[2]
        date_str = ticker_row[1]

        india_vix = ticker_row[3]
        pe_ticker_symbol = ticker_row[7]
        ce_ticker_symbol = ticker_row[10]
        if ticker_minute < start_minute or ticker_minute > end_minute:
            continue
        if india_vix >= 50:
            continue
        pe_premium = ticker_row[6]
        ce_premium = ticker_row[9]

        if date_time not in day_profit_dic:
            curr_day_profit = DayProfit()
            date_obj = get_date_from_str(date_str, constants.DATE_FORMAT)
            curr_day_profit.week_day = date_obj.weekday()
            curr_day_profit.date_str = date_str

            pe_leg = LegProfit()
            curr_day_profit.pe_leg = pe_leg

            ce_leg = LegProfit()
            curr_day_profit.ce_leg = ce_leg

            day_profit_list.append(curr_day_profit)
            day_profit_dic[date_time] = 1

        # this is for implementing trailing sl scenario
        if curr_day_profit.is_trailing_sl_hit:
            continue
        # if True:
        #     continue
        pe_leg = curr_day_profit.pe_leg
        append_status = curr_day_profit.append_leg_profit(pe_leg, pe_premium, ticker_minute, sl)
        if append_status is False:
            nan_count = nan_count + 1

        ce_leg = curr_day_profit.ce_leg
        append_status = curr_day_profit.append_leg_profit(ce_leg, ce_premium, ticker_minute, sl)
        if append_status is False:
            nan_count = nan_count + 1

        # checking for day trailing.
        curr_day_profit_val = curr_day_profit.get_profit()
        if target_profit != -1:
            if curr_day_profit_val > target_profit:
                curr_day_profit.is_target_profit_reached = True
            if curr_day_profit.is_target_profit_reached:
                if curr_day_profit_val < day_trailing_sl:
                    curr_day_profit.is_trailing_sl_hit = True
        curr_day_profit.profit_list.append(curr_day_profit.get_profit())

    if week_day != -1:
        day_profit_list = [day_profit for day_profit in day_profit_list if day_profit.week_day == week_day]

    print("time taken>>", (millis() - start_analyze_time), len(day_profit_list),
          sum([round(day_profit.get_profit(), 2) for day_profit in day_profit_list]))
    for day_profit in day_profit_list:
        print(f'{day_profit.date_str},{round(day_profit.get_profit(), 2)}')
    # hello = pd.DataFrame({"profit": [round(day_profit.get_profit(), 2) for day_profit in day_profit_list]},
    #                      [i for i in range(len(day_profit_list))])

    loss_days = [day_profit for day_profit in day_profit_list if day_profit.get_profit() < 0]
    win_days = [day_profit for day_profit in day_profit_list if day_profit.get_profit() > 0]
    # loss_days_with_pos_profit = [day_profit for day_profit in loss_days if max(day_profit.profit_list) > 20]
    # hello.to_clipboard()
    mean_profit = mean_loss = None
    if len(win_days) > 0:
        mean_profit = sum([day_profit.get_profit() for day_profit in win_days]) / len(win_days)
    if len(loss_days) > 0:
        mean_loss = sum([day_profit.get_profit() for day_profit in loss_days]) / len(loss_days)
    if mean_profit is not None and mean_loss is not None:
        print(
            f'win:{len(win_days)},loss:{len(loss_days)},ratio:{round(len(win_days) / len(loss_days), 2)}, win mean:{round(mean_profit, 2)}'
            f',mean loss:{round(mean_loss, 2)} ,rr:{round(mean_profit / mean_loss, 2)}')

    print("nan_count", nan_count, (millis() - start_analyze_time))


# test_data()
# get_all_atm_strikes_by_interval()
# generate_day_trades_by_interval()
# analyze_interval_trades("0920")
# populate_list()
# new_test_data()
# test_all_strike_df_perf()
# analyze_profit("2019-02-18", "2019-02-19", sl=.6, target_profit=-1, day_trailing_sl=20, week_day=-1)
# analyze_profit("2020-01-01", "2020-12-31", sl=.6, target_profit=40, day_trailing_sl=20, week_day=-1)
# analyze_profit("2021-01-01", "2021-12-31", sl=.6, target_profit=40, day_trailing_sl=20, week_day=-1)
analyze_profit("2019-02-18", "2022-02-14", sl=.6, target_profit=-1, day_trailing_sl=20, week_day=-1)
# test_looping()
# get_all_nifty_strikes()
# print(len(minute_list))
# get_nearest_thursday()
# print("done!!!", random.random())
