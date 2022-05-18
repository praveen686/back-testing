from typing import Dict, List

from zerodha_classes import Straddle


# from zerodha_kiteconnect_algo_trading import MyTicker

# ticker_tracker: MyTicker = None


class DayTrade:
    #

    def __init__(self, date_str: str, access_token: str):
        self.date_str: str = date_str
        self.access_token: str = access_token
        self.enctoken: str = ""
        self.straddle_by_time: Dict[str, Straddle] = {}
        self.ltp: Dict[int, float] = {}


class AllTrade:
    trade_intervals_by_week_day: Dict[int, List[str]] = {
        0: ["09:40|1.2|100|60", "10:40|1.2|100|60", "11:40|1.2|100|60"],
        1: ["09:40|1.2|100|50", "10:40|1.2|100|50", "11:40|1.2|100|50"],
        2: ["09:40|1.6|130|65", "10:40|1.6|130|65", "11:40|1.6|130|65"],
        3: ["09:20|1.6|130|65", "10:40|1.6|130|65", "11:40|1.6|130|65"],
        4: ["09:40|1.2|100|60", "10:40|1.2|100|60", "11:40|1.2|100|60"]
    }

    trading_data_by_date: Dict[str, DayTrade] = {}

#
# result_mon = analyze_interval_trades(["0940", "1040", "1140", "1240"], '2021-01-01', '2022-02-11', 1.2, -1, 50,
#                                      stop_at_target=-1, allowed_week_day=0, is_c2c_enabled=True)
# result_tue = analyze_interval_trades(["0940", "1040", "1140", "1240"], '2021-01-01', '2022-02-11', 1.2, -1, 50,
#                                      stop_at_target=-1, allowed_week_day=1, is_c2c_enabled=True)
# result_wed = analyze_interval_trades(["0940", "1040", "1140", "1240"], '2021-01-01', '2022-02-11', 1.6, 130, 65,
#                                      stop_at_target=-1, allowed_week_day=2, is_c2c_enabled=True)
# result_thu = analyze_interval_trades(["0920", "1040", "1140", "1240"], '2021-01-01', '2022-02-11', 1.6, 130, 65,
#                                      stop_at_target=-1, allowed_week_day=3, is_c2c_enabled=True)
# result_fri = analyze_interval_trades(["0940", "1040", "1140", "1240"], '2021-01-01', '2022-02-11', 1.2, 100, 50,
#                                      stop_at_target=-1, allowed_week_day=4, is_c2c_enabled=True)
