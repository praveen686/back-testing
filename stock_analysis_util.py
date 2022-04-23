import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime


def set_return_and_cum_return(df, col_name):
    df[col_name + '_return'] = df[col_name].pct_change() + 1
    df[col_name + '_cum_return'] = df[col_name + '_return'].cumprod()
    # df[col_name+'_return'].iloc[0] =1
    # df[col_name+'_cum_return'].iloc[0] =1
    # first_row=df.iloc[0]
    # first_row[col_name+'_return']=1
    # df.loc[0,col_name+'_return'] =1
    # df.loc[0,col_name+'_cum_return'] =1
    df.loc[df.id == df.id.values[0], col_name + '_return'] = 1
    df.loc[df.id == df.id.values[0], col_name + '_cum_return'] = 1


def resample(df, frequency, col_name):
    df = df.copy()
    # resamples it and takes the last entry from the resample list .last() is for that.
    resampled = df.resample(frequency).last()
    # get the return for every eventry and also get teh cummulative amount
    set_return_and_cum_return(resampled, col_name)
    # resampled[col_name+'_return']=resampled[col_name].pct_change()+1
    return resampled


def split_by_duration(ticker_data_dic, frequency):
    frequency_ticker_data = {}
    for key in ticker_data_dic.keys():
        frequency_ticker_data[key] = resample(ticker_data_dic[key], frequency)
        # resetting the index to find out the mean
        # frequency_ticker_data[key]["id"]=frequency_ticker_data[key].index
    return frequency_ticker_data


# merge different rows by summing the col data
def merge_by_summing_col_data(ticker_data_dic):
    frames_to_be_combined = []
    for key in ticker_data_dic.keys():
        frames_to_be_combined.append(ticker_data_dic[key].copy())
    all_combined = pd.concat(frames_to_be_combined).groupby(['id']).sum().reset_index()
    set_return_and_cum_return(all_combined, 'weighted_investment')
    # all_combined['Close_return']=all_combined.Close.pct_change()+1
    return all_combined


# create a new column id by convreting the existing index col to date time
def reset_index(ticker_data):
    new_ticker_data = {}
    for key in ticker_data.keys():
        new_ticker_data[key] = ticker_data[key]['data'].copy()
        new_ticker_data[key].index = pd.to_datetime(new_ticker_data[key].index)
        new_ticker_data[key]["id"] = new_ticker_data[key].index
    return new_ticker_data


def reset_indv_ticker_index(ticker_data):
    ticker_data.index = pd.to_datetime(ticker_data.index)
    ticker_data["id"] = ticker_data.index


def filter_by_date(ticker_data_dic, start_date_str, end_date_str):
    src_date_format = "%Y-%m-%d"
    start_date = datetime.datetime.strptime(start_date_str, src_date_format)
    end_date = datetime.datetime.strptime(end_date_str, src_date_format)

    new_ticker_data = {}
    for key in ticker_data_dic.keys():
        ticker_data = ticker_data_dic[key]
        ticker_data = ticker_data[(ticker_data.index >= start_date) & (ticker_data.index <= end_date)]
        new_ticker_data[key] = ticker_data
    return new_ticker_data


def filter_by_segment(ticker_data_dic, by_segment, segment):
    segment_symbols = by_segment[segment]
    new_ticker_data = {}
    for key in ticker_data_dic.keys():
        if key in segment_symbols:
            ticker_data = ticker_data_dic[key]
            new_ticker_data[key] = ticker_data
    return new_ticker_data


def filter_by_content(ticker_data_dic, len_of_asianpaint):
    # src_date_format="%Y-%m-%d"
    # start_date=datetime.datetime.strptime(start_date_str, src_date_format)
    # end_date=datetime.datetime.strptime(end_date_str, src_date_format)
    new_ticker_data = {}
    for key in ticker_data_dic.keys():
        ticker_data = ticker_data_dic[key]
        print(f'symbol {key} content size {len(ticker_data)} asianpaint diff {len_of_asianpaint}')
        if len(ticker_data) == len_of_asianpaint:
            new_ticker_data[key] = ticker_data
    return new_ticker_data


def get_ticker_meta_data(ticker_data_dic):
    means = []
    seventyfive_percentiles = []
    fifty_percentiles = []
    twenty_five_percentiles = []
    positive_month_return_count_list = []
    total_month_list = []
    for key in ticker_data_dic.keys():
        ticker_data = ticker_data_dic[key]
        # ticker_data['close_return']=ticker_data.ClosFe.pct_change()+1
        quarterly_data = resample(ticker_data, "3M", 'Close')
        monthly_data = resample(ticker_data, "1M", 'Close')
        positive_month_return_count = len(monthly_data[monthly_data.Close_return > 1])
        positive_month_return_count_list.append(positive_month_return_count)
        total_month_list.append(len(monthly_data))
        # 'Close_return' is the column in the which return for each of segmented data will be present
        # What is precentile: if score of student is 75, and its 85th percentile, only 15% students has score higher than or equal to 75
        describe = quarterly_data['Close_return'].describe()
        means.append(describe['mean'])
        seventyfive_percentiles.append(describe['75%'])
        fifty_percentiles.append(describe['50%'])
        twenty_five_percentiles.append(describe['25%'])
    describe_df = pd.DataFrame(
        {"Symbol": ticker_data_dic.keys(), "mean": means, "75": seventyfive_percentiles, "50": fifty_percentiles,
         "25": twenty_five_percentiles, "positive_count": positive_month_return_count_list,
         "total_count": total_month_list}, ticker_data_dic.keys())
    sum = describe_df['50'].sum()
    describe_df['weight'] = describe_df['50'] / sum
    describe_df['profit_month_ration'] = describe_df['positive_count'] / describe_df['total_count']
    return describe_df


def find_return_by_ticker(ticker_data_dic, total_amount, weight, symbol):
    ticker_data = ticker_data_dic[symbol]
    # to get teh cumm return using the global list and use that cummulative
    set_return_and_cum_return(ticker_data, 'Close')

    # this will give you final return for a stock if we had the split the total amount based on individual stock weight
    ticker_data['weighted_investment'] = total_amount * weight * ticker_data['Close_cum_return']
    # ticker_data['weighted_cum_return_on_amount1']=total_amount*weight
    regular_weight = 1 / len(ticker_data_dic)
    ticker_data['non_weighted_investment'] = total_amount * regular_weight * ticker_data['Close_cum_return']
    ticker_data['weight'] = weight
    # ticker_data.loc[asian_paint.index=='2010-01-04','Close']=444
    # ticker_data.iat[0,9]=total_amount*weight


# stock_meta_data=[]
def find_return_on_specific_amount(ticker_data_dic, amount):
    # this sets the metadata including weightage based on quarterly result and 50 percentile
    # below method does all this
    # for each of the ticker find the return for each quarter, and also find the 50 adn 75 percentile returns
    # for ex: if i have returns like 2,3,5,4,,5,6,8 quartelty return percentages and if i say 50 percentrile 3%, it says that > 50% of quarterly returns is > 3%
    # it also find weightages based on 50 percentile return, by diving individual 50 percentile returns by sum of all 50 percentile returns
    # includes describe details for each of the ticker, including weightage
    global stock_meta_data
    stock_meta_data = get_ticker_meta_data(ticker_data_dic)
    for index, row in stock_meta_data.iterrows():
        # 1.gets the cummulative percentage for each ticker
        # 2. get weighted cumm return  amount by multiplying cumm percnetage * weightage * iniital amount
        find_return_by_ticker(ticker_data_dic, amount, row['weight'], row.Symbol)

    # find teh sum of stock cumm data by merging it
    summed_data = merge_by_summing_col_data(ticker_data_dic)
    return summed_data
