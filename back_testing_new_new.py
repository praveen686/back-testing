import copy
import datetime
import json
import random
from itertools import groupby
from typing import List, Dict

import pandas as pd

import constants
from option_util import get_minute_list, millis, load_nifty_min_data, load_india_vix_day_data, get_nifty_spot_price, \
    get_nearest_thursday, get_india_vix, round_nearest, get_nearest_expiry, get_instrument_prefix, \
    get_ticker_data_by_expiry_and_strike
from store_ticker_data_from_zerodha import store_india_vix_day_data_from_zerodha
from util import get_pickle_data, write_pickle_data, get_date_from_str, get_date_in_str, \
    get_formatted_time_by_adding_delta_to_base, get_diff_in_days

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
def get_all_atm_strikes_by_date(start_date: str, end_date: str):
    strike_count = 0
    df_other_day_list = []
    df_other_day_str_list = []
    df_other_time_intervals = []
    df_other_atm_option_strike_list = []
    atm_leg_trades_by_date_n_strike: Dict[str, LegTrade] = {}

    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    india_vix_day_dic = load_india_vix_day_data()
    trading_days_list = list(india_vix_day_dic.keys())
    # trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]
    expiry_df = pd.read_csv("expiry_df.csv")
    start_time = millis()
    # this holds the list of unique atm leg trades, unique in the sense, same strike can become atm multiple times,
    # still there will be only entry in the list
    unique_leg_trades: List[LegTrade] = []
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
        trading_minute_list = get_minute_list('%H:%M:%S', "09:15:00", "15:00:00")
        for trading_minute in trading_minute_list:

            # for trade_interval in trade_intervals:
            #     minute_reformatted = f'{trade_interval[0:2]}:{trade_interval[2:4]}:00'
            spot_price = get_nifty_spot_price(trading_date_str, trading_minute, nifty_min_data_dic, 'close')
            if spot_price == -1:
                print(f'no spot price present for date:{trading_date_str} and time:{trading_minute}')
                continue
            spot_price_nearest = round_nearest(spot_price, 100)
            for option_type in ["PE", "CE"]:
                strike_count = strike_count + 1
                df_other_day_list.append(date_time_in_secs)
                df_other_day_str_list.append(trading_date_str)
                # df_other_time_intervals.append(trade_interval)
                strike_ticker_symbol = f'{instrument_prefix}{spot_price_nearest}{option_type}'
                df_other_atm_option_strike_list.append(strike_ticker_symbol)
                strike_date_key = f'{strike_ticker_symbol}|{trading_date_str}'
                # same strike my repeat in a day as the strike which was atm at 9.30 migh continue being atm till 11 or
                # might go up/down and come back to become atm at 11
                if strike_date_key not in atm_leg_trades_by_date_n_strike:

                    leg_trade = LegTrade(trading_date_str, strike_ticker_symbol, india_vix, spot_price_nearest,
                                         option_type)
                    atm_leg_trades_by_date_n_strike[strike_date_key] = leg_trade
                    leg_trade.atm_minutes.append(trading_minute)
                else:
                    leg_trade: LegTrade = atm_leg_trades_by_date_n_strike[strike_date_key]
                    leg_trade.atm_minutes.append(trading_minute)
        # atm_premium = random.randrange(100, 300, 3)

    print("strike count", strike_count)
    print(f'len of atm_leg_trades_by_date_n_strike:{len(atm_leg_trades_by_date_n_strike)}')
    write_pickle_data('atm_leg_trades_by_date_n_strike', atm_leg_trades_by_date_n_strike)
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
def populate_leg_trade_with_premium_data_n_group_it_by_date():
    total_count_of_strikes = 0
    option_strike_minute_ticker_df = get_pickle_data('option_strike_minute_ticker_df')
    # this has all the entries for all the symbols
    row_entries = option_strike_minute_ticker_df.values
    atm_leg_trades_by_date_n_strike: Dict[str, LegTrade] = get_pickle_data('leg_trades_by_date_strike_n_offset')
    atm_strikes_by_interval_dest_list = []
    start_time = millis()
    # for index, row_entry in enumerate(row_entries):
    all_leg_trades: List[LegTrade] = []
    active_leg_trade: LegTrade = None
    for index, row_entry in enumerate(row_entries):
        # whenever 9:15 is reached, will append the premium to a new LegTrade fetched from 'atm_strikes_by_interval'
        if row_entry[4] == "09:15:00":
            total_count_of_strikes = total_count_of_strikes + 1

            leg_trade_strike_key = f'{row_entry[1]}|{row_entry[3]}'  # a combination of symbol and date
            print(leg_trade_strike_key)
            if leg_trade_strike_key in atm_leg_trades_by_date_n_strike:
                # the way I have set up the datamodel, a key of 'symbol and date' might have multiple
                # atm strikes under it as the same strike would continue as the atm for so long or come back at later
                # point and become atm then
                # for ex: 'BANKNIFTY 22 D 13 34000' might be atm strike at 9:20 till 11:20 or come back at 13:20 and become atm again
                active_leg_trade = atm_leg_trades_by_date_n_strike[leg_trade_strike_key]
                all_leg_trades.append(active_leg_trade)
            else:
                active_leg_trade = None
        if active_leg_trade is not None:
            active_leg_trade.premium_tickers.append(row_entry[5])  # catching premium

    grouped_leg_trade_by_date: List[List[LegTrade]] = [list(g) for k, g in
                                                       groupby(sorted(all_leg_trades,
                                                                      key=lambda xy: xy.trade_date),
                                                               lambda xy: xy.trade_date)]

    # loop through
    day_trades: List[DayTrade] = []
    for date_leg_trades in grouped_leg_trade_by_date:
        day_trade = DayTrade(date_leg_trades[0].trade_date, date_leg_trades[0].india_vix, date_leg_trades)
        day_trades.append(day_trade)
        # if len(date_leg_trades) != 30:
        #     print(f'data not correct for the date :{date_leg_trades[0].straddle_date}')

        # leg_pair_time_dic: Dict[str, LegPair] = {}
        # # leg_pairs: List[LegPair] = []
        # leg_trade_pairs: List[List[LegTrade]] = [list(g) for k, g in
        #                                          groupby(
        #                                              sorted(date_leg_trades, key=lambda xy: xy.straddle_time),
        #                                              lambda xy: xy.straddle_time)]
        # for leg_trade_pair in leg_trade_pairs:
        #     leg_pair: LegPair = LegPair(leg_trade_pair[0].straddle_time, leg_trade_pair[0], leg_trade_pair[1])
        #     leg_pair_time_dic[leg_trade_pair[0].straddle_time] = leg_pair
        #     # leg_pairs.append(leg_pair)
        # day_trades.append(DayTrade(leg_pair_time_dic, date_leg_trades[0].straddle_date, date_leg_trades[0].india_vix))

    write_pickle_data("day_trades_all_minute", day_trades)
    # print(x_temp, total_count_of_strikes)
    # print(len(atm_strikes_by_interval_dest_list))
    print(millis() - start_time)


class LegTrade:
    def __init__(self, trade_date: str, ticker_symbol: str, india_vix: int, strike_price, option_type):
        # list of minutes at which this particular leg/ticker was atm
        self.atm_minutes: List[str] = []
        self.strike_price: float = strike_price
        self.option_type: str = option_type
        self.trade_date: str = trade_date
        self.ticker_symbol = ticker_symbol
        self.premium_tickers = []
        self.valid_prem_tickers: List[float] = []
        self.profit_by_time: Dict[int, float] = {}
        self.is_sl_hit = False
        self.sl_hit_index: int = None
        self.india_vix = india_vix
        self.is_c2c_set = False
        self.sl_hit_premium = -1

    def walk(self, minute_index, start_index, sl: float, transaction_type: str):
        start_time = millis()
        # if the interval time hasnt reached.
        if minute_index >= start_index:
            ticker_premium = self.premium_tickers[minute_index]
            # this is to check whether its not nan
            if ticker_premium == ticker_premium:
                self.valid_prem_tickers.append(float(ticker_premium))
            else:
                # falling back to previous premium if current premium is null given its non zero size
                if len(self.valid_prem_tickers) > 0:
                    self.valid_prem_tickers.append(self.valid_prem_tickers[-1])
                    # last_key_present = list(self.valid_prem_tickers.keys())[-1]
                    # self.valid_prem_tickers[minute_index] = self.valid_prem_tickers[last_key_present]
                # else:
                #     self.valid_prem_tickers[minute_index] = 0

            if len(self.valid_prem_tickers) > 0:
                # premium_keys = list(self.valid_prem_tickers.keys())
                start_premium = self.valid_prem_tickers[0]
                curr_premium = self.valid_prem_tickers[-1]
                if self.is_sl_hit is False:
                    curr_profit = round(start_premium - curr_premium, 2) * (-1 if transaction_type == "BUY" else 1)
                    # check for sl only if its enabled
                    if sl != -1:
                        # if curr_profit < (sl * float(self.valid_prem_tickers[0])) * -1:
                        if ((transaction_type == "SELL" and curr_premium > (sl * start_premium)) or (
                                transaction_type == "BUY" and curr_premium < (sl * start_premium))):
                            self.is_sl_hit = True
                            self.sl_hit_index = minute_index
                            self.sl_hit_premium = curr_premium
                else:
                    # getting the previous profit to append in case sl is met already
                    if len(self.profit_by_time) == 0:
                        self.profit_by_time[minute_index] = 0
                    curr_profit = self.profit_by_time[list(self.profit_by_time.keys())[-1]]
                self.profit_by_time[minute_index] = curr_profit
            else:
                self.profit_by_time[minute_index] = 0
                # raise Exception("there should be entries")

    def set_sl(self, sl_status: bool):
        self.is_sl_hit = sl_status

    # get the profit upto the minute passed
    def get_profit(self, minute_index: int, start_index: int):
        profit_keys = list(self.profit_by_time.keys())
        profit_key = minute_index if minute_index != -1 else profit_keys[-1]
        if minute_index >= start_index and profit_key not in profit_keys:
            raise Exception(f'minute index:{minute_index} should be present!!!')
        # if accessed before trading as started, this could raise 'KeyError' so returning 0
        return 0 if profit_key not in profit_keys else self.profit_by_time[profit_key]
        # return self.profit_by_time[profit_key]
        # return profit
        # print(self.profit_by_time)


class LegPair:

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
        # self.pair_profit_tracker = []
        self.is_pair_sl_set = False
        # to identify whether this pair was added as part of adjustment
        self.pair_type = constants.LEG_PAIR_TYPE_ORIGINAL
        self.adjustment_leg: LegPair = None

        # minutes_till_0915 = (9 * 60) + 15

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def serialize(self):
        return {
            'pe': {"tickers": self.pe_leg.premium_tickers, "symbol": self.pe_leg.ticker_symbol},
            'ce': {"tickers": self.ce_leg.premium_tickers, "symbol": self.ce_leg.ticker_symbol}
        }

    def test_test(self):
        return 1

    def walk_leg(self, minute_index, sl: float, is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float,
                 transaction_type: str):

        self.pe_leg.walk(minute_index, self.start_min_index, 1 if self.pe_leg.is_c2c_set else sl, transaction_type)
        self.ce_leg.walk(minute_index, self.start_min_index, 1 if self.ce_leg.is_c2c_set else sl, transaction_type)
        # if add_adj_leg:
        #     if self.pe_leg.is_sl_hit and
        profit_so_far = self.pe_leg.get_profit(minute_index, self.start_min_index) + self.ce_leg.get_profit(
            minute_index, self.start_min_index)
        start_premium = \
            sorted([self.pe_leg.premium_tickers[0], self.ce_leg.premium_tickers[0]], key=lambda x: float(x))[0]
        # no need to check for min target reached if its been already checked in the prev cycle.
        if min_profit_perc != -1:
            if self.target_min_profit_perc_reached is False:
                if profit_so_far >= min_profit_perc * float(start_premium):
                    self.target_min_profit_perc_reached = True
                    self.curr_trailing_sl_profit = profit_so_far * trailing_sl_perc
                # self.pair_profit_tracker.append(profit_so_far)
                # idea is to check whether we have reached target perc of the smallest premium in the leg
                if self.target_min_profit_perc_reached:
                    # after you have reached min profit and gone beyond, if it goes less than trailing sl profit exit
                    if profit_so_far < self.curr_trailing_sl_profit and not self.is_pair_sl_set:
                        self.set_sl(True)
                        self.is_pair_sl_set = True

        if is_c2c_enabled:
            self.set_c2c(self.pe_leg, self.ce_leg)
            self.set_c2c(self.ce_leg, self.pe_leg)

    def set_c2c(self, other_leg: LegTrade, analyzed_leg: LegTrade):
        # if the sl of the other leg is already hit, you dont have the change the sl there as it doesnt do any purpose but only helps capturing wrog dat
        if other_leg.is_sl_hit and (analyzed_leg.is_c2c_set is False and analyzed_leg.is_sl_hit is False):
            analyzed_leg.is_c2c_set = True
            analyzed_leg.sl = 1

    def set_sl(self, sl_status: bool):
        self.pe_leg.set_sl(sl_status)
        self.ce_leg.set_sl(sl_status)

    def get_profit(self, minute_index=-1):
        return self.pe_leg.get_profit(minute_index, self.start_min_index) + self.ce_leg.get_profit(minute_index,
                                                                                                   self.start_min_index)


class NewDayTrade:
    def __init__(self, trade_date_str: str, india_vix: float, leg_trades: List[LegTrade]):
        self.trade_date_str: str = trade_date_str
        self.india_vix: float = india_vix
        self.leg_trades: List[LegTrade] = leg_trades


class DayTrade:
    def __init__(self, trade_date_str: str, india_vix: float, leg_trades: List[LegTrade]):
        self.trade_date_str: str = trade_date_str
        self.india_vix: float = india_vix
        self.leg_trades: List[LegTrade] = leg_trades
        # this list holds the trades that needs to be backtested
        self.filtered_leg_pairs_by_time: List[LegPair] = []
        self.profit_tracker = []
        # this profit is different from other, as this will cause the flow to stop if this profit has been reached.
        self.is_stop_at_target_profit_reached = False
        # even though this profit is reached, it will still check for trailing sl
        self.is_target_profit_reached = False
        # after reaching above profit, if falls below trailing sl, the process will be stopped.
        self.is_trailing_sl_hit = False
        #     going with trailing sl which is decided dynamically
        self.trailing_profit = -1

    # setting the pairs and start minute that are applicable for selected time intervals
    def set_leg_pairs_by_straddle_times(self, straddle_times: List[str]):
        self.filtered_leg_pairs_by_time = []
        for straddle_time in straddle_times:
            pe_min_strike = f'{straddle_time.split("|")[0]}|{(straddle_time.split("|")[1].split(",")[0])}'
            # atm minutes will have entries like -100 to 100 to get the itm and otm strikes.
            pe_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                            pe_min_strike in leg_trade.atm_minutes and leg_trade.option_type == "PE"]
            ce_min_time = f'{straddle_time.split("|")[0]}|{(straddle_time.split("|")[1].split(",")[1])}'
            ce_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                            ce_min_time in leg_trade.atm_minutes and leg_trade.option_type == "CE"]

            if len(pe_leg_trade) > 0 and len(ce_leg_trade) > 0:

                start_min_index = get_start_minute_index(straddle_time)
                pe_start_premium = pe_leg_trade[0].premium_tickers[start_min_index]
                ce_start_premium = ce_leg_trade[0].premium_tickers[start_min_index]
                premium_diff = 0
                if pe_start_premium == pe_start_premium and ce_start_premium == ce_start_premium:
                    premium_diff = round(abs(float(pe_start_premium) - float(ce_start_premium)))
                print(
                    f'premdiff:{premium_diff > 35} diff:{premium_diff} pesym:{pe_leg_trade[0].ticker_symbol} cesym:{ce_leg_trade[0].ticker_symbol}  {pe_leg_trade[0].india_vix} {pe_start_premium} {ce_start_premium}')
                # lets say there 30 difference, 30* 2 = 60, which is greater than 50, so will pick next strike, even though it will move 50 points
                if premium_diff > 35 and False:
                    # this for adjusting the strike if the amount if the strike price is not balanced.
                    if pe_start_premium > ce_start_premium:
                        new_pe_min_time = f'{straddle_time[0:8]}|-{round_nearest(premium_diff * 2, 100)}'
                        pe_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                                        new_pe_min_time in leg_trade.atm_minutes and leg_trade.option_type == "PE"]
                        straddle_time_offset = f'{straddle_time[0:8]}|-{round_nearest(premium_diff * 2, 100)},0'
                    else:
                        new_ce_min_time = f'{straddle_time[0:8]}|{round_nearest(premium_diff * 2, 100)}'
                        ce_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                                        new_ce_min_time in leg_trade.atm_minutes and leg_trade.option_type == "CE"]
                        straddle_time_offset = f'{straddle_time[0:8]}|0,{round_nearest(premium_diff * 2, 100)}'
                    if len(pe_leg_trade) > 0 and len(ce_leg_trade) > 0:
                        leg_pair = LegPair("", copy.deepcopy(pe_leg_trade[0]), copy.deepcopy(ce_leg_trade[0]))
                        leg_pair.start_min_index = start_min_index
                        leg_pair.selected_straddle_time = straddle_time_offset
                        pe_start_premium = pe_leg_trade[0].premium_tickers[start_min_index]
                        ce_start_premium = ce_leg_trade[0].premium_tickers[start_min_index]
                        premium_diff = round(abs(float(pe_start_premium) - float(ce_start_premium)))
                        print(
                            f'corrpremdiff:{premium_diff > 20} {premium_diff} pesym:{pe_leg_trade[0].ticker_symbol} cesym:{ce_leg_trade[0].ticker_symbol}  {pe_leg_trade[0].india_vix} {pe_start_premium} {ce_start_premium}')

                else:
                    leg_pair = LegPair("", copy.deepcopy(pe_leg_trade[0]), copy.deepcopy(ce_leg_trade[0]))
                    leg_pair.selected_straddle_time = straddle_time
                    leg_pair.start_min_index = start_min_index
                    self.filtered_leg_pairs_by_time.append(leg_pair)

                # # todo make the change here to fetch based on the time
                # leg_pair = self.leg_pair_dic[straddle_time]
                # leg_pair.selected_straddle_time = straddle_time
                # leg_pair.start_min_index = get_start_minute_index(straddle_time)
                # self.filtered_leg_pairs_by_time.append(leg_pair)
            else:
                print("x")

    def get_leg_pair_by_time(self, trade_min):
        pe_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                        trade_min in leg_trade.atm_minutes and leg_trade.option_type == "PE"]
        ce_leg_trade = [leg_trade for leg_trade in self.leg_trades if
                        trade_min in leg_trade.atm_minutes and leg_trade.option_type == "CE"]

        if len(pe_leg_trade) > 0 and len(ce_leg_trade) > 0:
            leg_pair = LegPair("", copy.deepcopy(pe_leg_trade[0]), copy.deepcopy(ce_leg_trade[0]))
            leg_pair.start_min_index = get_start_minute_index(trade_min)
            leg_pair.selected_straddle_time = trade_min
            return leg_pair
        return None

    def walk(self, minute_index, sl: float, target_profit: int, trailing_profit_perc: float, stop_at_target: int,
             is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float, add_adj_leg: bool,
             transaction_type: str):
        day_profit_so_far = 0
        for leg_pair in self.filtered_leg_pairs_by_time:
            leg_pair.walk_leg(minute_index, sl, is_c2c_enabled, min_profit_perc, trailing_sl_perc, transaction_type)
            day_profit_so_far = day_profit_so_far + leg_pair.get_profit(minute_index)
            # only do the adjustment for the original leg, skip the leg the was added for the adjustment
            if add_adj_leg and leg_pair.pair_type == constants.LEG_PAIR_TYPE_ORIGINAL and leg_pair.adjustment_leg is None:
                pe_leg_profit = leg_pair.pe_leg.get_profit(minute_index, leg_pair.start_min_index)
                ce_leg_profit = leg_pair.ce_leg.get_profit(minute_index, leg_pair.start_min_index)
                if leg_pair.pe_leg.is_sl_hit and ce_leg_profit <= 0:
                    print("reached in ce adj", self.trade_date_str)
                    formatted_time = get_formatted_time_by_adding_delta_to_base("09:15:00", minute_index)
                    new_leg_pair = self.get_leg_pair_by_time(formatted_time)
                    if new_leg_pair is not None:
                        new_leg_pair.pair_type = constants.LEG_PAIR_TYPE_ADJUSTMENT
                        self.filtered_leg_pairs_by_time.append(new_leg_pair)
                        leg_pair.adjustment_leg = new_leg_pair

                if leg_pair.ce_leg.is_sl_hit and pe_leg_profit <= 0:
                    print("reached in pe adj")
                    formatted_time = get_formatted_time_by_adding_delta_to_base("09:15:00", minute_index)
                    new_leg_pair = self.get_leg_pair_by_time(formatted_time)
                    if new_leg_pair is not None:
                        new_leg_pair.pair_type = constants.LEG_PAIR_TYPE_ADJUSTMENT
                        self.filtered_leg_pairs_by_time.append(new_leg_pair)
                        leg_pair.adjustment_leg = new_leg_pair

        self.profit_tracker.append(round(day_profit_so_far, 2))

        if self.is_trailing_sl_hit or self.is_stop_at_target_profit_reached:
            return
        # if day_profit_so_far <= -50:
        #     # print("reached..*************************")
        #     self.set_sl_for_all(True)
        #     self.is_trailing_sl_hit = False
        # if day_profit_so_far <= -600:
        #     self.set_sl_for_all(True)
        if target_profit != -1:
            # this is the case target profit has reached but the profit went below trailing profit
            if self.is_target_profit_reached:
                if day_profit_so_far <= self.trailing_profit:
                    # print("reached..*************************")
                    self.set_sl_for_all(True)
                    self.is_trailing_sl_hit = False
                    print("reached trailing profit", self.trade_date_str, day_profit_so_far, self.trailing_profit,
                          minute_index)
            # if day_profit_so_far < target_profit * -1:
            #     self.set_sl_for_all(True)
            if day_profit_so_far > target_profit:
                self.is_target_profit_reached = True
                # first time trailing profit will be -1 so set it blindly
                if self.trailing_profit == -1:
                    self.trailing_profit = day_profit_so_far * trailing_profit_perc
                else:
                    new_trailing_profit = day_profit_so_far * trailing_profit_perc
                    if new_trailing_profit > self.trailing_profit:
                        self.trailing_profit = new_trailing_profit
                        print("reached trailing profit set", self.trade_date_str, day_profit_so_far,
                              self.trailing_profit,
                              minute_index)

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
    start_min_part = int(start_time_str[3:5])
    start_min = (start_hour_part * 60) + start_min_part
    start_min_index = (start_min - minutes_till_0915)
    return start_min_index


day_trades: List[DayTrade] = None


def analyze_interval_trades(straddle_times: List[str], start_date: str, end_date: str, regular_sl_perc: float,
                            target_profit: int, trailing_profit_perc: float, stop_at_target: int, allowed_week_day: int,
                            is_c2c_enabled: bool, min_profit_perc: float, trailing_sl_perc: float, add_adj_leg: bool,
                            start_time, end_time, analyzed_date_str: str, transaction_type: str, india_vix_fn):
    if len(straddle_times) == 0:
        return
    nifty_min_data_dic = load_nifty_min_data("BANKNIFTY")
    # analyze_profit("2019-02-18", "2019-02-19", sl=.6, target_profit=-1, day_trailing_sl=20, week_day=-1)
    analyze_start_time = millis()
    global day_trades
    if day_trades is None:
        day_trades = get_pickle_data("day_trades_all_minute")
    # this is not needed same day is not traded again
    day_trades = [day_trade for day_trade in day_trades if
                  start_date <= day_trade.trade_date_str <= end_date]
    # day_trades = [day_trade for day_trade in day_trades if '2019-10-27' <= day_trade.trade_date_str <= "2019-10-27"]
    # filter(lambda x: '2019-02-18' <= x.trade_date_str <= "2022-02-14", day_trades))
    total_profit = 0
    cummulative_profits = []
    trading_minute_list = get_minute_list('%H:%M:%S', start_time, end_time)
    profit_tracker: List[{}] = []
    # walk through each DayTrade>LegPair>LegTrade
    for day_trade in day_trades:
        day_trade_date = get_date_from_str(day_trade.trade_date_str)
        trade_week_day = day_trade_date.weekday()
        if allowed_week_day != -1 and trade_week_day != allowed_week_day:
            continue
        if india_vix_fn(day_trade.india_vix) is False:
            continue
        # start_time = millis()
        # only work in LegPairs whose interval matches the one that is present in the parameter
        day_trade.set_leg_pairs_by_straddle_times(straddle_times)
        for minute_index in range(len(trading_minute_list)):
            day_trade.walk(minute_index, regular_sl_perc, target_profit, trailing_profit_perc, stop_at_target,
                           is_c2c_enabled,
                           min_profit_perc, trailing_sl_perc, add_adj_leg, transaction_type)
        day_profit = round(day_trade.get_profit(), 2)
        print(day_trade.trade_date_str, day_trade.profit_tracker[-1])
        if day_trade.trade_date_str == analyzed_date_str:
            analysis_dic = {}
            analyze_leg_pairs = day_trade.filtered_leg_pairs_by_time
            for leg_pair_index, leg_pair in enumerate(analyze_leg_pairs):
                pe_leg = leg_pair.pe_leg
                for ticker_index, ticker in enumerate(pe_leg.premium_tickers):
                    row_entry = {}
                    formatted_time = get_formatted_time_by_adding_delta_to_base("09:15:00", ticker_index)
                    spot = get_nifty_spot_price(day_trade.trade_date_str, formatted_time, nifty_min_data_dic, 'close')
                    pe_ticker = ticker
                    ce_ticker = leg_pair.ce_leg.premium_tickers[ticker_index]
                    pe_profit = 0 if ticker_index not in leg_pair.pe_leg.profit_by_time else \
                        leg_pair.pe_leg.profit_by_time[
                            ticker_index]
                    ce_profit = 0 if ticker_index not in leg_pair.ce_leg.profit_by_time else \
                        leg_pair.ce_leg.profit_by_time[
                            ticker_index]
                    row_entry = {f'spot-{leg_pair_index}': spot, f'pe-premium-{leg_pair_index}': pe_ticker,
                                 f'ce-premium-{leg_pair_index}': ce_ticker, f'pe-profit-{leg_pair_index}': pe_profit,
                                 f'ce-profit-{leg_pair_index}': ce_profit}
                    if ticker_index not in analysis_dic:
                        analysis_dic[ticker_index] = row_entry
                    else:
                        insert_row_entry = analysis_dic[ticker_index]
                        for key in row_entry:
                            insert_row_entry[key] = row_entry[key]
            analysis_data_df = pd.DataFrame(analysis_dic.values(), list(range(0, 375)))
            analysis_data_df.to_csv("analysis_data.csv")

        total_profit = total_profit + day_profit
        if len(day_trade.filtered_leg_pairs_by_time) > 0:
            # cummulative_profits.append({"profit": round(total_profit, 2), "date": day_trade.trade_date_str})
            cummulative_profits.append({"profit": round(total_profit, 2), "date": day_trade.trade_date_str})
            for index, filtered_pair in enumerate(day_trade.filtered_leg_pairs_by_time):
                print(f'sl>>hit>>{filtered_pair.pe_leg.is_sl_hit} {filtered_pair.pe_leg.option_type} index:{index}')
                print(f'sl>>hit>>{filtered_pair.ce_leg.is_sl_hit} {filtered_pair.ce_leg.option_type} index:{index}')

            if day_trade.filtered_leg_pairs_by_time[0].pe_leg.is_sl_hit and day_trade.filtered_leg_pairs_by_time[
                0].ce_leg.is_sl_hit:
                print("both sl hit")
            profit_tracker.append(
                {"profit": day_profit, "date": day_trade.trade_date_str, "max": day_trade.max_profit_reached(),
                 "week_day": trade_week_day})

    print(profit_tracker)
    if len(profit_tracker) == 0:
        return None
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
    days_gt_tr_pft = [day_profit["max"] for day_profit in profit_tracker if day_profit["max"] > target_profit]
    days_gt_sat_pft = [day_profit["max"] for day_profit in profit_tracker if day_profit["max"] > stop_at_target]

    result['days>target_profit'] = len(days_gt_tr_pft)
    result['days>stop_at_profit'] = len(days_gt_sat_pft)

    result['mean_day_profit'] = round(day_profit_df["profit"].mean())
    if len(day_profit_df) > 1:
        result['std_day_profit'] = round(day_profit_df["profit"].std())
    else:
        result['std_day_profit'] = None
    result['negative_days_count'] = len(day_profit_df[day_profit_df.profit < 0])

    day_profit_df['Cumulative'] = day_profit_df.profit.cumsum().round(2)
    day_profit_df['HighValue'] = day_profit_df['Cumulative'].cummax()
    day_profit_df['DrawDown'] = day_profit_df['Cumulative'] - day_profit_df['HighValue']
    result['drawdown'] = round(day_profit_df.sort_values('DrawDown').DrawDown.values[0])

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
    result["win_days"] = len(win_days)
    result["loss_days"] = len(loss_days)
    result["mean_profit"] = round(mean_profit, 2)
    result["mean_loss"] = round(mean_loss, 2)
    result["r_r_ratio"] = r_r_ratio
    result["allowed_week_day"] = allowed_week_day
    result["profit_tracker"] = profit_tracker
    result["week_day_profit_df"] = day_profit_df

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


def run_analysis(status: bool):
    # only for the current year.
    if status:
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg = 3, 52, 11, 116000, 480, '2021-01-01', '2022-02-11', False
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg = 1, 52, 11, 116000, 480, '2019-01-01', '2022-04-28', True
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str = 4, 16, 11, 116000, 480, "2022-01-03", "2022-04-28", False, '2022-03-10'
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date = 3, 6, 11, 116000, 480, "2022-01-18", "2022-01-18"

        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 3, 52, 7, 100000, 400, "2019-02-18", '2019-12-31', False, '2022-03-10', "SELL"
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 3, 52, 7, 80000, 300, '2020-01-01', '2020-12-31', False, '2022-03-10', "SELL"
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 3, 52, 11, 116000, 480, '2021-01-01', '2021-12-31', False, '2022-03-10', "SELL"
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 3, 16, 11, 116000, 480, "2022-01-03", "2022-04-28", False, '2022-01-07', "SELL"
        # individual dates
        # lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 3, 16, 11, 116000, 480, "2022-02-03", "2022-02-03", False, '2022-01-07', "SELL"

        lots, weeks_run, buy_legs_cost, margin_needed_for_straddle, average_sl_buy, start_date, end_date, add_adj_leg, analysis_date_str, transaction_type = 1, 16, 11, 100000, 400, "2019-02-18", "2022-04-28", False, '2022-01-07', "SELL"

        brokerage_per_straddle = 250
        lot_quantity = 25

        test_to_run = ["result_mon", "result_tue", "result_tue1", "result_wed", "result_wed1",
                       "result_thu",
                       "result_thu1", "result_fri"]
        test_to_run = ["result_thu"]
        # test_to_run = ["result_thu", "result_thu1"]

        result_mon = result_tue = result_wed = result_thu = result_fri = None
        # "09:40:00|0,0", "10:40:00|0,0", "11:40:00|0,0"
        result_mon = analyze_interval_trades(["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
                                             1.2, 60, .5,
                                             stop_at_target=-1, allowed_week_day=0, is_c2c_enabled=True,
                                             min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                             start_time="09:15:00", end_time="14:30:00",
                                             analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                             india_vix_fn=lambda x: x <= 20 and "result_mon" in test_to_run)
        result_mon1 = analyze_interval_trades(["09:40:00|100,-100", "10:40:00|100,-100"], start_date,
                                              end_date,
                                              1.2, 60, .5,
                                              stop_at_target=-1, allowed_week_day=0, is_c2c_enabled=True,
                                              min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                              start_time="09:15:00", end_time="14:30:00",
                                              analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                              india_vix_fn=lambda x: x >= 20 and "result_mon1" in test_to_run)
        # "09:40:00|0,0", "10:40:00|0,0", "11:40:00|0,0"
        result_tue = analyze_interval_trades(["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
                                             1.2, -1,
                                             .8,
                                             stop_at_target=-1, allowed_week_day=1, is_c2c_enabled=False,
                                             min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                             start_time="09:15:00", end_time="14:30:00",
                                             analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                             india_vix_fn=lambda x: x < 20 and "result_tue" in test_to_run)

        # "09:40:00|100,-100", "10:40:00|100,-100", "11:40:00|100,-100"
        result_tue1 = analyze_interval_trades(["09:40:00|100,-100", "10:40:00|100,-100"],
                                              start_date, end_date, 1.2,
                                              -1,
                                              .6,
                                              stop_at_target=-1, allowed_week_day=1, is_c2c_enabled=False,
                                              min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                              start_time="09:15:00", end_time="14:30:00",
                                              analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                              india_vix_fn=lambda x: x >= 20 and "result_tue1" in test_to_run)
        # "09:40:00|0,0", "10:40:00|0,0", "11:40:00|0,0"
        result_wed = analyze_interval_trades(["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
                                             1.2, -1,
                                             .6,
                                             stop_at_target=-1, allowed_week_day=2, is_c2c_enabled=False,
                                             min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                             start_time="09:15:00", end_time="14:30:00",
                                             analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                             india_vix_fn=lambda x: x < 20 and "result_wed" in test_to_run)
        # "09:40:00|100,-100", "10:40:00|100,-100", "11:40:00|100,-100"
        result_wed1 = analyze_interval_trades(["09:40:00|100,-100", "10:40:00|100,-100"],
                                              start_date, end_date, 1.2,
                                              -1,
                                              .6,
                                              stop_at_target=-1, allowed_week_day=2, is_c2c_enabled=False,
                                              min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                              start_time="09:15:00", end_time="14:30:00",
                                              analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                              india_vix_fn=lambda x: x >= 20 and "result_wed1" in test_to_run)

        # "09:20:00|0,0", "10:40:00|0,0", "11:40:00|0,0"
        result_thu = analyze_interval_trades(["09:20:00|-800,800", "10:40:00|-800,-800"], start_date, end_date,
                                             1.6, -1, .6,
                                             stop_at_target=-1, allowed_week_day=3, is_c2c_enabled=False,
                                             min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=False,
                                             start_time="09:15:00", end_time="14:30:00",
                                             analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                             india_vix_fn=lambda x: x < 20 and "result_thu" in test_to_run)

        result_thu1 = analyze_interval_trades(["09:20:00|100,-100", "10:40:00|100,-100"], start_date,
                                              end_date, 1.6,
                                              -1, .6,
                                              stop_at_target=-1, allowed_week_day=3, is_c2c_enabled=False,
                                              min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=False,
                                              start_time="09:15:00", end_time="14:30:00",
                                              analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                              india_vix_fn=lambda x: x >= 20 and "result_thu1" in test_to_run)
        # "09:40:00|0,0", "10:40:00|0,0", "11:40:00|0,0"
        result_fri = analyze_interval_trades(["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
                                             1.2, 60, .5,
                                             stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=True,
                                             min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                             start_time="09:15:00", end_time="14:30:00",
                                             analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                             india_vix_fn=lambda x: x <= 20 and "result_fri" in test_to_run)
        result_fri1 = analyze_interval_trades(["09:40:00|100,-100"], start_date,
                                              end_date,
                                              1.2, -1, .5,
                                              stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=True,
                                              min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg,
                                              start_time="09:15:00", end_time="14:30:00",
                                              analyzed_date_str=analysis_date_str, transaction_type=transaction_type,
                                              india_vix_fn=lambda x: x > 20 and "result_fri1" in test_to_run)
        # result_fri4 = analyze_interval_trades(["0940", "1040", "1140"], '2021-01-01', '2022-02-11', 1.2, 100, 60,
        #                                       stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=False,
        #                                       min_profit_perc=-1, trailing_sl_perc=.5, add_adj_leg=add_adj_leg)
        results = [result_mon, result_mon1, result_tue, result_tue1, result_wed, result_wed1, result_thu, result_thu1,
                   result_fri, result_fri1]
        valid_results = [result for result in results if result is not None and result["intervals"] > 0]
        total_profit = 0
        # straddle_counts = sum([result["straddle_count"] for result in results if result is not None])
        # 25 is the lot size / no. of months run

        combined_profit_tracker = []

        total_profit_after_brokerage = 0
        first_valid_intervals = valid_results[0]["intervals"]
        for valid_result in valid_results:
            write_pickle_data('week_day_profit_df', valid_result["week_day_profit_df"])
            week_intervals = valid_result["intervals"]
            profit_per_unit = valid_result["total_profit"]
            profit_trackers = valid_result["profit_tracker"]
            cumm_tracker = valid_result["cumm_prft_list"]
            no_of_days_run = len(profit_trackers)
            weekday_lot_profit = profit_per_unit * lots * lot_quantity
            weekday_brokerage = brokerage_per_straddle * week_intervals * no_of_days_run
            weekday_profit_after_brokerage = weekday_lot_profit - weekday_brokerage
            day_profits = [tracker["profit"] for tracker in profit_trackers]
            cumm_profits = [tracker["profit"] for tracker in cumm_tracker]

            print(
                f'day:{valid_result["allowed_week_day"]} ppu:{profit_per_unit} win_d:{valid_result["win_days"]} '
                f'loss_d:{valid_result["loss_days"]} mean_p:{valid_result["mean_profit"]} mean_l:{valid_result["mean_loss"]} rr:{valid_result["r_r_ratio"]}'
                f' lot_profit:{weekday_lot_profit}, brokerage:{weekday_brokerage}, net profit:{weekday_profit_after_brokerage} ntve_m_ct:{valid_result["negative_months_count"]} mn_d_pft:{valid_result["mean_day_profit"]} '
                f' std_d_pft:{valid_result["std_day_profit"]} ntve_d_ct:{valid_result["negative_days_count"]} drawdown:{float(valid_result["drawdown"]) * lots * lot_quantity} '
                f' >gt_t_p:{valid_result["days>target_profit"]} >gt_s_a_t:{valid_result["days>stop_at_profit"]} cumm_tackers:{cumm_profits} daytracker:{day_profits}')
            total_profit_after_brokerage = total_profit_after_brokerage + weekday_profit_after_brokerage
            # adding profit tracker to the combined result
            combined_profit_tracker.extend(valid_result["profit_tracker"])

        max_interval_in_week = max([valid_result["intervals"] for valid_result in valid_results])
        print("mx interval", max_interval_in_week)
        daily_margin_for_sl = average_sl_buy * 2 * lots * lot_quantity * max_interval_in_week
        daily_straddle_margin = margin_needed_for_straddle * lots * max_interval_in_week
        daily_margin = daily_straddle_margin + daily_margin_for_sl
        print(
            f'after brokerage:{round(total_profit_after_brokerage)},,straddle margin:{daily_straddle_margin},'
            f'margin sl:{daily_margin_for_sl}  '
            f'returns :{round(total_profit_after_brokerage / daily_margin, 2)}')

        print("combined length", len(combined_profit_tracker))
        combined_profit_tracker = sorted(combined_profit_tracker, key=lambda xy: xy["date"])
        combined_profit_tracker_df = pd.DataFrame(combined_profit_tracker,
                                                  [i for i in range(len(combined_profit_tracker))])
        combined_profit_tracker_df.index = pd.to_datetime(combined_profit_tracker_df.date)
        write_pickle_data('combined_profit_tracker_df', combined_profit_tracker_df)
