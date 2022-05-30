import random
import time as time_  # make sure we don't override time
import datetime
import csv
import pandas as pd
import numpy as np

from util import get_pickle_data, write_pickle_data

month_to_month_dic = {10: 'O', 11: 'N', 12: 'D'}
date_time_str = '02May2019'


def is_last_expiry(expiry_date):
    next_expiry = expiry_date + datetime.timedelta(7)
    if expiry_date.month != next_expiry.month:
        return True
    else:
        return False


# this prefix will be used to find correct files belonging to this expiry
def get_instrument_prefix(expiry_date_str, nifty_type):
    # print('99'.zfill(5))
    date_time_obj = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')
    # print(date_time_obj)
    # print(date_time_obj.year-2000)
    if date_time_obj.month < 10:
        one_digit_month = date_time_obj.month
    else:
        one_digit_month = month_to_month_dic[date_time_obj.month]
    # check if its monthly expiry
    if is_last_expiry(date_time_obj):
        month_uppercase = date_time_obj.strftime("%b").upper()
        instrument_prefix = f'{nifty_type}{date_time_obj.year - 2000}{month_uppercase}'
    else:
        instrument_prefix = f'{nifty_type}{date_time_obj.year - 2000}{one_digit_month}{str(date_time_obj.day).zfill(2)}'
    return instrument_prefix


def millis():
    return int(round(time_.time() * 1000))


def round_nearest(x, num=50):
    return int(round(float(x) / num) * num)


columns = ['expiryDate', 'tickerPrefix', 'ticker', 'date', 'time', 'open', 'high', 'low', 'close', 'volume', 'oi']


# read from the file that has ticker data based on expiry and strike price
def read_strike_ticker_file(file_path, expiry_date, ticker_prefix):
    expiry_dic = {"expiryDate": [], "tickerPrefix": [], "ticker": [], "date": [], "time": [], "open": [], "high": [],
                  "low": [], "close": [], "volume": [], "oi": []}
    start = millis()
    strike_ticker_candles = []

    # file = open(file_path)
    with open(file_path) as infile:
        csvreader = csv.reader(infile)
        next(csvreader, None)
        for row in csvreader:
            strike_ticker_candle_dic = {}
            strike_ticker_candle_dic["ticker"] = row[0]
            strike_ticker_candle_dic["date"] = row[1]
            strike_ticker_candle_dic["time"] = row[2]
            strike_ticker_candle_dic["open"] = row[3]
            strike_ticker_candle_dic["high"] = row[4]
            strike_ticker_candle_dic["low"] = row[5]
            strike_ticker_candle_dic["close"] = row[6]
            strike_ticker_candle_dic["expiryDate"] = expiry_date
            strike_ticker_candle_dic["tickerPrefix"] = ticker_prefix
            strike_ticker_candles.append(strike_ticker_candle_dic)
    # print(("time taken to read file", (millis() - start)))
    return strike_ticker_candles


# expirty:2019-01-31 ticker_prefix:NIFTY19JAN
# reading a single expiry csv file for a strike price and populating the dic
def read_ticker_file(file_path, expiry_date, ticker_prefix):
    expiry_dic = {"expiryDate": [], "tickerPrefix": [], "ticker": [], "date": [], "time": [], "open": [], "high": [],
                  "low": [], "close": [], "volume": [], "oi": []}
    start = millis()
    # file = open(file_path)
    with open(file_path) as infile:
        csvreader = csv.reader(infile)
        next(csvreader, None)
        for row in csvreader:
            expiry_dic["expiryDate"].append(expiry_date)
            expiry_dic["tickerPrefix"].append(ticker_prefix)
            expiry_dic["ticker"].append(row[0])
            expiry_dic["date"].append(row[1])
            expiry_dic["time"].append(row[2])
            expiry_dic["open"].append(row[3])
            expiry_dic["high"].append(row[4])
            expiry_dic["low"].append(row[5])
            expiry_dic["close"].append(row[6])
            expiry_dic["volume"].append(row[7])
            expiry_dic["oi"].append(row[8])
    print(("time taken to read file", (millis() - start)))
    return expiry_dic


def get_ticker_data_from_option_files(ticker_files, expiry_date_str, ticker_prefix, trade_date):
    # ticker_df_dic={"expiryDate":[],"tickerPrefix":[],"ticker":[],"date":[],"time":[],"open":[],"high":[],"low":[],"close":[],"volume":[],"oi":[]}
    strike_ticker_candles_all_files = []
    for ticker_file in ticker_files:
        read_file_start = millis()
        file_abs_path = ticker_file['filePath']
        strike_ticker_candles = read_strike_ticker_file(file_abs_path, expiry_date_str, ticker_prefix)
        strike_ticker_candles_all_files.extend(strike_ticker_candles)
        # print(f'time to read file>>>{(millis() - read_file_start)}')

        # print(
        #     f'abs:{file_abs_path} expiry:{expiry_date_str} ticker_prefix:{ticker_prefix} size:{len(strike_ticker_candles_all_files)}')

        # append the minute ticker data to the existing list
        # for column in columns:
        #     ticker_df_dic[column].extend(ticker_dic[column])
    # ticker_df = pd.DataFrame(ticker_df_dic)
    # filtering ticker data for only the relevant dates
    strike_ticker_candles_for_trade_date = [candle for candle in strike_ticker_candles_all_files if
                                            candle['date'] == trade_date]
    # print(f' count before filtering {len(strike_ticker_candles_for_trade_date)}')
    strike_ticker_candles_for_trade_date_dic = {}
    for candle in strike_ticker_candles_for_trade_date:
        strike_ticker_candles_for_trade_date_dic[candle['time']] = candle

    return strike_ticker_candles_for_trade_date_dic


def get_ticker_data_by_expiry_and_strike(strike_price, expiry_date, option_type, trade_date,
                                         all_nifty_weekly_option_files, nifty_type):
    # get the token prefix from expiry date
    expiry_date_str = expiry_date.strftime('%Y-%m-%d')
    ticker_prefix = get_instrument_prefix(expiry_date_str, nifty_type)
    # get the folder path from the expiry
    # ticker_file_folder_path=get_folder_path_from_expiry(expiry_date_str)
    # generate the file name from atm,offset,expiry_prefix,option_type
    ticker_file_name = f'{ticker_prefix}{strike_price}{option_type}.csv'
    # print(("ticker file name>>>",ticker_file_name))
    # get list of the files from master map
    ticker_files = [file for file in all_nifty_weekly_option_files if file['file'] == ticker_file_name]
    # print(f'file count>>{len(ticker_files)}')
    # load it in df and return
    read_all_file_start = millis()
    strike_ticker_candles_for_trade_date_dic = get_ticker_data_from_option_files(ticker_files,
                                                                                 expiry_date_str, ticker_prefix,
                                                                                 trade_date)
    # print(f'time to read all files>>>{(millis() - read_all_file_start)}')

    # print(ticker_df)
    return strike_ticker_candles_for_trade_date_dic, expiry_date_str, ticker_prefix, ticker_file_name


def get_nearest_expiry(trade_date_str, expiry_df):
    filtered = expiry_df.loc[expiry_df['expiry'] >= trade_date_str]
    print(len(filtered['expiry'].values))
    if len(filtered['expiry'].values) == 0:
        print("werwwerwer", trade_date_str)
    next_expiry_str = filtered['expiry'].values[0]
    # next_expiry = next_weekday(date, 3)
    return datetime.datetime.strptime(next_expiry_str, '%Y-%m-%d')


def get_nifty_atm(date_str, time, nifty_min_data_dic, column_to_consider, nifty_type):
    # generate the date_time string
    search_date_time_string = f'{date_str}T{time}+0530'
    search_date_time_obj = datetime.datetime.strptime(search_date_time_string, '%Y-%m-%dT%H:%M:%S+0530')
    added_interval_time = search_date_time_obj + datetime.timedelta(minutes=-3)
    past_time_str = added_interval_time.strftime('%Y-%m-%dT%H:%M:%S+0530')
    # print(search_date_time_string)
    # close_list = nifty_one_minute_df.loc[nifty_one_minute_df.index == search_date_time_string][
    #     column_to_consider]
    if search_date_time_string not in nifty_min_data_dic:
        closest_keys = [k for k in nifty_min_data_dic if past_time_str <= k <= search_date_time_string]
        if len(closest_keys) == 0:
            raise Exception(f'no entry present between {search_date_time_string} and {past_time_str} ')
        else:
            closest_key = closest_keys[-1]
    else:
        closest_key = search_date_time_string
    close = nifty_min_data_dic[closest_key][column_to_consider]

    rounding_number = 50 if nifty_type == "NIFTY" else 100
    atm = round_nearest(float(close), rounding_number)
    return atm


def get_india_vix(date_str, instr_min_dic):
    # '2019-01-01T00:00:00+0530'
    search_date_time_string = f'{date_str}T00:00:00+0530'
    if search_date_time_string not in instr_min_dic:
        # closest_key = [k for k in instr_min_dic if k == search_date_time_string][0]
        # return instr_min_dic[closest_key]['close']
        raise Exception(f'india vix not found for the search {date_str}')
    close = instr_min_dic[search_date_time_string]['close']
    return float(close)


def load_nifty_min_data(nifty_type):
    nifty_prefix = 'nifty' if nifty_type == "NIFTY" else "b-nifty"
    filename = f'{nifty_prefix}-minute-candle'
    nifty_min_data_dic = get_pickle_data(filename)
    return nifty_min_data_dic


def load_india_vix_day_data():
    filename = f'india-vix-day-candle'
    india_vix_min_data_dic = get_pickle_data(filename)
    return india_vix_min_data_dic


def load_trading_days(nifty_type):
    nifty_prefix = 'nifty' if nifty_type == "NIFTY" else "b-nifty"
    filename = f'{nifty_prefix}-trading-days'
    trading_days = get_pickle_data(filename)
    return trading_days


def store_trading_days(nifty_type):
    nifty_prefix = 'nifty' if nifty_type == "NIFTY" else 'b-nifty'
    nifty_one_minute_df = pd.read_csv(f'{nifty_prefix}-minute-candle.csv')
    nifty_one_minute_df['date'] = pd.to_datetime(nifty_one_minute_df['date_time']).dt.date
    unique_date_array = nifty_one_minute_df.date.unique()
    unique_date_string_array = [(lambda x=x: x.strftime('%Y-%m-%d'))() for x in unique_date_array]
    trading_days_df = pd.DataFrame({"date": unique_date_string_array}, unique_date_string_array)
    write_pickle_data(f'{nifty_prefix}-trading-days', trading_days_df)


def get_nifty_spot_price(date_str, time, nifty_min_data_dic, column_to_consider):
    # generate the date_time string
    search_date_time_string = f'{date_str}T{time}+0530'
    # 2019-01-01T09:15:00+0530
    # get the nifty spot price
    # return 333.33
    # close_list = nifty_one_minute_df.loc[nifty_one_minute_df.index == search_date_time_string][
    #     column_to_consider]
    if search_date_time_string not in nifty_min_data_dic:
        # closest_key = [k for k in nifty_min_data_dic if k >= search_date_time_string][0]
        # return nifty_min_data_dic[closest_key][column_to_consider]
        return -1
    return nifty_min_data_dic[search_date_time_string][column_to_consider]


def get_minutes(start_time='09:20', end_time='09:30', step=10):
    start_time = datetime.datetime.strptime(start_time, '%H:%M')
    end_time = datetime.datetime.strptime(end_time, '%H:%M')
    # considering its going till 11:30
    minute_diff = (end_time - start_time).total_seconds() / 60
    minute_list = [start_time + datetime.timedelta(minutes=it) for it in range(0, int(minute_diff + 1), step)]
    minute_list_str = [minute.strftime("%H:%M:%S") for minute in minute_list]
    return minute_list_str


def get_minute_list(time_format: str, start_minute, end_minute):
    # print((entry_date_time_str, exit_date_time_str))
    entry_date_time = datetime.datetime.strptime(f'2021-01-01 {start_minute}', '%Y-%m-%d %H:%M:%S')
    # entry_date_time = datetime.datetime.strptime(f'2021-01-01 09:15:00', '%Y-%m-%d %H:%M:%S')
    exit_date_time = datetime.datetime.strptime(f'2021-01-01 {end_minute}', '%Y-%m-%d %H:%M:%S')
    # exit_date_time = datetime.datetime.strptime(f'2021-01-01 15:30:00', '%Y-%m-%d %H:%M:%S')
    time_diff = exit_date_time - entry_date_time
    minute_diff = (time_diff.total_seconds() / 60)
    minute_list = [entry_date_time + datetime.timedelta(minutes=it) for it in range(0, int(minute_diff + 1))]
    minute_str_list = [minute.strftime(time_format) for minute in minute_list]
    return minute_str_list


def get_nearest_thursday(curr_date, option_type, strike_index):
    # start_time = datetime.datetime.strptime('2022-12-23', '%Y-%m-%d')
    # print(start_time.strftime('%a'), start_time.strftime('%Y'))
    d = curr_date.weekday()
    days_to_thursday = 3 - d if (3 - d) >= 0 else 7 - (d - 3)
    expiry_day = curr_date + datetime.timedelta(days=days_to_thursday)
    expiry_year = expiry_day.strftime('%Y')[-2:]
    expiry_month = int(expiry_day.strftime("%m"))
    expiry_day = expiry_day.strftime("%d")
    formatted_expiry_month = expiry_month if expiry_month < 10 else "O" if expiry_month == 10 else "N" if expiry_month == 11 else "D"
    strike_price = 34000 + random.randrange(100 * strike_index, 100 * (strike_index + 1))
    banknifty_ticker_symbol = f'BANKNIFTY{expiry_year}{formatted_expiry_month}{expiry_day}{strike_price}{option_type}'
    return banknifty_ticker_symbol
