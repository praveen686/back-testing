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


#
# ["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
#                                              1.2, 60, .5,

class AllTrade:
    trade_intervals_by_week_day: Dict[int, List[str]] = {
        0: ["time>'09:40' and iv<=20|sp:sp|1.2|60|.5",
            "time>'10:40' and iv<=20|sp:sp|1.2|60|.5"],
        1: ["time>'09:40' and iv<20|sp:sp|1.2|-1|-1",
            "time>'09:40' and iv>=20|sp+100 if ttype=='PE' else sp-100|1.2|-1|-1",
            "time>'10:40' and iv<20|sp:sp|1.2|-1|-1",
            "time>'10:40' and iv>=20|sp+100 if ttype=='PE' else sp-100|1.2|-1|-1"],
        2: ["time>'09:40' and iv<20|sp:sp|1.2|-1|-1",
            "time>'09:40' and iv>=20|sp+100 if ttype=='PE' else sp-100|1.2|-1|-1",
            "time>'10:40' and iv<20|sp:sp|1.2|-1|-1",
            "time>'10:40' and iv>=20|sp+100 if ttype=='PE' else sp-100|1.2|-1|-1"],
        3: ["time>'09:20'|sp:sp|1.6|-1|-1", "time>'10:40'|sp:sp|1.6|-1|-1"],
        4: ["time>'09:40' and iv<=20|sp:sp|1.2|60|.5", "time>'10:40' and iv<=20|sp:sp|1.2|60|.5"]
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

trade = AllTrade.trade_intervals_by_week_day[0][0]
fn_suffix = trade.split("|")[0]
hello_fn = eval(f'lambda time,iv: {fn_suffix}')
print(hello_fn("09:39", 18))
