import store_one_min_data
from grab_weekly_option_fies import get_all_nifty_weekly_option_files_for_2022, get_all_nifty_weekly_option_files

from util import write_pickle_data


def store_all_data():
    # india vix data


    nifty_option_data_files_till_20 = get_all_nifty_weekly_option_files('NIFTY')
    b_nifty_option_data_files_till_20 = get_all_nifty_weekly_option_files('BANKNIFTY')

    write_pickle_data('nifty_weekly_option_data_files_till_20', nifty_option_data_files_till_20)
    write_pickle_data('b_nifty_weekly_option_data_files_till_20', b_nifty_option_data_files_till_20)


    # 2022 data
    # nifty_option_data_files_2022 = get_all_nifty_weekly_option_files_for_2022('NIFTY')
    # b_nifty_option_data_files_2022 = get_all_nifty_weekly_option_files_for_2022('BANKNIFTY')
    #
    # write_pickle_data('nifty_weekly_option_data_files_2022', nifty_option_data_files_2022)
    # write_pickle_data('b_nifty_weekly_option_data_files_2022', b_nifty_option_data_files_2022)

    # trading days
    # store_india_vix_data_from_zerodha()
    # store_nifty_trading_data_from_zerodha()
    # store_bnifty_min_candle_from_zerodha()


store_all_data()
