import pickle
import datetime
import random

import constants


def get_pickle_data(pickle_file_name):
    infile = open(pickle_file_name, 'rb')
    pickle_data = pickle.load(infile)
    infile.close()
    return pickle_data


def write_pickle_data(pickle_file_name, option_data_files):
    filename = f'{pickle_file_name}'
    outfile = open(filename, 'wb')
    # option_data_files = get_all_nifty_weekly_option_files(nifty_type)
    pickle.dump(option_data_files, outfile)
    outfile.close()


def get_diff_in_mins(start, end):
    start_time = datetime.datetime.strptime(start, constants.HOUR_MIN_TIME_FORMAT)
    end_time = datetime.datetime.strptime(end, constants.HOUR_MIN_TIME_FORMAT)
    diff_in_mins = (end_time - start_time).total_seconds() / 60
    return diff_in_mins


def get_diff_in_days(start_date, end_date):
    start_time = datetime.datetime.strptime(start_date, constants.DATE_FORMAT)
    end_time = datetime.datetime.strptime(end_date, constants.DATE_FORMAT)
    diff_in_days = (end_time - start_time).total_seconds() / (60 * 60 * 24)
    return diff_in_days


def get_today_date_in_str():
    current_time = datetime.datetime.now()
    today_date_str = current_time.strftime(constants.DATE_FORMAT)
    return today_date_str


def get_current_min_in_str():
    current_time = datetime.datetime.now()
    return current_time.strftime('%H:%M')


def get_date_in_str(date, date_format=constants.DATE_FORMAT):
    date_str = date.strftime(date_format)
    return date_str


def get_date_from_str(date, date_format=constants.DATE_FORMAT):
    date = datetime.datetime.strptime(date, date_format)
    return date


# this is used to create a new straddle when desired condition is hit.
def get_formatted_time_by_adding_delta_to_base(base_min_str: str, delta: int):
    input_time = datetime.datetime.strptime(base_min_str, constants.HOUR_MIN_SEC_TIME_FORMAT)
    new_time = input_time + datetime.timedelta(minutes=delta)
    return new_time.strftime(constants.HOUR_MIN_SEC_TIME_FORMAT)
