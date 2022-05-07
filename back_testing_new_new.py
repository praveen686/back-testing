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


# *********** date that are present for india vix but no spot price present for whole day
# ***************** 2019-10-27(weekend) 2020-11-14(weekend) 2021-11-04(weekday)

# *********** date that are present for india vix but no spot price present for some the intervals
# ***************** 2021-02-24 starting from 10:20


# this method is to get the atm ticker symbol associated with each interval 9.20 9.40 etc as LegTrade classes
def get_all_atm_strikes_by_interval():
    strike_count = 0
    df_other_day_list = []
    df_other_day_str_list = []
    df_other_time_intervals = []
    df_other_atm_option_strike_list = []
    atm_strikes_by_interval: Dict[str, List[LegTrade]] = {}

    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    india_vix_day_dic = load_india_vix_day_data()
    trading_days_list = list(india_vix_day_dic.keys())
    # trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    expiry_df = pd.read_csv("expiry_df.csv")
    start_time = millis()
    for ticker_format_trade_date in trading_days_list:
        trading_date_str = ticker_format_trade_date.replace("T00:00:00+0530", "")
        if trading_date_str == "2019-10-27" or trading_date_str == "2020-11-14" or trading_date_str == "2021-11-04" \
                or trading_date_str == "2021-02-24" or trading_date_str >= "2022-03-01":
            print(f'not processing for day :{trading_date_str}')
            continue
        india_vix = round(float(india_vix_day_dic[ticker_format_trade_date]['close']))
        trading_date = get_date_from_str(trading_date_str)
        date_time_in_secs = (trading_date - datetime.datetime(1970, 1, 1)).total_seconds()
        nearest_expiry_date = get_nearest_expiry(trading_date_str, expiry_df)
        instrument_prefix = get_instrument_prefix(get_date_in_str(nearest_expiry_date, constants.DATE_FORMAT),
                                                  "BANKNIFTY")

        for trade_interval in trade_intervals:
            minute_reformatted = f'{trade_interval[0:2]}:{trade_interval[2:4]}:00'
            spot_price = get_nifty_spot_price(trading_date_str, minute_reformatted, nifty_min_data_dic, 'close')
            if spot_price == -1:
                print(f'no spot price present for date:{trading_date_str} and time:{trade_interval}')
                continue
            spot_price_nearest = round_nearest(spot_price, 100)
            for option_type in ["PE", "CE"]:
                strike_count = strike_count + 1
                df_other_day_list.append(date_time_in_secs)
                df_other_day_str_list.append(trading_date_str)
                df_other_time_intervals.append(trade_interval)
                strike_ticker_symbol = f'{instrument_prefix}{spot_price_nearest}{option_type}'
                df_other_atm_option_strike_list.append(strike_ticker_symbol)
                interval_key = f'{strike_ticker_symbol}|{trading_date_str}'
                if interval_key not in atm_strikes_by_interval:
                    atm_strikes_by_interval[interval_key] = [LegTrade(trade_interval, trading_date_str,
                                                                      strike_ticker_symbol, india_vix)]
                else:
                    atm_strikes_by_interval[interval_key].append(LegTrade(trade_interval, trading_date_str,
                                                                          strike_ticker_symbol, india_vix))
        # atm_premium = random.randrange(100, 300, 3)

    print("strike count", strike_count)
    print(f'len of atm_strikes_by_interval:{len(atm_strikes_by_interval)},all strike:{len(df_day_list)}')
    write_pickle_data('atm_strikes_by_interval', atm_strikes_by_interval)
    print("time taken>>>", (millis() - start_time))


# this method is go through atm ticker symbols for each interval and use premium data from every minute data and
# use that to populate LegTrade data
def generate_day_trades_by_interval():
    total_count_of_strikes = 0
    every_minute_df = get_pickle_data('every_minute_df')
    row_entries = every_minute_df.values
    atm_strikes_by_interval_src_list: Dict[str, List[LegTrade]] = get_pickle_data('atm_strikes_by_interval')
    atm_strikes_by_interval_dest_list = []
    start_time = millis()
    # for index, row_entry in enumerate(row_entries):
    all_interval_leg_trades: List[LegTrade] = []
    active_leg_trades: List[LegTrade] = None
    for index, row_entry in enumerate(row_entries):
        if row_entry[4] == "09:15:00":
            total_count_of_strikes = total_count_of_strikes + 1

            leg_trade_strike_key = f'{row_entry[3]}|{row_entry[1]}'  # a combination of symbol and date
            if leg_trade_strike_key in atm_strikes_by_interval_src_list:
                # the way I have set up the datamodel, a key of 'symbol and date' might have multiple
                # atm strikes under it as the same strike would continue as the atm for so long or come back at later
                # point and become atm then
                # for ex: 'BANKNIFTY 22 D 13 34000' might be atm strike at 9:20 till 11:20 or come back at 13:20 and become atm again
                active_leg_trades = atm_strikes_by_interval_src_list[leg_trade_strike_key]
                all_interval_leg_trades.extend(active_leg_trades)
            else:
                active_leg_trades = None
        if active_leg_trades is not None:
            for active_leg_trade in active_leg_trades:
                active_leg_trade.premium_tickers.append(row_entry[5])  # catching premium
    grouped_leg_trade_by_date: List[List[LegTrade]] = [list(g) for k, g in
                                                       groupby(sorted(all_interval_leg_trades,
                                                                      key=lambda xy: xy.straddle_date),
                                                               lambda xy: xy.straddle_date)]

    day_trades: List[DayTrade] = []
    for date_leg_trades in grouped_leg_trade_by_date:
        if len(date_leg_trades) != 30:
            print(f'data not correct for the date :{date_leg_trades[0].straddle_date}')
        leg_pair_time_dic: Dict[str, LegPair] = {}
        # leg_pairs: List[LegPair] = []
        leg_trade_pairs: List[List[LegTrade]] = [list(g) for k, g in
                                                 groupby(
                                                     sorted(date_leg_trades, key=lambda xy: xy.straddle_time),
                                                     lambda xy: xy.straddle_time)]
        for leg_trade_pair in leg_trade_pairs:
            leg_pair: LegPair = LegPair(leg_trade_pair[0].straddle_time, leg_trade_pair[0], leg_trade_pair[1])
            leg_pair_time_dic[leg_trade_pair[0].straddle_time] = leg_pair
            # leg_pairs.append(leg_pair)
        day_trades.append(DayTrade(leg_pair_time_dic, date_leg_trades[0].straddle_date, date_leg_trades[0].india_vix))

    write_pickle_data("day_trades", day_trades)
    # print(x_temp, total_count_of_strikes)
    # print(len(atm_strikes_by_interval_dest_list))
    print(millis() - start_time)


class LegTrade:
    def __init__(self, straddle_time: str, trade_date: str, ticker_symbol: str, india_vix: int):
        self.straddle_time: str = straddle_time
        self.straddle_date: str = trade_date
        self.ticker_symbol = ticker_symbol
        self.premium_tickers = []
        self.valid_prem_tickers = []
        self.profit_by_time = []
        self.is_sl_hit = False
        self.sl_hit_index: int = None
        self.india_vix = india_vix

    def walk(self, minute_index, start_index, sl: float):
        start_time = millis()
        if minute_index >= start_index:
            ticker_premium = self.premium_tickers[minute_index]
            if ticker_premium == ticker_premium:
                self.valid_prem_tickers.append(ticker_premium)

        # print("wee", millis() - start_time)
        if len(self.valid_prem_tickers) == 0:
            self.profit_by_time.append(0)
        else:
            if self.is_sl_hit is False:
                curr_profit = round(float(self.valid_prem_tickers[0]) - float(self.valid_prem_tickers[-1]), 2)
                if curr_profit < sl * float(self.valid_prem_tickers[0]) * -1:
                    self.is_sl_hit = True
                    self.sl_hit_index = minute_index
            else:
                # getting the previous profit to append in case sl is met already
                curr_profit = self.profit_by_time[-1]
            self.profit_by_time.append(curr_profit)
        # print("wee", millis() - start_time)

    def get_profit(self, minute_index: int):
        profit = self.profit_by_time[minute_index]
        return profit
        # print(self.profit_by_time)


class LegPair:
    # minutes_till_0915 = (9 * 60) + 15

    def __init__(self, start_time_str: str, pe_leg_trade: LegTrade, ce_leg_trade: LegTrade):
        # self.start_time_str = start_time_str
        # start_hour_part = int(start_time_str[:2])
        # start_min_part = int(start_time_str[2:])
        # start_min = (start_hour_part * 60) + start_min_part
        # self.start_min_index = (start_min - LegPair.minutes_till_0915) - 1
        self.pe_leg: LegTrade = pe_leg_trade
        self.ce_leg: LegTrade = ce_leg_trade
        # below values will be set based on the straddle chosen time
        self.selected_straddle_time: str = None
        self.start_min_index = None

    def walk_leg(self, minute_index, sl: float):
        self.pe_leg.walk(minute_index, self.start_min_index, sl)
        self.ce_leg.walk(minute_index, self.start_min_index, sl)

    def get_profit(self, minute_index=-1):
        return self.pe_leg.get_profit(minute_index) + self.ce_leg.get_profit(minute_index)


class DayTrade:
    def __init__(self, leg_pair_dic: Dict[str, LegPair], trade_date_str: str, india_vix: int):
        self.leg_pair_dic: Dict[str, LegPair] = leg_pair_dic
        self.trade_date_str: str = trade_date_str
        self.filtered_leg_pairs_by_time: [LegPair] = None
        self.india_vix = india_vix

    def set_leg_pairs_by_straddle_times(self, straddle_times: List[str]):
        self.filtered_leg_pairs_by_time = []
        for straddle_time in straddle_times:
            if straddle_time in self.leg_pair_dic:
                leg_pair = self.leg_pair_dic[straddle_time]
                leg_pair.selected_straddle_time = straddle_time
                leg_pair.start_min_index = get_start_minute_index(straddle_time)
                self.filtered_leg_pairs_by_time.append(leg_pair)
            else:
                print("x")

    def walk(self, minute_index, sl: float):
        for leg_pair in self.filtered_leg_pairs_by_time:
            leg_pair.walk_leg(minute_index, sl)

    def get_profit(self):
        total_profit = sum([leg_pair.get_profit() for leg_pair in self.filtered_leg_pairs_by_time])
        return total_profit


def get_start_minute_index(start_time_str: str):
    minutes_till_0915 = (9 * 60) + 15
    start_hour_part = int(start_time_str[:2])
    start_min_part = int(start_time_str[2:])
    start_min = (start_hour_part * 60) + start_min_part
    start_min_index = (start_min - minutes_till_0915)
    return start_min_index


def analyze_interval_trades(straddle_times: List[str]):
    # analyze_profit("2019-02-18", "2019-02-19", sl=.6, target_profit=-1, day_trailing_sl=20, week_day=-1)
    analyze_start_time = millis()
    day_trades: List[DayTrade] = get_pickle_data("day_trades")
    # 2019-10-27
    day_trades = [day_trade for day_trade in day_trades if '2019-02-18' <= day_trade.trade_date_str <= "2022-02-11"]
    # day_trades = [day_trade for day_trade in day_trades if '2019-10-27' <= day_trade.trade_date_str <= "2019-10-27"]
    # filter(lambda x: '2019-02-18' <= x.trade_date_str <= "2022-02-14", day_trades))
    total_profit = 0
    trading_minute_list = get_minute_list('%H:%M:%S', "09:15:00", "14:30:00")
    profit_tracker: List[{}] = []
    for day_trade in day_trades:
        if day_trade.india_vix > 50:
            continue
        # start_time = millis()
        day_trade.set_leg_pairs_by_straddle_times(straddle_times)
        for minute_index in range(len(trading_minute_list)):
            day_trade.walk(minute_index, .6)
        day_profit = round(day_trade.get_profit(), 2)
        print(f'{day_trade.trade_date_str},{day_profit}')
        total_profit = total_profit + day_profit
        profit_tracker.append({"profit": day_profit, "date": day_trade.trade_date_str})

    print(total_profit, (millis() - analyze_start_time))

    win_days = [day_profit["profit"] for day_profit in profit_tracker if day_profit["profit"] > 0]
    loss_days = [day_profit["profit"] for day_profit in profit_tracker if day_profit["profit"] < 0]
    # loss_days_with_pos_profit = [day_profit for day_profit in loss_days if max(day_profit.profit_list) > 20]
    # hello.to_clipboard()
    mean_profit = mean_loss = None
    if len(win_days) > 0:
        mean_profit = sum(win_days) / len(win_days)
    if len(loss_days) > 0:
        mean_loss = sum(loss_days) / len(loss_days)
    if mean_profit is not None and mean_loss is not None:
        print(
            f'total profit:{total_profit} win:{len(win_days)},loss:{len(loss_days)},ratio:{round(len(win_days) / len(loss_days), 2)}, win mean:{round(mean_profit, 2)}'
            f',mean loss:{round(mean_loss, 2)} ,rr:{round(mean_profit / mean_loss, 2)}')


def generate_leg_trade():
    leg_trade_dic: Dict[str, LegTrade] = {}
    every_minute_df = get_pickle_data('every_minute_df')
    row_entries = every_minute_df.values
    for row_entry in row_entries:
        leg_trade_key = None


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


# get_all_atm_strikes_by_interval()
# generate_day_trades_by_interval()
analyze_interval_trades(["0920"])
