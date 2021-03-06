import re
from itertools import groupby
from typing import List
import datetime
import pandas as pd
import numpy as np

from option_util import get_minutes
from util import get_today_date_in_str
from trade_setup import DayTrade
from zerodha_algo_trader import ZerodhaBrokingAlgo

access_token = '0ccraaVV1xLO76zF3FrOH7djci7r3o3z'
today_date_str: str = get_today_date_in_str()
enc_token = "kCEFtP09oy0RbK0WaO2z/cJR25YYfKZdRPiDggVaekQR1o+ZabW/aam4/K1qfnT8jyNiaPdD8pqoTuYCQOODneV5aEFGNtqQSQBD2eFux3KDq7Cv6U8u1g=="

algo = ZerodhaBrokingAlgo(False, 0, DayTrade(today_date_str, access_token))
straddle = algo.prepare_option_legs(1.6, 25, "11:50", 10)
# straddle = algo.place_straddle_order(1.6, 25, "11:40", enc_token, access_token)
straddle = algo.add_legs_to_basket(straddle, "11:50", access_token, 25)
print("")
exit(0)


# zero = ZerodhaApi(False)
# basket_id = zero.create_new_basket("testtestest2", "mpSeGMu7mJEjTD6EyEJ8voN6UzfX7Fnt")
# zero.add_basket_items(basket_id, 'BANKNIFTY2251940200CE', "mpSeGMu7mJEjTD6EyEJ8voN6UzfX7Fnt", 25)


class Anoop:
    anoop_instance = None

    def __init__(self):
        self.test = True
        Anoop.anoop_instance = self

    @staticmethod
    def get_instance():
        return Anoop.anoop_instance


anoop1 = Anoop()
hello: Anoop = Anoop.get_instance()
print(hello.test)

elem1 = {"222": "ee"}
elem2 = {"bbb": "ee"}
elem_list = [elem1, elem2]
elem_list.remove(elem2)
print(elem_list)

group_by_test = [{"class": 1, "name": "anoop"}, {"class": 2, "name": "anil"}, {"class": 1, "name": "raju"}]
grouped_data = [list(g) for k, g in groupby(sorted(group_by_test, key=lambda xy: xy["class"]), lambda xy: xy["class"])]
test = "44,eee"
print(test.split(",")[1])

line = re.sub(r"[a-z:]+", "", "sl:.4")
line = re.sub(r":00$", "", "09:00:00")

print(line)

# x = lambda atm: atm
x = eval('lambda atm: atm')
print(x(4))

list_to: List[int] = [1, 3, 3]

my_new_list = eval('[0,2,2]')
print(my_new_list[0])
check = "eee" in "eee"
print(check)

print(get_minutes())


def test_profit():
    df1 = pd.DataFrame({"close1": [10, 15, 20, 25, 30]}, ["10:30", "10:40", "10:50", "11:10", "11:40"])
    df2 = pd.DataFrame({"close2": [50, 25, 75, 60]}, ["12:00", "12:10", "12:30", "12:50"])
    for i in range(3):
        check = df1.iloc[i].index
        print(check)
    basedf = pd.DataFrame({"close": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
                          ["10:30", "10:40", "10:50", "11:00", "11:10", "11:20", "11:30", "11:40", "11:50", "12:00",
                           "12:10", "12:20", "12:30", "12:40", "12:50"])
    df1_change = df1.rolling(2).apply(lambda x: x[1] - x[0])
    df2_change = df2.rolling(2).apply(lambda x: x[1] - x[0])
    finaldf = basedf.join(df1_change)
    finaldf = finaldf.join(df2_change)
    finaldf['close1'] = finaldf['close1'].replace(np.nan, 0)
    finaldf['close2'] = finaldf['close2'].replace(np.nan, 0)

    finaldf['close1'] = finaldf.close1.cumsum()
    finaldf['close2'] = finaldf.close2.cumsum()

    finaldf['profit'] = finaldf['close1'] + finaldf['close2']

    # df3['pct_change1'] = (df3['pct_change'] + df3['close2']) / 2
    print(finaldf)


test_profit()
