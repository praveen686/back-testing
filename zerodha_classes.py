from typing import List, Dict


class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.zerodha_order: Dict = None
        self.is_c2c_set = False
        self.is_trailing_sl_set = False


# ["09:40:00|0,0", "10:40:00|0,0"], start_date, end_date,
#                                              1.2, 60, .5,
class TradeMatrix:
    def __init__(self, matrix_id: str, time: str, trade_selector_fn, strike_selector_fn, sl: float, target_profit: int,
                 trailing_sl_perc: float, quantity: int, is_c2c_enabled: bool):
        self.matrix_id: str = matrix_id
        self.time: str = time
        self.trade_selector_fn = trade_selector_fn
        self.strike_selector_fn = strike_selector_fn
        self.sl = sl
        self.target_profit = target_profit
        self.trailing_sl_perc = trailing_sl_perc
        self.quantity = quantity
        self.is_c2c_enabled = is_c2c_enabled


class Basket:
    def __init__(self, basket_id, tradingsymbol, transaction_type, order_type, quantity):
        self.basket_id = basket_id
        self.tradingsymbol: str = tradingsymbol
        self.transaction_type: str = transaction_type
        self.order_type: str = order_type
        self.quantity: int = quantity
        self.price: float = 0
        self.trigger_price: float = 0


class Position:
    def __init__(self, symbol, option_type: str, sell_or_buy: str, quantity: int, spot_price: float,
                 strike_price: float, sl: float):
        self.symbol = symbol
        self.option_type = option_type
        self.sell_or_buy = sell_or_buy
        self.spot_price: float = spot_price
        self.strike_price: float = strike_price
        self.place_order: Order = None
        self.sl_order: Order = None
        self.sl = sl
        self.quantity = quantity

    def is_sl_hit(self):
        return self.sl_order is not None and self.sl_order.zerodha_order is not None and self.sl_order.zerodha_order[
            'status'] == "COMPLETE"

    def is_c2c_enabled(self):
        return self.sl_order is not None and self.sl_order.is_c2c_set

    def get_premium(self):
        return self.place_order.zerodha_order['average_price']


class Straddle:

    def __init__(self, trade_time: str, buy_pe_position: Position, buy_ce_position: Position,
                 sell_pe_position: Position,
                 sell_ce_position: Position, src_trade_matrix: TradeMatrix):
        self.trade_time = trade_time
        self.buy_pe_position: Position = buy_pe_position
        self.buy_ce_position: Position = buy_ce_position
        self.sell_pe_position: Position = sell_pe_position
        self.sell_ce_position: Position = sell_ce_position
        self.src_trade_matrix: TradeMatrix = src_trade_matrix
        self.basket: Basket
