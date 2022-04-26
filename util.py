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


def get_today_date_in_str():
    current_time = datetime.datetime.now()
    today_date_str = current_time.strftime(constants.DATE_FORMAT)
    return today_date_str


def get_date_in_str(date, date_format=constants.DATE_FORMAT):
    date_str = date.strftime(date_format)
    return date_str


def get_date_from_str(date, date_format=constants.DATE_FORMAT):
    date = datetime.datetime.strptime(date, date_format)
    return date
