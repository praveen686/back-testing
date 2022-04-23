import threading
from typing import List, Optional, Dict
from option_util import *


def change_date_format(date, src_date_format="%Y-%m-%d", des_date_format="%m/%d/%Y"):
    sel_date = datetime.datetime.strptime(date, src_date_format)
    dest_date_str = sel_date.strftime(des_date_format)
    return dest_date_str


class OptionLeg:
    def __init__(self, leg_id, option_type, buy_or_sell, lot_count, sl, re_entry, leg_type, active,
                 offset: List[int]):
        self.leg_id = leg_id
        self.option_type = option_type
        self.buy_or_sell = buy_or_sell
        self.lots = lot_count
        self.initial_sl = sl
        # ony if the premium reaches back to below value and reentry will be done.
        self.reEntry = re_entry
        self.leg_type = leg_type
        self.active = active
        self.offset: List[int] = offset

    def __str__(self):
        return "Option Leg %s" % self.leg_id


class Config:
    def __init__(self, entry_times: List[str], exit_time, c2c, column_to_consider, days_to_trade, india_vix_max_value,
                 track_sl_hit_leg, re_entry, re_entry_perc, cut_off_leg):
        self.entry_times: List[str] = entry_times
        self.exit_time = exit_time
        self.c2c = c2c
        self.column_to_consider = column_to_consider
        self.days_to_trade: List[int] = days_to_trade
        self.india_vix_max_value = india_vix_max_value
        self.track_sl_hit_leg = track_sl_hit_leg
        self.re_entry: int = re_entry
        self.re_entry_perc: int = re_entry_perc
        self.cut_off_leg = cut_off_leg


class Trade:
    def __init__(self, trade_time, price, is_stop_loss, spot_price):
        self.trade_time: str = trade_time
        self.price: float = price
        self.spot_price = spot_price
        self.is_stop_loss: bool = is_stop_loss


class OptionLegDayTracker:
    def __init__(self, option_leg: OptionLeg, dest_date_str: str, strike_price, strike_ticker_prefix: str,
                 strike_ticker_candles_for_trade_date_dic, expiry_date, option_file_name, atm):
        self.day_tracker: Optional[DayTracker] = None
        self.last_date_str = None
        self.option_leg = option_leg
        self.expiry_date = expiry_date
        self.dest_date_str: str = dest_date_str
        self.strike_price: float = strike_price
        self.option_file_name: str = option_file_name
        self.atm = atm
        self.sl = option_leg.initial_sl
        # curr_stop_loss:float
        # price_to_reenter:float
        self.trades: List[Trade] = []
        self.strike_ticker_candles_for_trade_date_dic: Dict[
            str, {}] = strike_ticker_candles_for_trade_date_dic  # instead of stock price, this will have premium price in it
        self.strike_ticker_prefix = strike_ticker_prefix
        self.last_premium = None
        self.last_time_part = None
        self.is_stop_loss_hit = False
        self.is_track_sl_hit = False

        self.live_leg_profit_on_sl_hit = None
        self.live_leg_premium_sl_hit = None
        self.sl_leg_premium_on_sl_hit = None
        self.sl_leg_hit_time = None
        self.spot_price_on_sl_hit = None
        self.is_other_sl_hit = False
        self.premium_diff_perc_list = []
        self.spot_price_diff_perc_list = []
        self.max_premium_diff_perc = None
        self.min_premium_diff_perc = None
        self.max_spot_price_diff_perc = None
        self.min_spot_price_diff_perc = None
        self.starting_new_position = False
        self.met_diff = False

        self.live_premiums = []
        self.live_times = []

    def set_day_tracker(self, day_tracker):
        self.day_tracker = day_tracker

    def get_candle(self, date_with_minute):
        time_part = date_with_minute.strftime("%H:%M:%S")
        if time_part not in self.strike_ticker_candles_for_trade_date_dic:
            # raise Exception(f'premium not present {time_part} for {self.option_leg.leg_id}')
            return
        curr_candle = self.strike_ticker_candles_for_trade_date_dic[time_part]
        return curr_candle

    def trade_leg(self, date_with_minute, spot_price):

        time_part = date_with_minute.strftime("%H:%M:%S")
        curr_candle = self.get_candle(date_with_minute)
        if curr_candle is None:
            print(
                f'premium not present {time_part} for {self.option_leg.leg_id} date :{self.day_tracker.trading_date} '
                f'file;{self.option_file_name}')
            return

        self.last_date_str = date_with_minute.strftime('%Y-%m-%d')
        # premium=
        high_premium = float(curr_candle['high'])
        self.last_premium = float(curr_candle[self.day_tracker.config.column_to_consider])
        self.last_time_part = time_part

        # if already entries have gone in
        if len(self.trades) > 0:
            is_trade_open = len(self.trades) % 2 > 0
            last_trade = self.trades[-1]
            # trying to reenter if the premium has come down again
            if last_trade.is_stop_loss:
                second_last_trade = self.trades[-2]
                # if premium<=second_last_trade.price*(.85):
                #     new_trade = Trade(time_part,premium,False)
                #     self.trades.append(new_trade)
                #     print(("starting second leg",time_part,"currprem",premium,"prevprem",second_last_trade.price))
            if is_trade_open:
                self.live_times.append(time_part)
                self.live_premiums.append(self.last_premium)
                # checkin whether stop loss is configured and if it acutally hit
                if self.sl != -1:
                    self.is_stop_loss_hit = self.last_premium > last_trade.price * (
                            1 + self.sl) if self.option_leg.buy_or_sell == "sell" else self.last_premium < last_trade.price * (
                            1 - self.sl)
                    if self.is_stop_loss_hit:
                        start_spot = millis()
                        print(f' time for spot :{millis() - start_spot}')
                        new_trade = Trade(time_part, self.last_premium, True, spot_price)
                        self.trades.append(new_trade)
                        print(("hit stop loss currprem", high_premium, "entryprem", last_trade.price, time_part))
                    # checking for trailing sl
                    # self.is_stop_loss_hit = self.last_premium < (
                    #         last_trade.price * .2) if self.option_leg.buy_or_sell == "sell" else self.last_premium < last_trade.price * (
                    #         1 - self.sl)
                    # if self.is_stop_loss_hit:
                    #     new_trade = Trade(time_part, self.last_premium, True, spot_price)
                    #     self.trades.append(new_trade)
        else:
            new_trade = Trade(time_part, self.last_premium, False, spot_price)
            self.live_times.append(time_part)
            self.live_premiums.append(self.last_premium)
            self.trades.append(new_trade)

    def is_trading_closed(self):
        return self.is_stop_loss_hit or self.is_track_sl_hit
        # return self.is_stop_loss_hit TODO as temp fix returning false always, need to remove it
        # return False

    def square_off_as_other_sl_hit(self, spot_price):

        last_trade = Trade(self.last_time_part, self.last_premium, False, spot_price)
        self.trades.append(last_trade)
        # self.starting_new_position = True
        self.is_track_sl_hit = True
        return last_trade

    def re_enter(self, time_part, premium, spot_price):

        last_trade = Trade(time_part, premium, False, spot_price)
        self.trades.append(last_trade)
        self.is_stop_loss_hit = False
        self.is_track_sl_hit = False
        return last_trade

    def get_last_trade(self, spot_price):
        last_trade = Trade(self.last_time_part, self.last_premium, False, spot_price)
        return last_trade

    def square_off(self):

        if len(self.trades) % 2 == 1:
            closing_candle_keys = \
                [k for k in self.strike_ticker_candles_for_trade_date_dic if k >= self.day_tracker.config.exit_time]
            if len(closing_candle_keys) == 0:
                raise Exception(f'no candles on ar after exit time {self.day_tracker.config.exit_time}')
            close_candle = self.strike_ticker_candles_for_trade_date_dic[closing_candle_keys[0]]
            spot_price = get_nifty_spot_price(self.last_date_str, close_candle['time'],
                                              self.day_tracker.nifty_min_data_dic,
                                              self.day_tracker.config.column_to_consider)
            last_trade = Trade(close_candle['time'], float(close_candle[self.day_tracker.config.column_to_consider]),
                               False,
                               spot_price)
            self.trades.append(last_trade)

    def get_profit(self, profit_type: str = 'total'):
        if len(self.trades) == 0:
            return None
        else:
            profit_reversal = (-1 if self.option_leg.buy_or_sell == "sell" else 1)
            as_trade_pairs = [i for i in chunks(self.trades, 2)]
            # print(as_trade_pairs)
            total_profit = 0
            for trade_pair in as_trade_pairs:
                # is last element
                if as_trade_pairs[-1] == trade_pair:
                    if profit_type == 'total':
                        curr_profit = (trade_pair[1].price - trade_pair[0].price) * profit_reversal
                    else:
                        curr_profit = (self.last_premium - trade_pair[0].price) * profit_reversal
                else:
                    curr_profit = (trade_pair[1].price - trade_pair[0].price) * profit_reversal
                total_profit = total_profit + curr_profit
            return total_profit


class DayTracker:
    # will be equal to no. legs traded.
    # def run(self):
    #     self.trade_day()

    def __init__(self, trading_date: str, option_leg_trackers, nearest_expiry: str, nifty_min_data_dic, config: Config):
        super(DayTracker, self).__init__()
        self.trading_date: str = trading_date
        self.option_leg_trackers: List[OptionLegDayTracker] = option_leg_trackers
        self.nearest_expiry = nearest_expiry
        self.nifty_min_data_dic = nifty_min_data_dic
        self.config: Config = config
        self.done_for_the_day = False
        self.profit_series = None
        self.profit_df = None

    def is_both_sl_hit(self):
        sl_hit_legs = [option_leg_tracker for option_leg_tracker in
                       self.option_leg_trackers if (option_leg_tracker.option_leg.leg_type == "primary")
                       & (option_leg_tracker.is_stop_loss_hit is True)]
        return len(sl_hit_legs) == len([option_leg_tracker for option_leg_tracker in
                                        self.option_leg_trackers if
                                        option_leg_tracker.option_leg.leg_type == "primary"])

    def is_track_sl_hit(self):
        is_track_sl_hit = len([option_leg_tracker for option_leg_tracker in
                               self.option_leg_trackers if (option_leg_tracker.option_leg.leg_type == "primary")
                               & (option_leg_tracker.is_track_sl_hit is True)]) > 0
        return is_track_sl_hit

    def count_of_sl_hit(self):
        sl_hit_trackers = [option_leg_tracker for option_leg_tracker in
                           self.option_leg_trackers if (option_leg_tracker.is_stop_loss_hit is True)]
        return len(sl_hit_trackers)

    def find_day_profit(self):
        return sum(option_leg_tracker.get_profit() for option_leg_tracker in self.option_leg_trackers)

    def trade_day(self):
        minute_list = self.get_minute_list(self.config)
        time_series = [minute.strftime("%H:%M:%S") for minute in minute_list]
        zero_fill = [0 for i in range(len(time_series))]
        base_df = pd.DataFrame({"base": zero_fill}, time_series)
        start_millis = millis()
        # is_any_sl_hit = False
        # sl_hit_processed = False
        is_sl_benchmark_set = False
        sl_hit_leg_tracker = None

        for minute in minute_list:
            if self.is_both_sl_hit():
                print(f'day closed as both sl hit')
                break
            time_part = minute.strftime("%H:%M:%S")
            spot_price = get_nifty_spot_price(self.trading_date, time_part, self.nifty_min_data_dic,
                                              self.config.column_to_consider)
            # just for analysis

            for option_leg_tracker in self.option_leg_trackers:
                # todo this will always return false for now
                if not option_leg_tracker.is_trading_closed():
                    option_leg_tracker.trade_leg(minute, spot_price)
                    fresh_stop_loss_hit = option_leg_tracker.is_stop_loss_hit
                    option_leg = option_leg_tracker.option_leg
                    if fresh_stop_loss_hit & (option_leg.leg_type == "primary") & self.config.c2c:
                        self.set_other_leg_sl_to_c2c(option_leg_tracker)
            # checking any one of the trackers has sl hit
            # is_any_sl_hit = len([option_leg_tracker for option_leg_tracker in self.option_leg_trackers if (
            #         option_leg_tracker.option_leg.leg_type == "primary") and option_leg_tracker.is_stop_loss_hit]) > 0
            # if hit stop close the other leg
            if sl_hit_leg_tracker is not None and False:
                # get the other leg
                live_leg_tracker: OptionLegDayTracker = [option_leg_tracker for option_leg_tracker in
                                                         self.option_leg_trackers if
                                                         option_leg_tracker.option_leg.leg_type == "primary"
                                                         and option_leg_tracker != sl_hit_leg_tracker][0]
                sl_hit_trade: Trade = sl_hit_leg_tracker.get_last_trade(spot_price)
                sl_hit_candle = sl_hit_leg_tracker.get_candle(minute)
                live_hit_candle = live_leg_tracker.get_candle(minute)

                # self.done_for_the_day = True
                # this is to make sure this portion is only entered once to set base value on sl hit
                if live_leg_tracker.is_other_sl_hit is False:
                    live_leg_tracker.live_leg_profit_on_sl_hit = live_leg_tracker.get_profit('current')
                    # live_leg_tracker.live_leg_premium_sl_hit = live_leg_tracker.get_profit('current')
                    live_leg_tracker.is_other_sl_hit = True
                    live_leg_tracker.sl_leg_hit_time = sl_hit_trade.trade_time
                    live_leg_tracker.spot_price_on_sl_hit = sl_hit_trade.spot_price
                    live_leg_tracker.sl_leg_premium_on_sl_hit = sl_hit_trade.price
                    if live_hit_candle is not None:
                        live_leg_tracker.live_leg_premium_sl_hit = float(
                            live_hit_candle[self.config.column_to_consider])
                    else:
                        print(live_hit_candle)
                if live_hit_candle is not None and self.config.cut_off_leg is True:
                    live_curr_premium = float(live_hit_candle[self.config.column_to_consider])
                    if live_curr_premium < live_leg_tracker.live_leg_premium_sl_hit * .5:
                        live_leg_tracker.square_off_as_other_sl_hit(spot_price)
                if sl_hit_candle is not None and self.config.re_entry > 0:
                    sl_hit_curr_premium = float(sl_hit_candle[self.config.column_to_consider])
                    live_curr_premium = float(live_hit_candle[self.config.column_to_consider])
                    premium_diff = sl_hit_curr_premium - live_leg_tracker.sl_leg_premium_on_sl_hit
                    premium_diff_perc = (premium_diff / live_leg_tracker.sl_leg_premium_on_sl_hit) * 100
                    spot_price_diff = spot_price - live_leg_tracker.spot_price_on_sl_hit
                    spot_price_diff_perc = (spot_price_diff / live_leg_tracker.spot_price_on_sl_hit) * 100
                    live_leg_tracker.premium_diff_perc_list.append(premium_diff_perc)
                    live_leg_tracker.spot_price_diff_perc_list.append(spot_price_diff_perc)
                    live_leg_tracker.max_spot_price_diff_perc = max(live_leg_tracker.spot_price_diff_perc_list)
                    live_leg_tracker.min_spot_price_diff_perc = min(live_leg_tracker.spot_price_diff_perc_list)
                    live_leg_tracker.max_premium_diff_perc = max(live_leg_tracker.premium_diff_perc_list)
                    live_leg_tracker.min_premium_diff_perc = min(live_leg_tracker.premium_diff_perc_list)
                    # for hitting sl on live leg
                    if ((sl_hit_leg_tracker.option_leg.option_type == 'CE' and premium_diff_perc < -50)
                        or (sl_hit_leg_tracker.option_leg.option_type == 'PE' and premium_diff_perc > 50)) \
                            and self.config.track_sl_hit_leg:
                        print(
                            f'trade date:{self.trading_date} live leg: {live_leg_tracker.option_leg.option_type} '
                            f'sl hit premium {sl_hit_curr_premium} '
                            f'sl hit base :{live_leg_tracker.sl_leg_premium_on_sl_hit} diff_perc :{premium_diff_perc}')
                        live_leg_tracker.square_off_as_other_sl_hit(spot_price)
                    #     for handling re-entry
                    if sl_hit_curr_premium < live_leg_tracker.sl_leg_premium_on_sl_hit * .1 and live_leg_tracker.max_premium_diff_perc > self.config.re_entry_perc and self.config.re_entry > 0:
                        # -1 to ignore the first entry; not doing this if re-entry has occurred 2 times already
                        if (len(sl_hit_leg_tracker.trades) / 2) - 1 >= self.config.re_entry:
                            print(
                                f' no re_entry: trade date:{self.trading_date} sl leg: {sl_hit_leg_tracker.option_leg.option_type} '
                                f'sl hit premium {sl_hit_curr_premium} '
                                f'sl hit base :{live_leg_tracker.sl_leg_premium_on_sl_hit} diff :{premium_diff}')
                        else:
                            print(
                                f're_entry : trade date:{self.trading_date} sl leg: {sl_hit_leg_tracker.option_leg.option_type} '
                                f'sl hit premium {sl_hit_curr_premium} '
                                f'sl hit base :{live_leg_tracker.sl_leg_premium_on_sl_hit} diff :{premium_diff}')

                            sl_hit_leg_tracker.re_enter(time_part, sl_hit_curr_premium, spot_price)

        # tracking of profits by time
        self.generate_profit_time_series_by_combining_ind_tracker(base_df)
        self.square_off_legs()

    def generate_profit_time_series_by_combining_ind_tracker(self, base_df):
        base_df['profit'] = base_df['base']
        for tracker_index, option_leg_tracker in enumerate(self.option_leg_trackers):
            premium_change_col_name = f'change{tracker_index}'
            day_premium_df = pd.DataFrame({premium_change_col_name: option_leg_tracker.live_premiums},
                                          option_leg_tracker.live_times)
            day_premium_change_df = day_premium_df.rolling(2).apply(lambda x: x[0] - x[1])
            base_df = base_df.join(day_premium_change_df)
            base_df[premium_change_col_name] = base_df[premium_change_col_name].replace(np.nan, 0)
            base_df[premium_change_col_name] = base_df[premium_change_col_name].cumsum()
            base_df['profit'] = base_df['profit'] + base_df[premium_change_col_name]
        self.profit_series = ','.join(map(str, list(base_df['profit'].values)))
        self.profit_df = base_df['profit']

    def set_other_leg_sl_to_c2c(self, sl_hit_leg: OptionLegDayTracker):
        option_type = sl_hit_leg.option_leg.option_type
        # moving other leg to cost to cost c2c
        other_leg_trackers: List[OptionLegDayTracker] = \
            [option_leg_tracker for option_leg_tracker in self.option_leg_trackers if
             (option_leg_tracker.option_leg.option_type != option_type) & (
                     option_leg_tracker.option_leg.leg_type == "primary")]
        if len(other_leg_trackers) > 0:
            other_leg_trackers[0].sl = 0

    def get_current_profit(self):
        total_profit = 0
        for option_leg_tracker in self.option_leg_trackers:
            leg_profit = option_leg_tracker.get_profit()
            if leg_profit is not None:
                total_profit += leg_profit
            # print(f'leg profit>>>{leg_profit} of id {option_leg_tracker.option_leg.leg_id}')
        return total_profit

    def square_off_legs(self):
        for option_leg_tracker in self.option_leg_trackers:
            option_leg_tracker.square_off()

    def get_minute_list(self, config: Config):
        entry_date_time_str = f'{self.trading_date} {get_entry_time(self.trading_date, config)}'
        exit_date_time_str = f'{self.trading_date} {config.exit_time}'
        # print((entry_date_time_str, exit_date_time_str))
        entry_date_time = datetime.datetime.strptime(entry_date_time_str, '%Y-%m-%d %H:%M:%S')
        exit_date_time = datetime.datetime.strptime(exit_date_time_str, '%Y-%m-%d %H:%M:%S')
        time_diff = exit_date_time - entry_date_time
        minute_diff = (time_diff.total_seconds() / 60)
        minute_list = [entry_date_time + datetime.timedelta(minutes=it) for it in range(0, int(minute_diff + 1))]
        return minute_list

    def get_date_obj(self):
        return datetime.datetime.strptime(self.trading_date, '%Y-%m-%d')

    def get_count_of_tracker(self, option_leg_type: str):
        return len([tracker for tracker in self.option_leg_trackers if tracker.option_leg.leg_type == option_leg_type])


def get_day_of_week(trading_date):
    return datetime.datetime.strptime(trading_date, '%Y-%m-%d').weekday()


def get_entry_time(trading_date_str, config: Config):
    weekday = datetime.datetime.strptime(trading_date_str, '%Y-%m-%d').weekday()
    if weekday == 5:
        print(f'weekday>>>{weekday}')
    return config.entry_times[weekday]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class BackTester:
    # column_to_consider = 'close'
    # entry_time = "09:30:00"
    # exit_time = "14:30:00"
    # nifty_type: str = 'NIFTY'
    # c2c = False

    def __init__(self, option_legs, nifty_min_data_dic, india_vix_min_dic, trading_days_list, expiry_df,
                 all_nifty_weekly_option_files,
                 config):
        self.all_trade_entries = None
        self.no_data_list = []
        self.day_trackers: List[DayTracker] = []
        self.nifty_min_data_dic = nifty_min_data_dic
        self.trading_days_list = trading_days_list
        self.expiry_df = expiry_df
        self.all_nifty_weekly_option_files = all_nifty_weekly_option_files
        self.option_legs: List[OptionLeg] = option_legs
        self.data_not_present = []
        self.config: Config = config
        self.india_vix_min_dic = india_vix_min_dic

    def create_option_leg_day_tracker(self, option_leg: OptionLeg, nearest_expiry, trade_date: str, nifty_type):
        start_millis = millis()

        # print(f'time to get atm>>>{(millis() - start_millis)}')
        # strike_price=round_nearest(atm*(1+leg_offset),50)

        atm = get_nifty_atm(trade_date, get_entry_time(trade_date, self.config), self.nifty_min_data_dic,
                            self.config.column_to_consider,
                            nifty_type)
        # strike_price = leg_offset(atm, day_of_week)
        day_of_week = get_day_of_week(trade_date)
        # strike price might vary depending on the option leg as there is option to decide on strike offset per leg
        strike_price = atm + (option_leg.offset[day_of_week])
        trade_date_in_option_format = change_date_format(trade_date)
        strike_ticker_candles_for_trade_date_dic, expiry_date_str, ticker_prefix, ticker_file_name = \
            get_ticker_data_by_expiry_and_strike(
                strike_price, nearest_expiry, option_leg.option_type, trade_date_in_option_format,
                self.all_nifty_weekly_option_files, nifty_type)

        # print(f'time to generate day tracker>>>{(millis() - start_millis)}')
        if len(strike_ticker_candles_for_trade_date_dic) == 0:
            self.no_data_list.append(
                {"trade_date": trade_date, "ticker_file_name": ticker_file_name, "id": option_leg.leg_id, "atm": atm,
                 "reason": "no ticker date for the date"})
            return None, ticker_file_name
        time_key_list = list(strike_ticker_candles_for_trade_date_dic.keys())
        restricted_time_key_list = [key for key in time_key_list if
                                    (key >= get_entry_time(trade_date, self.config)) & (key <= self.config.exit_time)]
        if len(restricted_time_key_list) == 0:
            self.no_data_list.append(
                {"trade_date": trade_date, "ticker_file_name": ticker_file_name, "id": option_leg.leg_id, "atm": atm,
                 "reason": "nothing within the time range"})
            return None, ticker_file_name
        # checking option ticker data is present for the entry time, ow this result in wrong premium to be captured as the entry might have gone deep itm or otm
        at_entry_time = [key for key in time_key_list if
                         (key == get_entry_time(trade_date, self.config))]
        if len(at_entry_time) == 0:
            self.no_data_list.append(
                {"trade_date": trade_date, "ticker_file_name": ticker_file_name, "id": option_leg.leg_id, "atm": atm,
                 "reason": "entry time"})
            return None, ticker_file_name

        # trading_day_ticker_df=get_trading_day_ticker_after_time(ticker_df,date_str,entry_time)
        option_leg_day_tracker = OptionLegDayTracker(option_leg, trade_date_in_option_format,
                                                     strike_price, ticker_prefix,
                                                     strike_ticker_candles_for_trade_date_dic, nearest_expiry,
                                                     ticker_file_name, atm)
        option_leg_day_tracker.last_time = restricted_time_key_list[-1]

        return option_leg_day_tracker, ticker_file_name

    def generate_day_tracker(self, trade_date: str, nifty_type):

        # initialzie DayTracker
        nearest_expiry_date = get_nearest_expiry(trade_date, self.expiry_df)
        india_vix = get_india_vix(trade_date, self.india_vix_min_dic)
        if india_vix > self.config.india_vix_max_value:
            return None
        # print((nearest_expiry_date,trade_date))
        option_leg_day_trackers: List[OptionLegDayTracker] = []
        # atm = get_nifty_atm(trade_date, self.config.entry_time, self.nifty_min_data_dic, self.config.column_to_consider,
        #                     nifty_type)
        for option_leg in [option_leg for option_leg in self.option_legs if option_leg.active]:
            option_leg_day_tracker, ticker_file_name = self.create_option_leg_day_tracker(option_leg,
                                                                                          nearest_expiry_date,
                                                                                          trade_date, nifty_type)
            if option_leg_day_tracker is not None:
                option_leg_day_trackers.append(option_leg_day_tracker)
        day_tracker = DayTracker(trade_date, option_leg_day_trackers, nearest_expiry_date, self.nifty_min_data_dic,
                                 self.config)
        # set a reference back to DayTracker from OptionLegTracker
        for tracker in option_leg_day_trackers:
            tracker.set_day_tracker(day_tracker)

        return day_tracker

    def back_test(self, start_row_index, end_row_index, nifty_type):
        # loop through trading days
        # self.: List[DayTracker] = []
        for i in range(start_row_index, end_row_index):
            # for i in range(18,len(trading_days_df)):
            start_millis = millis()
            trade_date = (self.trading_days_list[i])
            if (
                    trade_date == "2019-10-27" or trade_date == "2020-06-04" or trade_date == "2020-11-14" or trade_date == "2021-11-04" or
                    trade_date == "2021-02-24" or trade_date == "2022-03-07"):
                print("!!!!exiting as speical case!!!!!!!!!!!!!!")
                self.no_data_list.append({"trade_date": trade_date, "reason": "special day"})
                continue
            day_of_week = get_day_of_week(trade_date)
            if day_of_week not in self.config.days_to_trade:
                self.no_data_list.append(
                    {"trade_date": trade_date, "reason": f'day not in list {self.config.days_to_trade}'})
                continue
            day_tracker = self.generate_day_tracker(trade_date, nifty_type)
            # print(f'time to get day tracker>>>{(millis() - start_millis)}')
            if day_tracker is not None:
                self.day_trackers.append(day_tracker)
                day_tracker.trade_day()
                print(f'time to trade day tracker>>>{(millis() - start_millis)}')
                print(f'current index:{i} date:{trade_date}')
            else:
                self.no_data_list.append(
                    {"trade_date": trade_date, "reason": f'india vix > {self.config.india_vix_max_value}'})

    def find_profit(self):
        total_profit = 0
        self.all_trade_entries = []
        for day_tracker in self.day_trackers:
            is_both_sl_hit = day_tracker.is_both_sl_hit()
            is_track_sl_hit = day_tracker.is_track_sl_hit()
            sl_hit_count = day_tracker.count_of_sl_hit()
            day_profit = day_tracker.find_day_profit()
            primary_count = day_tracker.get_count_of_tracker('primary')
            secondary_count = day_tracker.get_count_of_tracker('secondary')
            if len(day_tracker.option_leg_trackers) <= 1:
                print(f'>>>>>>>>>>>>>>>>>>>>>>{day_tracker.trading_date}')
            # day_profit_other_way = 0
            for option_leg_day_tracker in day_tracker.option_leg_trackers:
                option_leg = option_leg_day_tracker.option_leg
                # sum_of_trades=[sum(trade.price for trade in option_leg_day_tracker.trades)]
                as_trade_pairs = [i for i in chunks(option_leg_day_tracker.trades, 2)]
                # print(as_trade_pairs)
                # for trade_pair in as_trade_pairs:
                for trade_pair_index in range(len(as_trade_pairs)):
                    trade_pair = as_trade_pairs[trade_pair_index]
                    # print(f'>>>>>>>> trade1{trade_pair[0].price} trade2{trade_pair[1].price} type:{option_leg.option_type} trade date:{day_tracker.trading_date}')
                    curr_profit = (trade_pair[0].price - trade_pair[1].price) if option_leg.buy_or_sell == "sell" else (
                            trade_pair[1].price - trade_pair[0].price)
                    trade_entry = {"profit": curr_profit, "option_type": option_leg.option_type,
                                   "trade_date": day_tracker.trading_date, "id": option_leg.leg_id,
                                   "week_day": get_day_of_week(day_tracker.trading_date)
                        , "start_prem": trade_pair[0].price, "end_prem": trade_pair[1].price,
                                   "start_time": trade_pair[0].trade_time, "end_time": trade_pair[1].trade_time,
                                   "expiry_date": option_leg_day_tracker.expiry_date,
                                   "option_file_name": option_leg_day_tracker.option_file_name,
                                   "atm": option_leg_day_tracker.atm,
                                   "strike_price": option_leg_day_tracker.strike_price,
                                   "sl": trade_pair[1].is_stop_loss,
                                   "entry_spot_price": trade_pair[0].spot_price,
                                   "exit_spot_price": trade_pair[1].spot_price, "sl_hit_count": sl_hit_count,
                                   "day_profit": day_profit, "prim_count": primary_count, "sec_count": secondary_count,
                                   "profit_series": day_tracker.profit_series,
                                   "other_sl_hit": option_leg_day_tracker.is_other_sl_hit,
                                   "max_profit_reached": round(float(day_tracker.profit_df.max()))

                                   # profit in live leg when sl was hit
                                   # "live_leg_profit_on_sl_hit": option_leg_day_tracker.live_leg_profit_on_sl_hit,
                                   # "sl_leg_premium_on_sl_hit": option_leg_day_tracker.sl_leg_premium_on_sl_hit,
                                   # "spot_price_on_sl_hit": option_leg_day_tracker.spot_price_on_sl_hit,
                                   # "max_spot_price_diff_perc": option_leg_day_tracker.max_spot_price_diff_perc,
                                   # "min_spot_price_diff_perc": option_leg_day_tracker.min_spot_price_diff_perc,
                                   # "max_premium_diff_perc": option_leg_day_tracker.max_premium_diff_perc,
                                   # "min_premium_diff_perc": option_leg_day_tracker.min_premium_diff_perc,
                                   # "other_sl_hit": option_leg_day_tracker.is_other_sl_hit,
                                   # "is_track_sl_hit": is_track_sl_hit,
                                   # "trade_index": trade_pair_index

                                   }
                    self.all_trade_entries.append(trade_entry)
                    # day_profit_other_way += curr_profit
            # print(f'day profit >>>>{day_profit} {day_tracker.trading_date} {day_profit_other_way}')
            total_profit += day_profit
        print(("profit>>>", total_profit))
        # print(self.all_trade_entries)
