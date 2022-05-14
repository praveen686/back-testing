from typing import Dict, List

from zerodha_classes import Straddle
from zerodha_kiteconnect_algo_trading import MyTicker


class DayTradingData:

    def __init__(self, date_str: str, access_token: str):
        self.date_str: str = date_str
        self.access_token: str = access_token
        self.straddle_by_time: Dict[str, Straddle] = {}


class Data:
    access_token: str = None
    my_ticker: MyTicker = None
    ltp: Dict[str, float] = {}
    trade_intervals_by_week_day: Dict[int, List[str]] = {4: ["09:20", "09:40"]}
    day_trading_data: Dict[str, DayTradingData] = {}
