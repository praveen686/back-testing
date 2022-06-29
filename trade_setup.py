from typing import Dict, List

from zerodha_classes import Straddle


# from zerodha_kiteconnect_algo_trading import MyTicker

# ticker_tracker: MyTicker = None


class DayTrade:
    def __init__(self, date_str: str, access_token: str):
        self.date_str: str = date_str
        self.access_token: str = access_token
        self.enctoken: str = ""
        self.straddle_by_time: Dict[str, Straddle] = {}
        self.ltp: Dict[int, float] = {}
        self.final_buy_leg_price = None  # this leg is to reduce the margin cost
        self.is_all_position_exited = False
        self.target_profit_reached = False
        self.trailing_profit_sl: float = None

class AllTrade:
    trade_intervals_by_week_day: Dict[int, List[str]] = {
        0: ["mon_0940|09:40|iv:iv<=20|sp:sp|1.2|60|.5|25|True",
            "mon_1040|10:40|iv:iv<=20|sp:sp|1.2|60|.5|25|True"],
        1: ["tue_0940_iv_lt_20|09:40|iv:iv<20|sp:sp|1.2|-1|-1|25|True",
            "tue_0940_iv_gte_20|09:40|iv:iv>=20|sp,ttype:sp+100 if ttype=='PE' else sp-100|1.2|-1|-1|25|True",
            "tue_1040_iv_lt_20|10:40|iv:iv<20|sp:sp|1.2|-1|-1|25|True",
            "tue_1040_iv_gte_20|10:40|iv:iv>=20|sp,ttype:sp+100 if ttype=='PE' else sp-100|1.2|-1|-1|25|True"],
        2: ["wed_0940_iv_lt_20|09:40|iv:iv<20|sp:sp|1.2|-1|-1|25|True",
            "wed_0940_iv_gte_20|09:40|iv:iv>=20|sp,ttype:sp+100 if ttype=='PE' else sp-100|1.2|-1|-1|25|True",
            "wed_1040_iv_lt_20|10:40|iv:iv<20|sp:sp|1.2|-1|-1|25|True",
            "wed_1040_iv_gte_20|10:40|iv:iv>=20|sp,ttype:sp+100 if ttype=='PE' else sp-100|1.2|-1|-1|25|True"],
        3: ["thu_0920|09:15|iv:iv<=30|sp,ttype:sp|1.6|-1|-1|25|True",
            "thu_1040|10:40|iv:iv<=30|sp,ttype:sp|1.6|-1|-1|25|True"],
        4: ["fri_0940|09:40|iv:iv<=20|sp:sp|1.2|60|.5|25|True",
            "fri_1040|10:40|iv:iv<=20|sp:sp|1.2|60|.5|25|True"],
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
