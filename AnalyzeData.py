import copy
import re
from datetime import datetime, timedelta
from typing import Dict, List

from back_testing import BackTester, DayTracker, OptionLegDayTracker, Trade
from back_testing_new_new import DayTrade, LegTrade, LegPair
from util import get_pickle_data, map_to_matrix

# this is called from flask router with back_test obj which was pickled earlier
from zerodha_classes import TradeMatrix


def analyze_data(back_tester: BackTester, trade_date: str, option_type: str):
    # analyze_data(back_tester, "2021-09-03", "PE")
    minute_str_list = get_minute_list()
    day_trackers: List[DayTracker] = [day_tracker for day_tracker in back_tester.day_trackers if
                                      day_tracker.trading_date == trade_date]
    if len(day_trackers) == 0:
        return {}
    day_tracker: DayTracker = day_trackers[0]
    short_minute_str_list = [re.sub(r':00$', '', min_str) for min_str in minute_str_list]
    # getting profit,profit perc,option prem data for individual legs
    option_data_list = get_option_data(day_tracker.option_leg_trackers, minute_str_list)
    plot_data = {'minutes': short_minute_str_list, 'expiry': day_tracker.nearest_expiry,
                 'optionPremData': option_data_list, 'totalProfit': round(day_tracker.get_current_profit(), 2)}
    nifty_plot_data = get_nifty_plot_data(day_tracker.nifty_min_data_dic, minute_str_list, day_tracker.trading_date)
    plot_data["niftyData"] = nifty_plot_data
    # total_profit_list = get_total_profit_list(minute_str_list, option_data_list)
    # plot_data['totalProfit'] = total_profit_list
    # plot_data['total_profit_sum'] = day_tracker.get_current_profit()
    return plot_data


def get_option_data(option_leg_trackers: List[OptionLegDayTracker], minute_str_list):
    option_data_list = []
    for option_leg_tracker in option_leg_trackers:
        ticker_candles_dic: Dict[
            str, {}] = option_leg_tracker.strike_ticker_candles_for_trade_date_dic
        value_with_index = get_list_value_with_index(ticker_candles_dic, minute_str_list, option_leg_tracker)
        strike_data = get_strike_plot_data(option_leg_tracker.strike_price, minute_str_list)
        option_prem_data = {"data": value_with_index, 'strikeData': strike_data,
                            'file': option_leg_tracker.option_file_name,
                            "optionType": option_leg_tracker.option_leg.option_type}
        # profit_data, profit_perc_data = get_profit_date(option_leg_tracker, minute_str_list)
        # option_prem_data['profit'] = profit_data
        # option_prem_data['profit_perc'] = profit_perc_data
        option_data_list.append(option_prem_data)
    return option_data_list


def get_profit_date(option_leg_tracker: OptionLegDayTracker, minute_str_list):
    ticker_candles_dic: Dict[
        str, {}] = option_leg_tracker.strike_ticker_candles_for_trade_date_dic
    trades: List[Trade] = option_leg_tracker.trades
    in_our_out = -1
    # having flag to make sure even for boundary condition i am considering those days as trade days
    is_boundary = False
    for key in ticker_candles_dic:
        is_boundary = False
        candle = ticker_candles_dic[key]
        candle['axis_ref_index'] = minute_str_list.index(key)
        matching_trade = len([trade for trade in trades if trade.trade_time == key]) > 0
        if matching_trade:
            is_boundary = True
            in_our_out = in_our_out * -1
        # if its open or close, treat i has 1
        if is_boundary:
            candle['in_our_out'] = 1
        else:
            candle['in_our_out'] = in_our_out
    traded_candles = [ticker_candles_dic[key] for key in ticker_candles_dic if
                      ticker_candles_dic[key]['in_our_out'] == 1]
    profit_reversal = (-1 if option_leg_tracker.option_leg.buy_or_sell == "sell" else 1)
    for candle in traded_candles:
        candle['profit'] = (float(candle['close']) - float(traded_candles[0]['close'])) * profit_reversal
        candle['profit_perc'] = float(candle['profit']) / float(traded_candles[0]['close'])
    profit_data = [[candle['axis_ref_index'], candle['profit']] for candle in traded_candles]
    profit_perc_data = [[candle['axis_ref_index'], candle['profit_perc']] for candle in traded_candles]
    return profit_data, profit_perc_data


# getting total profit by summing up indv profits
def get_total_profit_list(minutes_str_list, option_data_list):
    total_profit_list = []
    for index in range(len(minutes_str_list)):
        profit = None
        for option_data in option_data_list:
            min_profit = get_profit_by_min(option_data['profit'], index)
            if min_profit is not None:
                profit = profit if profit is not None else 0
                profit = profit + min_profit
        if profit is not None:
            total_profit_list.append([index, profit])
    return total_profit_list


def get_profit_by_min(profit_list, min_index):
    min_profit = [profit for profit in profit_list if profit[0] == min_index]
    if len(min_profit) == 0:
        return None
    else:
        return min_profit[0][1]


def get_minute_list():
    # print((entry_date_time_str, exit_date_time_str))
    entry_date_time = datetime.strptime('2021-01-01 09:15:00', '%Y-%m-%d %H:%M:%S')
    exit_date_time = datetime.strptime('2021-01-01 15:30:00', '%Y-%m-%d %H:%M:%S')
    time_diff = exit_date_time - entry_date_time
    minute_diff = (time_diff.total_seconds() / 60)
    minute_list = [entry_date_time + timedelta(minutes=it) for it in range(0, int(minute_diff + 1))]
    minute_str_list = [minute.strftime('%H:%M:%S') for minute in minute_list]
    return minute_str_list


# this is needed for highchart so that the trade could be marked in the graph
def get_list_value_with_index(candle_list_dic: Dict[str, tuple], minute_str_list: List[str],
                              option_leg_tracker: OptionLegDayTracker):
    trades: List[Trade] = option_leg_tracker.trades
    option_premiums_with_trade_marked = []
    start_premium = None
    for key in candle_list_dic:
        matching_trades = [trade for trade in trades if trade.trade_time == key]
        premium_index = minute_str_list.index(key)
        option_value = float(candle_list_dic[key]['close'])
        matching_trade = None
        if len(matching_trades) > 0:
            matching_trade = matching_trades[0]
        if matching_trade is not None:
            # when trade is started/ended at this time, modify the data so that its shown diff. in the graph
            option_trade_entry = {"marker": {
                "fillColor": '#FF0000',
                "lineWidth": 3,
                "lineColor": "#FF0000",
                "radius": 4
            }, "y": option_value, "x": premium_index}
            if start_premium is None:
                start_premium = option_value
            else:
                profit = (option_value - start_premium) * -1
                profit_perc = (profit / start_premium) * 100
                start_premium = None
                option_trade_entry['marker']['profit'] = profit
                option_trade_entry['marker']['profitPerc'] = round(profit_perc, 2)

            option_premiums_with_trade_marked.append(option_trade_entry)
        else:
            option_premiums_with_trade_marked.append([premium_index, option_value])
    return option_premiums_with_trade_marked


def get_highchart_option_data():
    return None


day_trades: List[DayTrade] = None


def get_leg_pair(trade_matrix: TradeMatrix, leg_trades: List[LegTrade]):
    time_str: str = trade_matrix.time
    strike_price_offset = trade_matrix.strike_selector_fn(0)
    pe_min_strike = f'{time_str}|{strike_price_offset[0]}'
    # atm minutes will have entries like -100 to 100 to get the itm and otm strikes.
    pe_leg_trade = [leg_trade for leg_trade in leg_trades if
                    pe_min_strike in leg_trade.atm_minutes and leg_trade.option_type == "PE"]
    ce_min_time = f'{time_str}|{strike_price_offset[1]}'
    ce_leg_trade = [leg_trade for leg_trade in leg_trades if
                    ce_min_time in leg_trade.atm_minutes and leg_trade.option_type == "CE"]

    if len(pe_leg_trade) > 0 and len(ce_leg_trade) > 0:
        leg_pair = LegPair("", copy.deepcopy(pe_leg_trade[0]), copy.deepcopy(ce_leg_trade[0]))
        return leg_pair


def get_high_chart_data(date: str, matrix_str):
    trade_matrix: TradeMatrix = map_to_matrix(matrix_str)
    global day_trades
    if day_trades is None:
        day_trades = get_pickle_data("day_trades_all_minute")
    filtered_day_trades = [day_trade for day_trade in day_trades if
                  date == day_trade.trade_date_str]
    leg_pair: LegPair = get_leg_pair(trade_matrix, filtered_day_trades[0].leg_trades)
    return leg_pair


# this is needed for highchart so that the trade could be marked in the graph
def get_list_value_with_(candle_list_dic: Dict[str, tuple], minute_str_list: List[str],
                         option_leg_tracker: OptionLegDayTracker):
    trades: List[Trade] = option_leg_tracker.trades
    option_premiums_with_trade_marked = []
    start_premium = None
    for key in candle_list_dic:
        matching_trades = [trade for trade in trades if trade.trade_time == key]
        premium_index = minute_str_list.index(key)
        option_value = float(candle_list_dic[key]['close'])
        matching_trade = None
        if len(matching_trades) > 0:
            matching_trade = matching_trades[0]
        if matching_trade is not None:
            # when trade is started/ended at this time, modify the data so that its shown diff. in the graph
            option_trade_entry = {"marker": {
                "fillColor": '#FF0000',
                "lineWidth": 3,
                "lineColor": "#FF0000",
                "radius": 4
            }, "y": option_value, "x": premium_index}
            if start_premium is None:
                start_premium = option_value
            else:
                profit = (option_value - start_premium) * -1
                profit_perc = (profit / start_premium) * 100
                start_premium = None
                option_trade_entry['marker']['profit'] = profit
                option_trade_entry['marker']['profitPerc'] = round(profit_perc, 2)

            option_premiums_with_trade_marked.append(option_trade_entry)
        else:
            option_premiums_with_trade_marked.append([premium_index, option_value])
    return option_premiums_with_trade_marked


def get_nifty_plot_data(nifty_data_dic: Dict[str, tuple], minute_str_list: List[str], date_str: str):
    nifty_min_data_with_index = []
    for index in range(len(minute_str_list)):
        time = minute_str_list[index]
        search_date_time_string = f'{date_str}T{time}+0530'
        if search_date_time_string in nifty_data_dic:
            nifty_min_data_with_index.append([index, nifty_data_dic[search_date_time_string]['close']])
    return nifty_min_data_with_index


def get_strike_plot_data(strike_price: float, minute_str_list: List[str]):
    strike_data_with_index = []
    for index in range(len(minute_str_list)):
        strike_data_with_index.append([index, strike_price])
    return strike_data_with_index
