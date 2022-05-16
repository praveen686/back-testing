import random
from typing import Dict

import requests

import constants
from zerodha_classes import Position, Order
from util import write_pickle_data, get_pickle_data
import requests
import json
import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Authorization': 'enctoken D1tQVzvB7+qZJjrBVYiQHd8kA5htch1m1CjkFfAnldIA8hl22Tqj7e+mXK5hRsDspDTFNHjntF9fm+9ktb2uQXQGnHR/ammbN2JCTxfYVdJEujvSFgi5yQ==',
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"98\", \"Google Chrome\";v=\"98\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-kite-userid": "XQ9712",
    "x-kite-version": "2.9.10"
}
zerodha_header = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "enctoken Eh7i4rCeXJ3FTH8so0pA1qk2FLyKg3X7B47yQVk+0C3guXbg8JWHIzGAgkBpwyuVkR9jLeygw3wIjRpSlKpkJjNPj9ZYIve9D3cnT2/8uptl5oQnI0AkJw==",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-kite-userid": "NNV006",
    "x-kite-version": "2.9.11"
}

nse_header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}


class ZerodhaApi:
    def __init__(self, is_testing: bool):
        self.is_testing = is_testing
        print("")

    def fetch_nse_data(self):
        nse_option_chain_url = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
        if self.is_testing:
            return get_pickle_data('nse_json_data')
        else:
            nse_response = requests.get(nse_option_chain_url, headers=nse_header)
            nse_json_data = json.loads(nse_response.text)
            write_pickle_data('nse_json_data', nse_json_data)
            return nse_json_data

    def exit_all_open_positions(self, zerodha_positions, access_token: str):
        open_positions = [position for position in zerodha_positions if position['quantity'] > 0]
        for position in open_positions:
            buy_quantity = position['buy_quantity']
            sell_quantity = position['sell_quantity']
            position['transaction_type'] = 'SELL' if buy_quantity > 0 else 'BUY'
            self.exit_position(position, access_token)

    def exit_position(self, position, access_token: str):
        data = {
            "exchange": "NFO",
            "tradingsymbol": "BANKNIFTY2241341700CE",
            "transaction_type": "BUY",
            "order_type": "MARKET",
            "quantity": "25",
            "price": "0",
            "product": "MIS",
            "validity": "DAY",
            "validity_ttl": "1",
            "disclosed_quantity": "0",
            "trigger_price": "0",
            "variety": "regular",
            "gtt_params": "",
            "user_id": "NNV006"
        }
        data['quantity'] = position['quantity']
        data['tradingsymbol'] = position['tradingsymbol']
        data['transaction_type'] = position['transaction_type']
        if self.is_testing:
            response = {"order_id": '220413000593839'}
            place_order = Order(-1)
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.post("https://kite.zerodha.com/oms/orders/regular", headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception occured while placing order {position.symbol}:{position.sell_or_buy}:{position.option_type}')

    def add_basket_items(self, basket_name: str, access_token: str):
        data = {
            "exchange": "NFO",
            "tradingsymbol": "BANKNIFTY2241341700CE",
            "weight": 0,
            "params": {"transaction_type": "BUY", "product": "MIS", "order_type": "MARKET", "validity": "DAY",
                       "validity_ttl": "1", "variety": "regular", "quantity": "25", "price": "0",
                       "trigger_price": "0", "disclosed_quantity": "0"}

        }
        if self.is_testing:
            response = {"order_id": '220413000593839'}
            place_order = Order(-1)
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.post("https://kite.zerodha.com/api/baskets", headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception occured while creating basket {basket_name}')
            resp_json_data = json.loads(response.text)
            basket_id = resp_json_data['data']
            return basket_id

    def create_new_basket(self, basket_name, access_token: str):
        data = {
            "name": "test"
        }
        data['name'] = basket_name
        if self.is_testing:
            response = {"order_id": '220413000593839'}
            place_order = Order(-1)
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.post("https://kite.zerodha.com/oms/orders/regular", headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception occured while creating basket {basket_name}')
            resp_json_data = json.loads(response.text)
            basket_id = resp_json_data['data']
            return basket_id

    def place_regular_order(self, position: Position, access_token: str, quantity: int):
        data = {
            "exchange": "NFO",
            "tradingsymbol": "BANKNIFTY2241341700CE",
            "transaction_type": "BUY",
            "order_type": "MARKET",
            "quantity": "25",
            "price": "0",
            "product": "MIS",
            "validity": "DAY",
            "validity_ttl": "1",
            "disclosed_quantity": "0",
            "trigger_price": "0",
            "variety": "regular",
            "gtt_params": "",
            "user_id": "NNV006"
        }
        data['quantity'] = quantity
        data['tradingsymbol'] = position.symbol
        data['transaction_type'] = position.sell_or_buy
        if self.is_testing:
            response = {"order_id": '220413000593839'}
            place_order = Order(-1)
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.post("https://kite.zerodha.com/oms/orders/regular", headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception occured while placing order {position.symbol}:{position.sell_or_buy}:{position.option_type}')
            resp_json_data = json.loads(response.text)
            order_id = resp_json_data['data']['order_id']
            place_order = Order(order_id)
        position.place_order = place_order
        return response

    def place_sl_order(self, position: Position, sl: float, quantity: int, access_token: str):
        sl_trigger_price = round(position.get_premium() * sl)
        sl_other_price = round(sl_trigger_price * 2)
        data = {
            "exchange": "NFO",
            "tradingsymbol": "BANKNIFTY2241341700CE",
            "transaction_type": "BUY",
            "order_type": "MARKET",
            "quantity": "25",
            "price": "0",
            "product": "MIS",
            "validity": "DAY",
            "disclosed_quantity": "0",
            "trigger_price": "0",
            "squareoff": 0,
            "stoploss": 0,
            "trailing_stoploss": 0,
            "variety": "regular",
            "user_id": "NNV006"
        }

        data['tradingsymbol'] = position.symbol
        data['quantity'] = quantity
        data['order_type'] = "SL"
        data['price'] = sl_other_price
        data['trigger_price'] = sl_trigger_price
        if self.is_testing:
            response = {}
            sl_order = Order(-1)
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.post("https://kite.zerodha.com/oms/orders/regular", headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception occured while placing SL order tr.price:{sl_trigger_price} {position.symbol}:{position.sell_or_buy}:{position.option_type}')
            resp_json_data = json.loads(response.text)
            order_id = resp_json_data['data']['order_id']
            sl_order = Order(order_id)
        position.sl_order = sl_order
        print(response)

    def get_latest_b_nifty(self, access_token: str):
        current_time = datetime.datetime.now()
        today_date_str = current_time.strftime("%Y-%m-%d")
        yesterday = current_time - datetime.timedelta(1)
        yesterday_date_str = yesterday.strftime("%Y-%m-%d")
        kite_url = f'https://api.kite.trade/quote?i=NSE:NIFTY+BANK'
        print(kite_url)
        if self.is_testing:
            spot_price = 34763
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.get(kite_url, headers=zerodha_header)
            spot_price = json.loads(response.text)['data']['NSE:NIFTY BANK']["last_price"]
        return round(float(spot_price))

    def get_zerodha_open_positions(self, access_token: str):
        position_url = f'https://kite.zerodha.com/oms/portfolio/positions?hello={random.random()}'

        if self.is_testing:
            json_data = get_pickle_data("zerodha_positions")
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.get(position_url, headers=zerodha_header)
            json_data = json.loads(response.text)

        # write_pickle_data("zerodha_positions", json.loads(response.text))
        positions = json_data["data"]["day"]
        # print(response)
        return positions

    def get_zerodha_open_orders(self, access_token: str):
        if self.is_testing:
            orders_json = get_pickle_data("zerodha_orders")
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            order_url = "https://kite.zerodha.com/oms/orders"
            response = requests.get(order_url, headers=zerodha_header)
            orders_json = json.loads(response.text)
            write_pickle_data("zerodha_orders", orders_json)
        return orders_json["data"]

    def modify_stop_loss(self, position: Position, sl_trigger_price: float, sl_other_price: float, access_token: str):
        data = {
            "exchange": "NFO",
            "tradingsymbol": "BANKNIFTY2241341700CE",
            "transaction_type": "BUY",
            "order_type": "MARKET",
            "quantity": "25",
            "price": "0",
            "product": "MIS",
            "validity": "DAY",
            "disclosed_quantity": "0",
            "trigger_price": "0",
            "squareoff": 0,
            "stoploss": 0,
            "trailing_stoploss": 0,
            "variety": "regular",
            "user_id": "NNV006"
        }
        data['tradingsymbol'] = position.symbol
        data['quantity'] = position.quantity
        data['order_type'] = "SL"
        data['price'] = sl_other_price
        data['trigger_price'] = sl_trigger_price
        data['order_id'] = position.sl_order.order_id
        if self.is_testing:
            response = {}
        else:
            ZerodhaApi.set_auth_header(zerodha_header, access_token)
            response = requests.put(f'https://kite.zerodha.com/oms/orders/regular/{position.sl_order.order_id}',
                                    headers=zerodha_header, data=data)
            if response.status_code != 200:
                raise Exception(
                    f'exception while placing modify sl order trigger price:{sl_trigger_price} {position.symbol}:{position.sell_or_buy}:{position.option_type}')
        print(response)

    @staticmethod
    def set_auth_header(header: Dict, access_token: str):
        header['authorization'] = f'token {constants.API_KEY}:{access_token}'


