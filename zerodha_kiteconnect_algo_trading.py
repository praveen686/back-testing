import logging
import time

from kiteconnect import KiteTicker, KiteConnect
import threading

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


class MyTicker:
    def __init__(self):
        self.kws = KiteTicker("gui6ggv8t8t5almq", 'wlfylKrL1KjreOnXy47b02TVAl7aHQgS')

    def on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        logging.debug("Tickseeee: {}".format(ticks))

    def on_connect(self, ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        ws.subscribe([738561, 5633])

        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_FULL, [738561])

    def on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        ws.stop()

    # Assign the callbacks.

    def connect(self, new_thread: bool):
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.connect(new_thread)


# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
# my_ticker = MyTicker()
# my_ticker.connect(False)
# x = threading.Thread(target=connect)
# x.start()
# print("reached here.....")
# time.sleep(10)
