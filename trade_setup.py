from typing import Dict, List

from zerodha_classes import Straddle
from zerodha_kiteconnect_algo_trading import MyTicker


class DayTrade:
    ticker_tracker: MyTicker = None

    def __init__(self, date_str: str, access_token: str):
        self.date_str: str = date_str
        self.access_token: str = access_token
        self.straddle_by_time: Dict[str, Straddle] = {}
        self.ltp: Dict[int, float] = {}


class AllTrade:
    trade_intervals_by_week_day: Dict[int, List[str]] = {4: ["09:20|1.2", "09:40|1.2"]}
    trading_data_by_date: Dict[str, DayTrade] = {}
