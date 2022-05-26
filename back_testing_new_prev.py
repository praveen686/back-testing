import datetime
import random
from itertools import groupby
from typing import List, Dict

import pandas as pd

import constants
from option_util import get_minute_list, millis, load_nifty_min_data, load_india_vix_day_data, get_nifty_spot_price, \
    get_nearest_thursday, get_india_vix, round_nearest, get_nearest_expiry, get_instrument_prefix, \
    get_ticker_data_by_expiry_and_strike
from store_ticker_data_from_zerodha import store_india_vix_day_data_from_zerodha
from util import get_pickle_data, write_pickle_data, get_date_from_str, get_date_in_str

vix_data_dic = get_pickle_data('india-vix-day-candle')
day_keys = list(vix_data_dic.keys())
# print(len(strike_prices) * len(day_keys) * len(minute_list))
# print(len(strike_prices), len(day_keys), len(minute_list))
trade_intervals = ["0920", "0940", "1000", "1020", "1040",
                   "1100", "1120", "1140", "1200", "1220", "1240", "1300", "1320", "1340", "1400"]


# *********** date that are present for india vix but no spot price present for whole day
# ***************** 2019-10-27(weekend) 2020-11-14(weekend) 2021-11-04(weekday)

# *********** date that are present for india vix but no spot price present for some the intervals
# ***************** 2021-02-24 starting from 10:20


# 1.get the atm ticker symbol associated with each interval 9.20 9.40 etc.
# 2.create a dic with key as the combination of ticker and trading date and value as LegTrade (without premium)
def get_all_atm_strikes_by_interval(start_date: str, end_date: str):
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
                or trading_date_str == "2021-02-24":
            print(f'not processing for day :{trading_date_str}')
            continue
        if trading_date_str < start_date or trading_date_str > end_date:
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
                # same strike my repeat in a day as the strike which was atm at 9.30 migh continue being atm till 11 or
                # might go up/down and come back to become atm at 11
                if interval_key not in atm_strikes_by_interval:
                    atm_strikes_by_interval[interval_key] = [LegTrade(trade_interval, trading_date_str,
                                                                      strike_ticker_symbol, india_vix)]
                else:
                    atm_strikes_by_interval[interval_key].append(LegTrade(trade_interval, trading_date_str,
                                                                          strike_ticker_symbol, india_vix))
        # atm_premium = random.randrange(100, 300, 3)

    print("strike count", strike_count)
    print(f'len of atm_strikes_by_interval:{len(atm_strikes_by_interval)}')
    write_pickle_data('atm_strikes_by_interval', atm_strikes_by_interval)
    print(sum([len(atm_strikes_by_interval[key]) for key in atm_strikes_by_interval]))
    print("time taken>>>", (millis() - start_time))


# def generate_leg_trade_for_every_minute():
#     day_strike_index_list = get_pickle_data("day_strike_index_list")
#     strikes = [entry[1] for entry in day_strike_index_list if "day" == entry[0]]


# this method is go through atm ticker symbols for each interval and use premium data from every minute data and
# use that to populate LegTrade data
# this method essentially does the population of LegTrade Object that I had earlier using atm strike for each interval
# 1.go through every minute data for all the atm strike (check for 09:15 minute as this is start minute)
# 1.1 check whether current strike is present the atm strike list that I had earlier prepared for the day, for ex: BANKNIFTY22D1334000PE|2022-05-31 (might be for 09:40) will be the key
# 1.1.1 if present get the LegTrade from 'atm strike list' and populate the premiums
# 2 group the final list of 'LegTrade' and group it based on day first to get the DayTrade and then based on Straddle Time to form the 'LegPair'
def generate_day_trades_by_interval():
    total_count_of_strikes = 0
    every_minute_df = get_pickle_data('every_minute_df')
    # this has all the entries for all the symbols
    row_entries = every_minute_df.values
    atm_strikes_by_interval_src_list: Dict[str, List[LegTrade]] = get_pickle_data('atm_strikes_by_interval')
    atm_strikes_by_interval_dest_list = []
    start_time = millis()
    # for index, row_entry in enumerate(row_entries):
    all_interval_leg_trades: List[LegTrade] = []
    active_leg_trades: List[LegTrade] = None
    for index, row_entry in enumerate(row_entries):
        # whenever 9:15 is reached, will append the premium to a new LegTrade fetched from 'atm_strikes_by_interval'
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

    # loop through
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
        self.is_c2c_set = False

    def walk(self, minute_index, start_index, sl: float):
        start_time = millis()
        # if the interval time hasnt reached.
        if minute_index >= start_index:
            ticker_premium = self.premium_tickers[minute_index]
            # this is to check whether its not nan
            if ticker_premium == ticker_premium:
                self.valid_prem_tickers.append(ticker_premium)

        # print("wee", millis() - start_time)
        # appending profit to the profit tracker, it will be 0 if no valid premium present so far.
        if len(self.valid_prem_tickers) == 0:
            self.profit_by_time.append(0)
        else:
            curr_premium = float(self.valid_prem_tickers[-1])
            if self.is_sl_hit is False:
                curr_profit = round(float(self.valid_prem_tickers[0]) - curr_premium, 2)
                # check for sl only if its enabled
                if sl != -1:
                    # if curr_profit < (sl * float(self.valid_prem_tickers[0])) * -1:
                    if curr_premium > (sl * float(self.valid_prem_tickers[0])):
                        self.is_sl_hit = True
                        self.sl_hit_index = minute_index
            else:
                # getting the previous profit to append in case sl is met already
                curr_profit = self.profit_by_time[-1]
            # this tracks the profit, profit till that minute
            self.profit_by_time.append(curr_profit)
        # print("wee", millis() - start_time)

    def set_sl(self, sl_status: bool):
        self.is_sl_hit = sl_status

    # get the profit upto the minute passed
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
        # this is to try trailing sl per pair
        self.target_min_profit_perc_reached = False
        # this will be only set once target profit has reached.
        self.curr_trailing_sl_profit = -1
        self.pair_profit_tracker = []
        self.is_pair_sl_set = False

    def walk_leg(self, minute_index, sl: float, is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float):
        self.pe_leg.walk(minute_index, self.start_min_index, 1 if self.pe_leg.is_c2c_set else sl)
        self.ce_leg.walk(minute_index, self.start_min_index, 1 if self.ce_leg.is_c2c_set else sl)
        profit_so_far = self.pe_leg.get_profit(minute_index) + self.ce_leg.get_profit(minute_index)
        start_premium = \
            sorted([self.pe_leg.premium_tickers[0], self.ce_leg.premium_tickers[0]], key=lambda x: float(x))[0]
        if min_profit_perc != -1 and profit_so_far >= min_profit_perc * float(start_premium):
            self.target_min_profit_perc_reached = True
            self.curr_trailing_sl_profit = profit_so_far * trailing_sl_perc
        self.pair_profit_tracker.append(profit_so_far)
        # idea is to check whether we have reached target perc of the smallest premium in the leg
        if self.target_min_profit_perc_reached:
            # after you have reached min profit and gone beyond, if it goes less than trailing sl profit exit
            if profit_so_far < self.curr_trailing_sl_profit and not self.is_pair_sl_set:
                self.set_sl(True)
                self.is_pair_sl_set = True
        if is_c2c_enabled:
            self.set_c2c(self.pe_leg, self.ce_leg)
            self.set_c2c(self.ce_leg, self.pe_leg)

    def set_c2c(self, hit_leg: LegTrade, other_leg: LegTrade):
        # if the sl of the other leg is already hit, you dont have the change the sl there as it doesnt do any purpose but only helps capturing wrog dat
        if hit_leg.is_sl_hit and (other_leg.is_c2c_set is False and other_leg.is_sl_hit is False):
            other_leg.is_c2c_set = True
            other_leg.sl = 1

    def set_sl(self, sl_status: bool):
        self.pe_leg.set_sl(sl_status)
        self.ce_leg.set_sl(sl_status)

    def get_profit(self, minute_index=-1):
        return self.pe_leg.get_profit(minute_index) + self.ce_leg.get_profit(minute_index)


class DayTrade:
    def __init__(self, leg_pair_dic: Dict[str, LegPair], trade_date_str: str, india_vix: int):
        self.leg_pair_dic: Dict[str, LegPair] = leg_pair_dic
        self.trade_date_str: str = trade_date_str
        self.filtered_leg_pairs_by_time: List[LegPair] = None
        self.india_vix = india_vix
        self.profit_tracker = []
        # this profit is different from other, as this will cause the flow to stop if this profit has been reached.
        self.is_stop_at_target_profit_reached = False
        # even though this profit is reached, it will still check for trailing sl
        self.is_target_profit_reached = False
        # after reaching above profit, if falls below trailing sl, the process will be stopped.
        self.is_trailing_sl_hit = False

    # setting the pairs and start minute that are applicable for selected time intervals
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

    def walk(self, minute_index, sl: float, target_profit: int, trailing_sl: int, stop_at_target: int,
             is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float):
        day_profit_so_far = 0
        for leg_pair in self.filtered_leg_pairs_by_time:
            leg_pair.walk_leg(minute_index, sl, is_c2c_enabled, min_profit_perc, trailing_sl_perc)
            day_profit_so_far = day_profit_so_far + leg_pair.get_profit(minute_index)
        self.profit_tracker.append(round(day_profit_so_far, 2))

        if self.is_trailing_sl_hit or self.is_stop_at_target_profit_reached:
            return
        # if day_profit_so_far <= -50:
        #     # print("reached..*************************")
        #     self.set_sl_for_all(True)
        #     self.is_trailing_sl_hit = False

        if target_profit != -1:
            # this is the case target profit has reached but the profit went below trailing profit
            if self.is_target_profit_reached:
                if day_profit_so_far <= trailing_sl:
                    # print("reached..*************************")
                    self.set_sl_for_all(True)
                    self.is_trailing_sl_hit = False
            if day_profit_so_far > target_profit:
                self.is_target_profit_reached = True
        if stop_at_target != -1 and day_profit_so_far > stop_at_target:
            self.set_sl_for_all(True)
            self.is_stop_at_target_profit_reached = True

    def set_sl_for_all(self, sl_status):
        for leg_pair in self.filtered_leg_pairs_by_time:
            leg_pair.set_sl(sl_status)

    def get_profit(self):
        total_profit = sum([leg_pair.get_profit() for leg_pair in self.filtered_leg_pairs_by_time])
        return total_profit

    def max_profit_reached(self):
        if len(self.profit_tracker) == 0:
            print("e")
        return max(self.profit_tracker)


def get_start_minute_index(start_time_str: str):
    minutes_till_0915 = (9 * 60) + 15
    start_hour_part = int(start_time_str[:2])
    start_min_part = int(start_time_str[2:])
    start_min = (start_hour_part * 60) + start_min_part
    start_min_index = (start_min - minutes_till_0915)
    return start_min_index


def analyze_interval_trades(straddle_times: List[str], start_date: str, end_date: str, regular_sl_perc: float,
                            target_profit: int, trailing_sl: int, stop_at_target: int, allowed_week_day: int,
                            is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float):
    # analyze_profit("2019-02-18", "2019-02-19", sl=.6, target_profit=-1, day_trailing_sl=20, week_day=-1)
    analyze_start_time = millis()
    day_trades: List[DayTrade] = get_pickle_data("day_trades")
    # 2019-10-27
    day_trades = [day_trade for day_trade in day_trades if start_date <= day_trade.trade_date_str <= end_date]
    # day_trades = [day_trade for day_trade in day_trades if '2019-10-27' <= day_trade.trade_date_str <= "2019-10-27"]
    # filter(lambda x: '2019-02-18' <= x.trade_date_str <= "2022-02-14", day_trades))
    total_profit = 0
    cummulative_profits = []
    trading_minute_list = get_minute_list('%H:%M:%S', "09:15:00", "14:30:00")
    profit_tracker: List[{}] = []
    # walk through each DayTrade>LegPair>LegTrade
    for day_trade in day_trades:
        day_trade_date = get_date_from_str(day_trade.trade_date_str)
        trade_week_day = day_trade_date.weekday()
        if allowed_week_day != -1 and trade_week_day != allowed_week_day:
            continue
        if day_trade.india_vix > 50:
            continue
        # start_time = millis()
        # only work in LegPairs whose interval matches the one that is present in the parameter
        day_trade.set_leg_pairs_by_straddle_times(straddle_times)
        for minute_index in range(len(trading_minute_list)):
            day_trade.walk(minute_index, regular_sl_perc, target_profit, trailing_sl, stop_at_target, is_c2c_enabled,
                           min_profit_perc, trailing_sl_perc)
        day_profit = round(day_trade.get_profit(), 2)
        # print(day_trade.profit_tracker)
        # for key in day_trade.leg_pair_dic:
        #     if key in ["1040", "1100", "1120", "1140"]:
        #         print(">>>>", key, day_trade.leg_pair_dic[key].pe_leg.get_profit(-1),
        #               day_trade.leg_pair_dic[key].ce_leg.get_profit(-1))
        # print(f'{day_trade.trade_date_str},{day_profit}')
        total_profit = total_profit + day_profit
        # cummulative_profits.append({"profit": round(total_profit, 2), "date": day_trade.trade_date_str})
        cummulative_profits.append(round(total_profit, 2))
        profit_tracker.append(
            {"profit": day_profit, "date": day_trade.trade_date_str, "max": day_trade.max_profit_reached(),
             "week_day": trade_week_day})

    day_profit_df = pd.DataFrame(profit_tracker, [i for i in range(len(profit_tracker))])
    write_pickle_data('day_profit_df', day_profit_df)
    # print(total_profit, (millis() - analyze_start_time))
    result = {}
    result['cumm_prft_list'] = cummulative_profits
    day_profit_df.index = pd.to_datetime(day_profit_df.date)
    per_month_df = day_profit_df.resample('M').agg(
        {'profit': 'sum', 'date': 'min'})
    result['negative_months_count'] = len(per_month_df[per_month_df.profit < 0])
    # result['negative_months'] = ",".join(map(str, per_month_df[per_month_df.profit < 0].profit.values))
    result['lowest_monthly_profit'] = round(per_month_df.sort_values('profit').profit.values[0])
    result['max_monthly_profit'] = round(per_month_df.sort_values('profit').profit.values[-1])
    result['total_profit'] = round(total_profit)
    result['straddle_count'] = len(straddle_times)
    # result['tot_profit'] = round(per_day_df.profit.sum())

    win_days = [day_profit["profit"] for day_profit in profit_tracker if day_profit["profit"] > 0]
    loss_days = [day_profit["profit"] for day_profit in profit_tracker if day_profit["profit"] < 0]
    max_days = [day_profit["max"] for day_profit in profit_tracker if day_profit["max"] > stop_at_target]

    result['days>stop_at_profit'] = len(max_days)
    result["intervals"] = len(straddle_times)
    # loss_days_with_pos_profit = [day_profit for day_profit in loss_days if max(day_profit.profit_list) > 20]
    # hello.to_clipboard()
    mean_profit = mean_loss = None
    if len(win_days) > 0:
        mean_profit = sum(win_days) / len(win_days)
    else:
        mean_profit = 0
    if len(loss_days) > 0:
        mean_loss = sum(loss_days) / len(loss_days)
    else:
        mean_loss = 0
    w_l_days_ratio = 'full' if len(loss_days) == 0 else round(len(win_days) / len(loss_days), 2)
    r_r_ratio = 'NA' if mean_loss == 0 else round(mean_profit / mean_loss, 2)
    print(
        f'week day >>> {allowed_week_day} profit:{result["total_profit"]}  win:{len(win_days)},loss:{len(loss_days)},ratio:{w_l_days_ratio}, win mean:{round(mean_profit, 2)}'
        f',mean loss:{round(mean_loss, 2)} ,rr:{r_r_ratio} result:{result}')
    return result


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


# only for the current year.
if True:
    # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 3, 52, 7, 100000, 400, '2019-01-01', '2019-12-31'
    # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 3, 52, 7, 80000, 300, '2020-01-01', '2020-12-31'
    # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 1, 52, 11, 116000, 480, '2021-01-01', '2022-02-11'
    lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 1, 52, 11, 116000, 480, '2019-01-01', '2022-04-28'
    # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 3, 16, 11, 116000, 480, "2022-01-18", "2022-01-18"
    # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 3, 6, 11, 116000, 480, "2022-01-04", "2022-01-04"
    brokerage_per_straddle = 250
    lot_quantity = 25
    # interval_times = ["1040", "1100", "1120", "1140"]
    # interval_times = ["0940", "1000", "1020", "1040"]
    interval_times = ["0940", "1040", ]
    interval_times_thu = ["0920", "1040"]
    # interval_times_fri = ["0940", "1000", "1020", "1040"]

    result_mon = result_tue = result_wed = result_thu = result_fri = None
    # result_mon = analyze_interval_trades(interval_times, start_date, end_date, 1.2, -1, 75,
    #                                      stop_at_target=-1, allowed_week_day=0, is_c2c_enabled=True,
    #                                      min_profit_perc=-1, trailing_sl_perc=.5)
    result_tue = analyze_interval_trades(interval_times, start_date, end_date, 1.2, -1, 65,
                                         stop_at_target=-1, allowed_week_day=1, is_c2c_enabled=True,
                                         min_profit_perc=-1, trailing_sl_perc=.5)
    result_wed = analyze_interval_trades(interval_times, start_date, end_date, 1.6, -1, 50,
                                         stop_at_target=-1, allowed_week_day=2, is_c2c_enabled=True,
                                         min_profit_perc=-1, trailing_sl_perc=.5)
    result_thu = analyze_interval_trades(interval_times_thu, start_date, end_date, 1.6, -1, 65,
                                         stop_at_target=-1, allowed_week_day=3, is_c2c_enabled=True,
                                         min_profit_perc=-1, trailing_sl_perc=.5)
    result_fri = analyze_interval_trades(interval_times, start_date, end_date, 1.2, -1, 50,
                                         stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=True,
                                         min_profit_perc=-1, trailing_sl_perc=.5)
    result_fri4 = analyze_interval_trades(["0940", "1040", "1140"], '2021-01-01', '2022-02-11', 1.2, 100, 60,
                                          stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=False,
                                          min_profit_perc=-1, trailing_sl_perc=.5)
    results = [result_mon, result_tue, result_wed, result_thu, result_fri]
    valid_results = [result for result in results if result is not None and result["intervals"] > 0]
    total_profit = sum([result["total_profit"] for result in valid_results])
    # straddle_counts = sum([result["straddle_count"] for result in results if result is not None])
    # 25 is the lot size / no. of months run

    total_days_in_year = weeks_run * len(valid_results)
    intervals = valid_results[0]["intervals"]
    # per_month = (total_profit * quantity) / months_run
    year_profit = total_profit * lots * lot_quantity
    yearly_brokerage = brokerage_per_straddle * intervals * total_days_in_year
    profit_after_brokerage = year_profit - yearly_brokerage
    yearly_cost_of_buy_leg = buy_legs_cost * lots * lot_quantity * intervals * total_days_in_year
    profit_after_buy_leg = profit_after_brokerage - 0

    daily_margin_for_sl = average_sl_buy * 2 * lots * lot_quantity * intervals
    daily_straddle_margin = margin_needed_for_straddle * lots * intervals
    daily_margin = daily_straddle_margin + daily_margin_for_sl
    print(
        f'totalprofit:{year_profit},year profit:{round(year_profit)}, y_brokerage:{yearly_brokerage},y_buy_leg:{yearly_cost_of_buy_leg}, '
        f'after brokerage:{round(profit_after_brokerage)},after buy leg:{round(profit_after_buy_leg)},straddle margin:{daily_straddle_margin},'
        f'margin sl:{daily_margin_for_sl}  '
        f'returns :{round(profit_after_buy_leg / daily_margin, 2)}')

# get_all_atm_strikes_by_interval("2019-01-01", "2022-04-28")
# generate_day_trades_by_interval()
