import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stock_analysis_util import *
import json

from util import get_pickle_data

a = '''
Highcharts.chart('container', {{

  title: {{
    text: 'Solar Employment Growth by Sector, 2010-2016'
  }},

  subtitle: {{
    text: 'Source: thesolarfoundation.com'
  }},

  yAxis: {{
    title: {{
      text: 'Number of Employees'
    }}
  }},

  xAxis: {{
    accessibility: {{
      rangeDescription: 'Range: 2010 to 2017'
    }}
  }},

  legend: {{
    layout: 'vertical',
    align: 'right',
    verticalAlign: 'middle'
  }},

  plotOptions: {{
    series: {{
      label: {{
        connectorAllowed: false
      }},
      pointStart: 2010
    }}
  }},

  series: {stock_data},

  responsive: {{
    rules: [{{
      condition: {{
        maxWidth: 500
      }},
      chartOptions: {{
        legend: {{
          layout: 'horizontal',
          align: 'center',
          verticalAlign: 'bottom'
        }}
      }}
    }}]
  }}

}});

'''


def plot_by_segment(ticker_data_dic, by_segment, col_name):
    series = []
    # plt.figure(figsize=(40,20))
    for segment in by_segment.keys():
        segment_entry = {}
        frames_to_be_combined = []
        for symbol in by_segment[segment]:
            if symbol in ticker_data_dic.keys():
                copied_ticker_data = ticker_data_dic[symbol].copy()
                # reset_indv_ticker_index(copied_ticker_data)
                set_return_and_cum_return(copied_ticker_data, 'Close')
                frames_to_be_combined.append(copied_ticker_data)
                segment_entry['name'] = symbol
                segment_entry['data'] = copied_ticker_data['Close_cum_return'].values.tolist()
        if len(frames_to_be_combined) > 0:
            all_combined = pd.concat(frames_to_be_combined).groupby(['id']).sum().reset_index()
            set_return_and_cum_return(all_combined, 'Close')
            # plt.plot(all_combined[['Close_cum_return']],label=segment,alpha=1)
            segment_entry['name'] = segment
            segment_entry['data'] = all_combined['Close_cum_return'].values.tolist()
            series.append(segment_entry)

    # plt.legend()
    # plt.show(block=True)
    return series


def plot_data_under_segment(ticker_data_dic, by_segment, segment_name):
    series = []
    header_segment_entry = {}
    # plt.figure(figsize=(40,20))
    frames_to_be_combined = []
    for symbol in by_segment[segment_name]:
        child_segment_entry = {}
        # copied_ticker_data=ticker_data_dic[symbol].copy()
        global copied_ticker_data
        if symbol in ticker_data_dic:
            copied_ticker_data = ticker_data_dic[symbol]
            # copied_ticker_data.is_copy = False
            reset_indv_ticker_index(copied_ticker_data)
            set_return_and_cum_return(copied_ticker_data, 'Close')
            frames_to_be_combined.append(copied_ticker_data)
            child_segment_entry['name'] = symbol
            child_segment_entry['data'] = copied_ticker_data['Close_cum_return'].values.tolist()
            series.append(child_segment_entry)

    all_combined = pd.concat(frames_to_be_combined).groupby(['id']).sum().reset_index()
    set_return_and_cum_return(all_combined, 'Close')
    header_segment_entry['name'] = segment_name
    header_segment_entry['data'] = all_combined['Close_cum_return'].values.tolist()
    series.append(header_segment_entry)
    # plt.legend()
    # plt.show(block=True)
    return series


def plot_data(summed_data):
    plt.figure(figsize=(40, 20))
    # resampled_ticker_df=resample(ticker_data_dic[key],freq)
    plt.plot(summed_data['weighted_investment_cum_return'], label='key', alpha=1)
    plt.legend()
    plt.show()


def get_summed_series(summed_data):
    summed_series = {}
    summed_series['name'] = "summed"
    summed_series['data'] = summed_data['weighted_investment_cum_return'].values.tolist()
    return summed_series


def get_segments(global_ticker_data_dic_with_sector):
    by_segment = {}
    for symbol in global_ticker_data_dic_with_sector:
        sector = global_ticker_data_dic_with_sector[symbol]['sector']
        if sector not in by_segment:
            sector_stocks = [symbol]
            by_segment[sector] = sector_stocks
        else:
            by_segment[sector].append(symbol)
    return by_segment


def plot_stock_data():
    start_date = "2017-03-08"
    end_date = "2022-03-08"
    global_ticker_data_dic_with_sector = get_pickle_data('my-top-list-historical-data')
    by_segment = get_segments(global_ticker_data_dic_with_sector)
    global_ticker_data_dic = reset_index(global_ticker_data_dic_with_sector)
    # removing the one that has 0 data.

    global_ticker_data_dic = filter_by_date(global_ticker_data_dic, start_date, end_date)
    # this is to filter out symbols that doesnt have trading for all the days
    len_of_asianpaint = len(global_ticker_data_dic['ASIANPAINT'])
    global_ticker_data_dic = filter_by_content(global_ticker_data_dic, len_of_asianpaint)
    in_ticker_dic = ('CAMS' in global_ticker_data_dic.keys())
    print(f'{len(global_ticker_data_dic)} and {in_ticker_dic}')
    # print(by_segment)
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'FMCG')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Building Products')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Chemicals')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'IT Services')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Pharmaceuticals')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Paint')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Private Banks')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Agro Chemicals')
    # series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Cement')
    series = plot_data_under_segment(global_ticker_data_dic, by_segment, 'Healthcare')
    # series = plot_by_segment(global_ticker_data_dic, by_segment, '')
    # print(series)
    stock_data = json.dumps(series, indent=4, sort_keys=True)
    f = open("demofile2.txt", "w")
    f.write(a.format(stock_data=stock_data))
    f.close()


def do_the_analysis():
    start_date = "2015-03-08"
    end_date = "2022-03-08"
    global_ticker_data_dic_with_sector = get_pickle_data('my-top-list-historical-data')
    print(global_ticker_data_dic_with_sector.keys())
    # global_ticker_data_dic=get_pickle_data('nifty-500-analysis-historical-data')

    # global_ticker_data_dic={'BAJAJFINSV':global_ticker_data_dic['BAJAJFINSV'],'ASIANPAINT':global_ticker_data_dic['ASIANPAINT']}
    # print(global_ticker_data_dic)
    global_ticker_data_dic = reset_index(global_ticker_data_dic_with_sector)
    # removing the one that has 0 data.
    global_ticker_data_dic = filter_by_date(global_ticker_data_dic, start_date, end_date)
    # this is to filter out symbols that doesnt have trading for all the days
    len_of_asianpaint = len(global_ticker_data_dic['ASIANPAINT'])
    global_ticker_data_dic = filter_by_content(global_ticker_data_dic, len_of_asianpaint)

    by_segment = get_segments(global_ticker_data_dic_with_sector)
    # global_ticker_data_dic=filter_by_segment(global_ticker_data_dic,by_segment,'Electrical Components & Equipments')
    # global_ticker_data_dic={'ASIANPAINT':global_ticker_data_dic['ASIANPAINT'],'ASIANPAINT1':global_ticker_data_dic['ASIANPAINT']}
    # get the weight based on quarterly result and split the amount initial amount among the stocks accordingly.
    ticker_meta_data = get_ticker_meta_data(global_ticker_data_dic)

    # to find the return if we split the total amount based on the weights (based on consistent quarter perf. using percentile) calcuated based on prev. returns
    summed_data = find_return_on_specific_amount(global_ticker_data_dic, 1000000)
    summed_data.index = pd.to_datetime(summed_data.id)
    quarterly_data = resample(summed_data, "3M", 'Close')
    print(summed_data.iloc[-1])
    series = get_summed_series(summed_data)
    # series = plot_by_segment(global_ticker_data_dic, by_segment, '')
    # print(series)
    series_data = json.dumps([series], indent=4, sort_keys=True)
    f = open("summed_data.txt", "w")
    f.write(a.format(stock_data=series_data))
    f.close()


# do_the_analysis()
plot_stock_data()
