import threading
import time
import calendar
from typing import List, Dict
import requests
import json
import datetime

from option_util import round_nearest, get_instrument_prefix
from util import write_pickle_data, get_pickle_data, get_today_date_in_str
from zerodha_api import ZerodhaApi
from zerodha_classes import *
from os.path import exists


class ZerodhaBrokingAlgo:
    def __init__(self, is_testing: bool, sleep_time: int):
        print("")
        self.is_testing = is_testing
        self.straddle_list: List[Straddle] = []
        self.zerodha_api = ZerodhaApi(is_testing)
        self.zerodha_positions: List[Dict] = []
        self.sleep_time = sleep_time

    def prepare_option_legs(self, sl: float, quantity: int) -> Straddle:
        ce_option_type = "CE"
        pe_option_type = "PE"
        option_sell = "SELL"
        option_buy = "BUY"
        # nse_json_data = get_pickle_data('nse_json_data')
        spot_price = self.zerodha_api.get_latest_b_nifty()
        nse_json_data = self.zerodha_api.fetch_nse_data()
        atm_strike_price = round_nearest(spot_price, 100)

        strike_price_list = nse_json_data['records']['data']
        nearest_expiry_date = nse_json_data['records']['expiryDates'][0]

        # pe_premium = get_strike_price_premium(strike_price_list, nearest_expiry_date, pe_option_type, strike_price)
        # ce_premium = get_strike_price_premium(strike_price_list, nearest_expiry_date, ce_option_type, strike_price)
        # getting the buy strike price for the given expiry to reduce the margin
        buy_pe_strike_entry = self.get_buy_leg(strike_price_list, nearest_expiry_date, pe_option_type, 4, spot_price)
        buy_ce_strike_entry = self.get_buy_leg(strike_price_list, nearest_expiry_date, ce_option_type, 4, spot_price)

        buy_pe_position = self.get_position(nearest_expiry_date, buy_pe_strike_entry['strikePrice'], spot_price,
                                            pe_option_type,
                                            option_buy, -1, quantity)
        buy_ce_position = self.get_position(nearest_expiry_date, buy_ce_strike_entry['strikePrice'], spot_price,
                                            ce_option_type,
                                            option_buy, -1, quantity)

        sell_pe_position = self.get_position(nearest_expiry_date, atm_strike_price, spot_price, pe_option_type,
                                             option_sell, sl, quantity)
        sell_ce_position = self.get_position(nearest_expiry_date, atm_strike_price, spot_price, ce_option_type,
                                             option_sell, sl, quantity)

        straddle = Straddle(buy_pe_position, buy_ce_position, sell_pe_position, sell_ce_position)
        return straddle

    def get_position(self, nearest_expiry_date: str, strike_price: float, spot_price: float, option_type: str,
                     sell_or_buy: str,
                     sl: float, quantity: int):
        symbol = self.generate_ticker_symbol(nearest_expiry_date, strike_price, option_type)
        position = Position(symbol, option_type, sell_or_buy, quantity, spot_price, strike_price, sl)
        return position

    def get_buy_leg(self, strike_price_list, nearest_expiry_date, option_type: str, lowest_price, spot_price: float):
        if option_type == "PE":
            strike_price_list = [strike_price_data for strike_price_data in strike_price_list if
                                 strike_price_data['strikePrice'] < spot_price and strike_price_data[
                                     'expiryDate'] == nearest_expiry_date]
        else:
            strike_price_list = [strike_price_data for strike_price_data in strike_price_list if
                                 strike_price_data['strikePrice'] > spot_price and strike_price_data[
                                     'expiryDate'] == nearest_expiry_date]
        buy_pe_strike_prices = [
            {"lp": strike_price_data[option_type]['lastPrice'], "strikePrice": strike_price_data['strikePrice'],
             option_type: strike_price_data[option_type]}
            for strike_price_data in strike_price_list
            if (option_type in strike_price_data) and
               strike_price_data[option_type]['lastPrice'] < lowest_price and strike_price_data[option_type][
                   'lastPrice'] > 1]
        buy_pe_strike_prices.sort(key=lambda x: x['lp'])
        if len(buy_pe_strike_prices) == 0:
            raise Exception(f'no strike price present below {lowest_price}')
        buy_pe_strike_price = buy_pe_strike_prices[0]
        print(buy_pe_strike_prices)
        return buy_pe_strike_price

    def get_strike_price_premium(self, strike_price_list, nearest_expiry_date, option_type: str, strike_price):
        strike_prices = [
            {"lp": strike_price_data[option_type]['lastPrice'], "strikePrice": strike_price_data['strikePrice'],
             option_type: strike_price_data[option_type]}
            for strike_price_data in strike_price_list
            if strike_price_data['expiryDate'] == nearest_expiry_date and (option_type in strike_price_data) and
               strike_price_data[option_type]['strikePrice'] == strike_price]
        strike_price = strike_prices[0]
        print(strike_price)
        return strike_price

    def generate_ticker_symbol(self, expiry_day_string, strike_price, option_type):
        expiry_date = datetime.datetime.strptime(expiry_day_string, "%d-%b-%Y")
        expiry_date_diff_format = expiry_date.strftime("%Y-%m-%d")
        prefix = get_instrument_prefix(expiry_date_diff_format, "BANKNIFTY")
        return f'{prefix}{strike_price}{option_type}'

    def attach_zerodha_order(self, straddle, zerodha_orders: List[Dict], order_type: str):
        manual_positions = [straddle.sell_pe_position, straddle.sell_ce_position]
        for manual_position in manual_positions:
            if order_type == "REGULAR" or order_type == "BOTH":
                matched_zerodha_orders = [order for order in zerodha_orders if
                                          manual_position.place_order.order_id == order["order_id"]]
                if len(matched_zerodha_orders) > 0:
                    manual_position.place_order.zerodha_order = matched_zerodha_orders[0]
            if order_type == "SL" or order_type == "BOTH":
                matched_zerodha_orders = [order for order in zerodha_orders if
                                          manual_position.sl_order.order_id == order["order_id"]]
                if len(matched_zerodha_orders) > 0:
                    manual_position.sl_order.zerodha_order = matched_zerodha_orders[0]

    def place_straddle_order(self, sl: float, quantity: int):
        # load existing straddle if any from the file and populate straddle_list instance variable
        self.load_straddles_from_file()
        straddle = self.prepare_option_legs(sl, quantity)
        self.straddle_list.append(straddle)
        self.zerodha_api.place_regular_order(straddle.buy_pe_position)
        time.sleep(self.sleep_time)
        self.zerodha_api.place_regular_order(straddle.buy_ce_position)
        time.sleep(self.sleep_time)
        self.zerodha_api.place_regular_order(straddle.sell_pe_position)
        time.sleep(self.sleep_time)
        self.zerodha_api.place_regular_order(straddle.sell_ce_position)

        # ideally this should be handled in the place order method but for the testing its manually assigned.

        if self.is_testing:
            straddle.sell_pe_position.place_order.order_id = '220413000657870'
            straddle.sell_ce_position.place_order.order_id = '220413000645744'

        time.sleep(self.sleep_time)
        # this will get the placed orders from zerodha and attaches it to 'placed_order' using the order id present
        # todo will have to remove this based on response from placed order
        zerodha_orders = self.zerodha_api.get_zerodha_open_orders()
        self.attach_zerodha_order(straddle, zerodha_orders, "REGULAR")
        # only once above orders are set to the position, you can place sl order as SL order relies on current premium
        # to come with SL trigger amount
        time.sleep(self.sleep_time)
        self.zerodha_api.place_sl_order(straddle.sell_pe_position, sl, quantity)
        time.sleep(self.sleep_time)
        self.zerodha_api.place_sl_order(straddle.sell_ce_position, sl, quantity)
        if self.is_testing:
            straddle.sell_pe_position.sl_order.order_id = '220413001614601'
            straddle.sell_ce_position.sl_order.order_id = '220413001261330'
        time.sleep(self.sleep_time)
        # again fetching the sl orders back from zerodha and attaching the same
        zerodha_orders = self.zerodha_api.get_zerodha_open_orders()
        # todo check whether you need to call separately to pull the orders or is it part of the order place response
        self.attach_zerodha_order(straddle, zerodha_orders, "SL")
        # this will save the final list present under straddle_list
        self.save_straddle_in_file()

    # def get_average_sell_price(self, symbol: str, positions: List):
    #     symbol_position = [position for position in positions if
    #                        position["tradingsymbol"] == symbol][0]
    #     return float(symbol_position['sell_price'])

    def analyze_existing_positions(self):
        # load existing straddle if any from the file
        self.load_straddles_from_file()

        # this is to avoid calling it for second straddle if its already invoked
        is_order_n_position_fetched = False
        for straddle in self.straddle_list:
            # if not self.is_both_sl_triggered():
            if self.is_both_sl_triggered(straddle):
                print("both the sl hit; returning")
                return
            # you need latest to position to find out the ltp for each of the positions
            if not is_order_n_position_fetched:
                self.zerodha_positions = self.zerodha_api.get_zerodha_open_positions()
                total_profit = self.get_current_profit(self.zerodha_positions)
                print(f'total profit:{total_profit}')
                time.sleep(self.sleep_time)
                zerodha_orders = self.zerodha_api.get_zerodha_open_orders()
                self.attach_zerodha_order(straddle, zerodha_orders, "BOTH")
                is_order_n_position_fetched = True

            sell_pe_position: Position = straddle.sell_pe_position
            sell_ce_position: Position = straddle.sell_ce_position

            self.handle_c2c_sl(sell_pe_position, sell_ce_position)
            self.handle_c2c_sl(sell_ce_position, sell_pe_position)

            # check the ltp of existing positions and set the trailing sl
            if not sell_pe_position.sl_order.is_trailing_sl_set:
                self.handle_trailing_sl(sell_pe_position)
            if not sell_ce_position.sl_order.is_trailing_sl_set:
                self.handle_trailing_sl(sell_ce_position)
        self.save_straddle_in_file()

    # setting other leg to c2c if a leg is hit
    def handle_c2c_sl(self, hit_position: Position, other_position: Position):
        if hit_position.is_sl_hit() and (
                other_position.is_c2c_enabled() is False and other_position.is_sl_hit() is False):
            sl_trigger_price = round(other_position.get_premium())
            sl_other_price = round(sl_trigger_price * 2)
            time.sleep(self.sleep_time)
            self.zerodha_api.modify_stop_loss(other_position, sl_trigger_price, sl_other_price)
            other_position.sl_order.is_c2c_set = True

    def handle_trailing_sl(self, algo_position: Position):
        zerodha_positions = [zerodha_position for zerodha_position in self.zerodha_positions if
                             zerodha_position['tradingsymbol'] == algo_position.symbol]
        if len(zerodha_positions) == 0:
            raise Exception(f'symbol {algo_position.symbol} not in the list')
        placed_order = algo_position.place_order
        sell_price = float(placed_order.zerodha_order["average_price"])
        last_price = float(zerodha_positions[0]["last_price"])
        # todo see whether you could keep on modifying trailing sl
        if (last_price / sell_price) < .2:
            print("set trailing stop loss")
            new_trigger_price = round(sell_price * .3)
            other_price = new_trigger_price * 2
            time.sleep(self.sleep_time)
            self.zerodha_api.modify_stop_loss(algo_position, new_trigger_price, other_price)
            algo_position.sl_order.is_trailing_sl_set = True

    def get_current_profit(self, positions):
        profit = sum([position["pnl"] for position in positions])
        print([position["pnl"] for position in positions])
        open_sell_positions = [position for position in positions if
                               position["quantity"] > 0 and position['sell_quantity'] > 0]
        return profit

    def is_both_sl_triggered(self, straddle) -> bool:
        sell_pe_position: Position = straddle.sell_pe_position
        sell_ce_position: Position = straddle.sell_ce_position
        return sell_pe_position.is_sl_hit() and sell_ce_position.is_sl_hit()

    def save_straddle_in_file(self):
        today_date_str = get_today_date_in_str()
        write_pickle_data(f'algo_trading_data/straddle_data_{today_date_str}', self.straddle_list)

    def load_straddles_from_file(self):
        today_date_str = get_today_date_in_str()
        file_exists = exists(f'algo_trading_data/straddle_data_{today_date_str}')
        if file_exists:
            self.straddle_list = get_pickle_data(f'algo_trading_data/straddle_data_{today_date_str}')

    def generate_straddle_from_existing_zerodha_position(self):
        # zerodha_positions = self.zerodha_api.get_zerodha_open_positions()
        zerodha_orders = get_pickle_data("zerodha_orders")
        sell_orders = [order for order in zerodha_orders if order['transaction_type'] == "SELL"]
        # for orders in sell_orders:
        #     # position = Position(symbol, option_type, sell_or_buy, quantity, spot_price, strike_price, sl)
        #     print(position)
        # position1= Position(symbol, "PE", "SELL", 25, spot_price, strike_price, sl)


class TradePlacer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        start_time = time.time()
        check_interval = 5
        while True:
            local_start_time = time.time()
            print("about to check")
            # zerodha.analyze_existing_positions()
            local_end_time = time.time()
            print(f'done checking; time taken:{round(local_end_time - local_start_time)}')
            time.sleep(check_interval - ((time.time() - start_time) % check_interval))
            local_end_time = time.time()
            print(f'done with sleep; time taken:{round(local_end_time - local_start_time)}')
