from typing import List, Dict


class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.zerodha_order: Dict = None
        self.is_c2c_set = False
        self.is_trailing_sl_set = False


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

    def __init__(self, buy_pe_position: Position, buy_ce_position: Position, sell_pe_position: Position,
                 sell_ce_position: Position):
        self.buy_pe_position: Position = buy_pe_position
        self.buy_ce_position: Position = buy_ce_position
        self.sell_pe_position: Position = sell_pe_position
        self.sell_ce_position: Position = sell_ce_position
