from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask import Flask, request, jsonify, make_response

from AnalyzeData import analyze_data
from util import get_pickle_data

app = Flask(__name__)
app.config['SECRET_KEY'] = "secretkey123"


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
