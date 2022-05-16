from typing import Dict

from flask import Flask, request, jsonify, make_response, send_from_directory
from kiteconnect import KiteTicker, KiteConnect

import constants
from trade_setup import DayTrade
import trade_setup
from AnalyzeData import analyze_data
from util import get_pickle_data, write_pickle_data, get_today_date_in_str
from zerodha_algo_trader import TradePlacer, ZerodhaBrokingAlgo, PositionAnalyzer
from zerodha_kiteconnect_algo_trading import MyTicker

from os.path import exists

app = Flask(__name__, static_folder="hello")
app.config['SECRET_KEY'] = "secretkey123"
kite = KiteConnect(api_key="gui6ggv8t8t5almq")


@app.route('/ui/<path:path>')
def send_report(path):
    return send_from_directory('trade-ui/build', path)


@app.route('/static/<path:path>')
def send_static_files(path):
    return send_from_directory('trade-ui/build/static', path)


@app.route('/starttimer', methods=["GET", "OPTIONS"])
def start_timer():
    trade_placer = TradePlacer()
    trade_placer.start()
    return {"success": True}


@app.route("/orders", methods=["GET", "OPTIONS"])
# this sets the route to this page
def home():
    date = request.args.get('date')
    option_type = request.args.get('option_type')
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":  # The actual request following the preflight
        closes = analyze_data(None, date, option_type)
        return _corsify_actual_response(jsonify(closes))
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))


@app.route("/zerodha", methods=["GET", "OPTIONS"])
# this sets the route to this page
def zerodha():
    file_exists = exists("trading_data_by_date")
    if file_exists:
        trading_data_by_date: Dict[str, trade_setup.DayTrade] = get_pickle_data("trading_data_by_date")
    else:
        trading_data_by_date: Dict[str, trade_setup.DayTrade] = {}
    trade_setup.AllTrade.trading_data_by_date = trading_data_by_date
    kite_url = 'https://kite.trade/connect/login?api_key=gui6ggv8t8t5almq&v=3'
    print(request.args)
    data = kite.generate_session(request.args['request_token'], api_secret=constants.API_SECRET)
    print(data["access_token"])
    access_token = data['access-token']
    today_date_str: str = get_today_date_in_str()
    day_trade: DayTrade = trading_data_by_date[today_date_str]
    if day_trade is not None:
        raise Exception(f'data should not be present for the date:{today_date_str}')

    # this checking is done so that there will be only one instance of Trade Placer. Like Singleton class in Java
    trade_placer = TradePlacer.trade_placer_instance
    if trade_placer is None:
        trade_placer = TradePlacer()
        trade_placer.start()
    position_analyzer = PositionAnalyzer.position_analyzer
    if position_analyzer is None:
        position_analyzer = PositionAnalyzer()
        position_analyzer.start()
    day_trade = DayTrade(today_date_str, access_token)
    trading_data_by_date[today_date_str] = day_trade
    # day_trade is set so that, algo trader can calculate profit using the ltp set in the day trader by the ticker
    zerodha_algo_trader = ZerodhaBrokingAlgo(is_testing=False, sleep_time=5, day_trade=day_trade,)
    trade_placer.zerodha_algo_trader = zerodha_algo_trader
    position_analyzer.zerodha_algo_trader = zerodha_algo_trader

    # write_pickle_data("access_token", data["access_token"])
    return {"status": True}


@app.route("/ticker", methods=["GET", "OPTIONS"])
def ticker():
    access_token = TradeData.Data.access_token
    if access_token is None:
        access_token = get_pickle_data("access_token")
        TradeData.Data.access_token = access_token
    if access_token is None:
        raise Exception("no access token present")
    if TradeData.Data.my_ticker is not None:
        raise Exception("ticker already present!!")
    my_ticker = MyTicker(access_token)
    my_ticker.start()
    # my_ticker.connect(True)
    TradeData.Data.my_ticker = my_ticker
    return {"": ""}


@app.route("/stopticker", methods=["GET", "OPTIONS"])
def stop_ticker():
    my_ticker = TradeData.Data.my_ticker
    if my_ticker is not None:
        my_ticker.stop_gracefully()
        TradeData.Data.my_ticker = None
    else:
        raise Exception("ticker not present")
    return {"status": "done"}


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


# back_tester = get_pickle_data("back_tester")
if __name__ == "__main__":
    app.run()
    trade_placer = TradePlacer()
    trade_placer.start()
