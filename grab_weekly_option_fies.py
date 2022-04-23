import os
import re
from util import *


def get_all_nifty_weekly_option_files(nifty_type):
    path = "/Users/anoopisaac/projects/backtest-options/"
    years = ['2019', '2020', '2021', '2022']
    year_end_pattern = "\d\d"
    month_pattern = "([0-9]|O|N|D|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    expiry_day_pattern = "\d\d"
    strike_price_pattern = "\d+"
    option_type_pattern = "(PE|CE)"
    only_nifty_match = re.compile(
        f'{nifty_type}{year_end_pattern}{month_pattern}.*{strike_price_pattern}{option_type_pattern}\.csv$')
    all_nifty_weekly_option_files = []

    for year in years:
        full_path = path + year
        file_list = os.listdir(full_path)
        # getting rid of rar files and getting only the folders that contains data.
        option_folder_data_match = re.compile(f'.*{year}$')
        # option_folder_data_match = re.compile(f'Options January 2020$')
        monthly_data_folders = [f for f in file_list if option_folder_data_match.match(f) is not None]
        # searching through monthly option folders and getting only the nifty data
        for monthly_data_folder in monthly_data_folders:
            option_files = os.listdir(full_path + "/" + monthly_data_folder)
            # print(option_files)
            # getting only the weekly files for nifty
            only_nifty_weekly_files = [{"file": f, "filePath": f'{full_path + "/" + monthly_data_folder}/{f}'} for f in
                                       option_files if only_nifty_match.match(f) is not None]
            # print(only_nifty_weekly_files)
            all_nifty_weekly_option_files.extend(only_nifty_weekly_files)
    return all_nifty_weekly_option_files


def get_all_nifty_weekly_option_files_for_2022(nifty_type):
    path = "/Users/anoopisaac/projects/backtest-options/2022/"
    months = ['Options January 2022', 'Options February 2022']
    year_end_pattern = "\d\d"
    month_pattern = "([0-9]|O|N|D|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    expiry_day_pattern = "\d\d"
    strike_price_pattern = "\d+"
    option_type_pattern = "(PE|CE)"
    only_nifty_match = re.compile(
        f'{nifty_type}{year_end_pattern}{month_pattern}.*{strike_price_pattern}{option_type_pattern}\.csv$')
    all_nifty_weekly_option_files = []

    for month in months:
        full_path = path + month
        folder_list = os.listdir(full_path)
        option_folder_data_match = re.compile(f'.*2022$')
        daily_data_folders = [f for f in folder_list if option_folder_data_match.match(f) is not None]
        # getting rid of rar files and getting only the folders that contains data.
        # option_folder_data_match = re.compile(f'.*{year}$')
        # option_folder_data_match = re.compile(f'Options January 2020$')
        # monthly_data_folders = [f for f in file_list if option_folder_data_match.match(f)!=None]
        # searching through monthly option folders and getting only the nifty data
        for daily_folder in daily_data_folders:
            option_files = os.listdir(full_path + "/" + daily_folder)
            # print(option_files)
            # getting only the weekly files for nifty
            only_nifty_weekly_files = [{"file": f, "filePath": f'{full_path + "/" + daily_folder}/{f}'} for f in
                                       option_files if only_nifty_match.match(f) is not None]
            # print(only_nifty_weekly_files)
            all_nifty_weekly_option_files.extend(only_nifty_weekly_files)
    return all_nifty_weekly_option_files

