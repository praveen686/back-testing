from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask import Flask, request, jsonify, make_response
from kiteconnect import KiteTicker, KiteConnect

from AnalyzeData import analyze_data
from util import get_pickle_data
from zerodha_kiteconnect_algo_trading import MyTicker

app = Flask(__name__)
app.config['SECRET_KEY'] = "secretkey123"
kite = KiteConnect(api_key="gui6ggv8t8t5almq")


@app.route("/orders", methods=["GET", "OPTIONS"])
# this sets the route to this page
def home():
    date = request.args.get('date')
    option_type = request.args.get('option_type')
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":  # The actual request following the preflight
        closes = analyze_data(back_tester, date, option_type)
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
    return {"": ""}


@app.route("/ticker", methods=["GET", "OPTIONS"])
def ticker():
    my_ticker = MyTicker()
    my_ticker.connect(True)
    return {"": ""}


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


back_tester = get_pickle_data("back_tester")
if __name__ == "__main__":
    app.run()
