# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from util import *
from back_testing import *
import pandas as pd
import re


# get all file names along with the location that has the option ticker data
def get_all_weekly_option_data_files(nifty_type):
    nifty_prefix = 'nifty' if nifty_type == "NIFTY" else 'b_nifty'

    weekly_option_data_files = get_pickle_data(f'{nifty_prefix}_weekly_option_data_files_till_20')
    # weekly_option_data_files_2022 = get_pickle_data(f'{nifty_prefix}_weekly_option_data_files_2022')
    weekly_option_all_data_files = []
    weekly_option_all_data_files.extend(weekly_option_data_files)
    # weekly_option_all_data_files.extend(weekly_option_data_files_2022)
    return weekly_option_all_data_files


def populate_all_initial_data(nifty_type):
    expiry_df = pd.read_csv("expiry_df.csv")
    all_nifty_weekly_option_files = get_all_weekly_option_data_files(nifty_type)
    # loading all nifty minute data in a global dic to improve the perf.
    nifty_min_data_dic = load_nifty_min_data(nifty_type)
    india_vix_day_dic = load_india_vix_day_data()
    trading_days_list = list(india_vix_day_dic.keys())
    trading_days_list = [trade_date.replace("T00:00:00+0530", "") for trade_date in trading_days_list]

    return nifty_min_data_dic, trading_days_list, expiry_df, all_nifty_weekly_option_files, india_vix_day_dic


def start_backtesting(nifty_type, option_legs_as_str: List[str], config: Config, start_date: str, end_date: str):
    leg_offset_config = {
        "NEAR_NIFTY": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 100},
        # "NEAR_NIFTY": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        "FAR_NIFTY": {0: 600, 1: 500, 2: 400, 3: 400, 4: 600, 5: 600},
        "NEAR_BANKNIFTY": {0: 100, 1: 100, 2: 0, 3: 0, 4: 100, 5: 100},
        "FAR_BANKNIFTY": {0: 1200, 1: 1200, 2: 1200, 3: 1200, 4: 1200, 5: 1200}
    }

    # unique_date_array.tolist().apply(lambda x: x.strftime('%Y-%m-%d'))
    start_millis = millis()
    nifty_min_data_dic, trading_days_list, expiry_df, all_nifty_weekly_option_files, india_vix_min_dic = populate_all_initial_data(
        nifty_type)

    start_row_index = trading_days_list.index(start_date)
    end_row_index = trading_days_list.index(end_date)
    # end_row_index = trading_days_df.index.get_loc("2020-01-08")
    # # start_row_index = trading_days_df.index.get_loc("2020-02-19")
    # end_row_index = trading_days_df.index.get_loc("2020-12-31")
    # start_row_index = trading_days_df.index.get_loc(start_date)
    # end_row_index = trading_days_df.index.get_loc(end_date)
    option_leg_list: List[OptionLeg] = []
    option_str = 'CE,sell,lot:1,sl:.4,primary,active,[0,0,0,0,0,0]'
    for option_leg_str in option_legs_as_str:
        option_leg_str_split = option_leg_str.split("|")
        option_type = option_leg_str_split[0]
        buy_or_sell = option_leg_str_split[1]
        lot_size = int(re.sub(r"[a-z:]+", "", option_leg_str_split[2]))
        sl = float(re.sub(r"[a-z:]+", "", option_leg_str_split[3]))
        re_entry = .5  # not used
        leg_type = option_leg_str_split[4]  # primary or secondary
        is_active = 'active' in option_leg_str
        offset_by_day = eval(option_leg_str_split[6])
        option_leg = OptionLeg(f'{option_type}_{buy_or_sell}_{leg_type}', option_type, buy_or_sell, lot_size, sl,
                               re_entry, leg_type, is_active, offset_by_day)
        option_leg_list.append(option_leg)

    # config: Config = Config("09:20:00", "14:30:00", 'NIFTY', True, 'close', [4])
    back_tester = BackTester(option_leg_list, nifty_min_data_dic, india_vix_min_dic, trading_days_list, expiry_df,
                             all_nifty_weekly_option_files, config)
    # back_tester.back_test(18,50)
    print(f'start {start_row_index}..end {end_row_index}')
    back_tester.back_test(start_row_index, end_row_index + 1, nifty_type)
    back_tester.find_profit()
    # //568,695

    print(f'time to load initial stuff >>{millis() - start_millis}')
    print(f'not loaded dates {back_tester.no_data_list} count {len(back_tester.no_data_list)}')

    return back_tester


# Press the green button in the gutter to run the script.
def run_test_with_confi():
    # "2019-02-11" starting day for the prain re
    # config: Config = Config("10:20:00", "14:30:00", True, 'close', [0, 1, 2, 3, 4], 50)
    # back_tester_nifty = start_backtesting('NIFTY', ['CE|sell|lot:1|sl:.3|primary|active|[0,0,0,0,0,0]',
    #                                                 'PE|sell|lot:1|sl:.3|primary|active|[0,0,0,0,0,0]'], config,
    #                                       "2019-02-11", "2019-12-31")

    # config: Config = Config(entry_times=["11:30:00", "11:30:00", "11:30:00", "11:30:00", "11:30:00"],
    config: Config = Config(
        entry_times=["09:20:00", "09:20:00", "09:20:00", "09:20:00", "09:20:00"],
        # entry_times=["09:40:00", "09:40:00", "09:40:00", "09:40:00", "09:40:00"],
        # entry_times=["09:30:00", "09:30:00", "09:30:00", "09:30:00", "09:30:00"],
        # entry_times=["10:30:00", "10:30:00", "10:30:00", "10:30:00", "10:30:00"],
        # entry_times=["11:30:00", "11:30:00", "11:30:00", "11:30:00", "11:30:00"],
        # entry_times=["11:00:00", "11:00:00", "11:00:00", "11:00:00", "11:00:00"],
        # entry_times=["10:00:00", "10:00:00", "10:00:00", "10:00:00", "10:00:00"],
        # entry_times=["13:00:00", "13:00:00", "13:00:00", "13:00:00", "13:00:00"],
        exit_time="14:30:00", c2c=True,
        column_to_consider='close',
        days_to_trade=[0, 1, 2, 3, 4], india_vix_max_value=50, track_sl_hit_leg=False, re_entry=0, re_entry_perc=20,
        cut_off_leg=False)
    back_tester = start_backtesting('BANKNIFTY', [
        'CE|sell|lot:1|sl:.4|primary|active|[0,0,0,0,0,0]',
        'PE|sell|lot:1|sl:.4|primary|active|[0,0,0,0,0,0]',
        # 'CE|sell|lot:1|sl:.2|primary|active|[0,0,0,0,0,0]',
        # 'PE|sell|lot:1|sl:.2|primary|active|[0,0,0,0,0,0]',
        # 'CE|sell|lot:1|sl:.2|primary|active|[0,0,0,0,0,0]',
        # 'PE|sell|lot:1|sl:.2|primary|active|[0,0,0,0,0,0]',
        # 'CE|sell|lot:1|sl:1.5|primary|active|[300,300,300,300,300,0]',
        # 'PE|sell|lot:1|sl:1.5|primary|active|[-300,-300,-300,-300,-300,0]',
    ], config,
                                    # "2020-11-04", "2020-11-04")
                                    # "2020-01-06", "2020-01-06")
                                    # "2021-01-01", "2021-12-31")
                                    # "2021-01-06", "2021-01-06")
                                    # "2019-02-20", "2019-02-20")
                                    # "2019-02-18", "2022-02-28")
                                    # "2020-01-01", "2020-12-31")
                                    # "2021-01-01", "2021-12-31")
                                    # "2022-01-03", "2022-02-28")
                                    "2019-02-18", "2022-02-28")
    # "2022-01-20", "2022-01-20")

    all_trades = []
    all_trades.extend(back_tester.all_trade_entries)
    # all_trades.extend(back_tester_b_nifty.all_trade_entries)

    back_test_trade_df = pd.DataFrame(all_trades)
    back_test_trade_df.index = pd.to_datetime(back_test_trade_df.trade_date)
    month_resampled = back_test_trade_df.resample('1M').sum()
    year_resampled = back_test_trade_df.resample('1Y').sum()
    daily_resampled = back_test_trade_df.resample('1D').sum()
    daily_resampled_min = back_test_trade_df.resample('1D').sum()
    print(f'profit considering all:{back_test_trade_df["profit"].sum()}')
    print(f'profit with both legs:{back_test_trade_df[back_test_trade_df.prim_count == 2]["profit"].sum()}')
    all_legs_df = back_test_trade_df[back_test_trade_df.prim_count == 2]
    by_week_df = all_legs_df[['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    print(by_week_df)
    month_resampled.to_csv("monthly_report")
    daily_resampled.to_csv("daily_report")
    print(back_test_trade_df[back_test_trade_df.sl_hit_count == 0].profit.sum())
    write_pickle_data('back_test_trade_df', back_test_trade_df)
    print(f'mean:{daily_resampled.profit.mean()}')
    write_pickle_data('back_tester', back_tester)


#     2021-03-17


def run_the_test(start_time: str, sl: float, start_date, end_date, india_vix, days_to_trade, offset: str, c2c: bool,
                 write_to_file: bool):
    trading_days = load_india_vix_day_data()
    date_key = f'{start_date}T00:00:00+0530'
    # '2021-06-07T00:00:00+0530'
    if date_key not in trading_days:
        print(f'date not present in the list :{start_date}')
        return
    config: Config = Config(
        entry_times=[start_time, start_time, start_time, start_time, start_time],
        exit_time="14:30:00", c2c=c2c,
        column_to_consider='close',
        days_to_trade=days_to_trade, india_vix_max_value=india_vix, track_sl_hit_leg=False, re_entry=0,
        re_entry_perc=20,
        cut_off_leg=False)
    back_tester = start_backtesting('BANKNIFTY', [
        f'CE|sell|lot:1|sl:{sl}|primary|active|{offset}',
        f'PE|sell|lot:1|sl:{sl}|primary|active|{offset}',
    ], config, start_date, end_date)
    all_trades_local = []
    all_trades_local.extend(back_tester.all_trade_entries)
    if write_to_file:
        back_test_trade_df = pd.DataFrame(all_trades_local)
        back_test_trade_df.index = pd.to_datetime(back_test_trade_df.trade_date)
        write_pickle_data('back_test_trade_df', back_test_trade_df)
        write_pickle_data('back_tester', back_tester)
    return all_trades_local


def generate_trade_data_by_start_time_and_sl():
    minute_list_str = get_minutes("09:20", "14:00", 20)
    # minute_list_str = ["09:20:00"]
    sl_list = [.2, .3, .4, .5, .6]
    # sl_list = [.5, .6]
    # sl_list = [.2]
    for sl in sl_list:
        for minute_str in minute_list_str:
            all_trades = run_the_test(minute_str, sl, "2019-02-18", "2022-02-28", 50, [0, 4],
                                      '[200, 200, 200, 200, 200]')
            # all_trades = run_the_test(minute_str, sl, "2020-01-01", "2020-12-31")
            # time_part = minute_str.replace(":00", "").replace(":", "")
            time_part = re.sub(r":00$", "", minute_str).replace(":", "")
            file_name = f'trade_data/trade_data_{time_part}_{sl}_offset.data'
            write_pickle_data(file_name, all_trades)
            print(f'sl:{sl} minute:{minute_str}')


def generate_data_manually():
    all_trades = []
    all_trades.extend(run_the_test("09:20:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("09:40:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("10:00:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("10:20:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("10:40:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("11:00:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("11:20:00", .4, "2019-02-18", "2022-02-28"))
    all_trades.extend(run_the_test("11:40:00", .4, "2019-02-18", "2022-02-28"))
    back_test_trade_df = pd.DataFrame(all_trades)
    back_test_trade_df.index = pd.to_datetime(back_test_trade_df.trade_date)
    write_pickle_data("all_trades_df", back_test_trade_df)


if __name__ == '__main__':
    # generate_trade_data_by_start_time_and_sl()
    # run_test_with_confi()
    run_the_test("09:20:00", .2, "2019-02-18", "2020-01-01", 50, [0, 1, 2, 3, 4], '[0, 0, 0, 0, 0]', False, True)
