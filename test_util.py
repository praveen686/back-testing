from trade_setup import AllTrade
from util import parse_trade_selectors

trade_str = AllTrade.trade_intervals_by_week_day[0]
matrices = parse_trade_selectors(trade_str)
print(matrices)
