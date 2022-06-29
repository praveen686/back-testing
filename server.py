from typing import Dict, List

from flask import Flask, request, jsonify, make_response, send_from_directory
from kiteconnect import KiteTicker, KiteConnect

import constants
import trade_setup
from trade_setup import DayTrade
from zerodha_classes import TradeMatrix
from AnalyzeData import analyze_data, get_high_chart_data
from util import get_pickle_data, write_pickle_data, get_today_date_in_str
from zerodha_algo_trader import TradePlacer, ZerodhaBrokingAlgo, PositionAnalyzer
from zerodha_api import ZerodhaApi
from zerodha_kiteconnect_algo_trading import TradeTicker

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


@app.route("/options", methods=["GET", "OPTIONS"])
# this sets the route to this page
def options():
    date = request.args.get('date')
    matrix_str = request.args.get('matrix_str')
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":  # The actual request following the preflight
        leg_pair = get_high_chart_data(date, matrix_str)
        return _corsify_actual_response(jsonify(leg_pair.serialize()))
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
    access_token = data['access_token']
    today_date_str: str = get_today_date_in_str()

    if today_date_str in trading_data_by_date:
        print(f'data already exist for the date:{today_date_str}, going to overwrite')
    day_trade = DayTrade(today_date_str, access_token)
    trading_data_by_date[today_date_str] = day_trade
    # day_trade is set so that, algo trader can calculate profit using the ltp set in the day trader by the ticker

    # write_pickle_data("access_token", data["access_token"])
    return {"status": True}


@app.route("/startAnalyzer", methods=["GET", "OPTIONS"])
def startAnalyzer():
    zerodha_algo_trader = ZerodhaBrokingAlgo(is_testing=False, sleep_time=5)
    zerodha_api = ZerodhaApi(False)
    # this checking is done so that there will be only one instance of Trade Placer. Like Singleton class in Java
    trade_placer = TradePlacer.trade_placer_instance
    if trade_placer is None:
        trade_placer = TradePlacer()
        trade_placer.zerodha_algo_trader = zerodha_algo_trader
        trade_placer.zerodha_api = zerodha_api
        trade_placer.start()
    position_analyzer = PositionAnalyzer.position_analyzer
    if position_analyzer is None:
        position_analyzer = PositionAnalyzer()
        position_analyzer.zerodha_algo_trader = zerodha_algo_trader
        position_analyzer.start()


@app.route("/testtest", methods=["GET", "OPTIONS"])
def test_test():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":  # The actual request following the preflight
        return _corsify_actual_response(jsonify([{"id": 1}]))
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))


@app.route("/setenctoken", methods=["GET", "OPTIONS"])
def settoken():
    enc_token = request.args.get('encToken')
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":  # The actual request following the preflight
        trading_data_by_date = trade_setup.AllTrade.trading_data_by_date
        today_date_str: str = get_today_date_in_str()
        if today_date_str not in trading_data_by_date:
            trading_data_by_date[today_date_str] = DayTrade(today_date_str, None)
        day_trade: DayTrade = trading_data_by_date[today_date_str]
        day_trade.enctoken = enc_token
        return _corsify_actual_response(jsonify([{"id": 1}]))
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))


@app.route("/ticker", methods=["GET", "OPTIONS"])
def ticker():
    trade_ticker = TradeTicker.ticker_instance
    return trade_ticker.day_trade.ltp


@app.route("/findmargin", methods=["GET", "OPTIONS"])
def find_required_margin():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    max_leg_price = int(request.args.get('buyLegPrice'))
    trade_placer = TradePlacer.trade_placer_instance
    algo = ZerodhaBrokingAlgo(False, 0)
    zerodha_api = ZerodhaApi(False)
    if trade_placer is None:
        trade_placer = TradePlacer()
        trade_placer.zerodha_algo_trader = algo
        trade_placer.zerodha_api = zerodha_api

    today_date_str = get_today_date_in_str()
    day_trade: DayTrade = trade_setup.AllTrade.trading_data_by_date[today_date_str]
    trade_matrix: List[TradeMatrix] = trade_placer.get_not_executed_trades()
    straddle = algo.prepare_option_legs(trade_matrix[0], day_trade, max_leg_price)
    response = zerodha_api.get_straddle_with_final_margin(straddle, day_trade.enctoken)
    return _corsify_actual_response(jsonify(response))


@app.route("/stopticker", methods=["GET", "OPTIONS"])
def stop_ticker():
    trade_ticker = TradeTicker.ticker_instance
    if trade_ticker is not None:
        trade_ticker.stop_gracefully()
        TradeTicker.ticker_instance = None
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
    # trade_placer = TradePlacer()
    # trade_placer.start()
