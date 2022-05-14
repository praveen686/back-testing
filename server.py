from flask import Flask, request, jsonify, make_response, send_from_directory
from kiteconnect import KiteTicker, KiteConnect

import TradeData
from AnalyzeData import analyze_data
from util import get_pickle_data, write_pickle_data
from zerodha_algo_trader import TradePlacer
from zerodha_kiteconnect_algo_trading import MyTicker

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
    kite_url = 'https://kite.trade/connect/login?api_key=gui6ggv8t8t5almq&v=3'
    print(request.args)
    data = kite.generate_session(request.args['request_token'], api_secret="p6q7g13y509l5m5fpnw9tkr44rguh0qb")
    print(data["access_token"])
    write_pickle_data("access_token", data["access_token"])
    TradeData.Data.access_token = str(data["access_token"])
    return {"": ""}


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
