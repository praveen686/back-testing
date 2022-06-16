import logging
import time
from typing import List

from kiteconnect import KiteTicker, KiteConnect
import threading

from trade_setup import DayTrade

logging.basicConfig(level=logging.DEBUG)

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="gui6ggv8t8t5almq")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

print(kite.login_url())
kite_url = 'https://kite.trade/connect/login?api_key=gui6ggv8t8t5almq&v=3'


# data = kite.generate_session("OZicDwL3zCwx9W5nS5VTax95aOH1izRg", api_secret="p6q7g13y509l5m5fpnw9tkr44rguh0qb")
# access_token = kite.set_access_token(data["access_token"])

# Initialise
# token gui6ggv8t8t5almq:


class MyTicker(threading.Thread):
    ticker_instance = None

    def __init__(self, tokens_to_subscribe: List[int], day_trade: DayTrade):
        threading.Thread.__init__(self)
        MyTicker.ticker_instance = self
        self.day_trade = day_trade
        self.kite_ticker = KiteTicker("gui6ggv8t8t5almq", day_trade.access_token)
        self.tokens_to_subscribe = tokens_to_subscribe

    def run(self):
        self.connect(False)

    def on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        logging.debug("Tickseeee: {}".format(ticks))
        for tick in ticks:
            self.day_trade.ltp[tick['instrument_token']] = tick['last_price']

    def on_connect(self, ws, response):
        logging.debug("start subscribing")
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        ws.subscribe(self.tokens_to_subscribe)

        # Set RELIANCE to tick in `full` mode.
        # ws.set_mode(ws.MODE_FULL, [738561])
        ws.set_mode(ws.MODE_LTP, [5633, 738561])

    def on_close(self, ws, code, reason):
        logging.debug("stopping connection")
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        # ws.stop()

    # Assign the callbacks.

    def connect(self, new_thread: bool):
        self.kite_ticker.on_ticks = self.on_ticks
        self.kite_ticker.on_connect = self.on_connect
        self.kite_ticker.on_close = self.on_close
        self.kite_ticker.connect(new_thread)

    def is_ticker_connected(self):
        return hasattr(self.kite_ticker, 'ws') and self.kite_ticker.is_connected()

    def stop_gracefully(self):
        self.kite_ticker.close()

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
# my_ticker = MyTicker()
# my_ticker.connect(False)
# x = threading.Thread(target=connect)
# x.start()
# print("reached here.....")
# time.sleep(10)
