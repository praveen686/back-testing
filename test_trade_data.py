from typing import List

import pandas as pd
from pandas import DataFrame

from option_util import get_minute_list
from util import get_pickle_data, get_diff_in_mins, write_pickle_data


def analyze_profit_series(trade_df_list: List[DataFrame]):
    time_series = get_minute_list('%H:%M:%S')
    # time_series = [minute.strftime("%H:%M:%S") for minute in minute_list]
    trade_df_1 = trade_df_list[0]
    trade_df_2 = trade_df_list[1]
    count_days_above_threshold = {'10': 0, '15': 0, '20': 0, '25': 0, '30': 0}
    for i in range(len(trade_df_1)):
        zero_fill = [0 for i in range(len(time_series))]
        base_df = pd.DataFrame({"base": zero_fill}, time_series)
        # base_df = base_df.join(day_premium_change_df)
        profit_series_1 = list(map(float, str(trade_df_1.iloc[i]['profit_series']).split(",")))
        profit_series_2 = list(map(float, str(trade_df_2.iloc[i]['profit_series']).split(",")))
        final_df = pd.DataFrame({"p1": profit_series_1, "p2": profit_series_2}, time_series)
        final_df = pd.DataFrame({"p1": profit_series_1, "p2": profit_series_2}, time_series)
        final_df['p'] = final_df["p1"] + final_df["p2"]
        for key in count_days_above_threshold:
            if len(final_df[final_df.p > key]) > 0:
                count_days_above_threshold[key] = count_days_above_threshold[key] + 1
    return count_days_above_threshold


def analyze_file(list_trade_params: List, week_day, file_suffix, unique_id=""):
    all_trades = []
    result = {}
    trade_df_list = []
    for trade_params in list_trade_params:
        start_time = trade_params[0]
        sl = trade_params[1]
        file_name = f'trade_data/trade_data_{start_time}_{sl}{file_suffix}.data'
        ind_trades = get_pickle_data(file_name)
        trade_df = pd.DataFrame(ind_trades)
        trade_df.index = pd.to_datetime(trade_df.trade_date)
        per_day_df = trade_df.resample('1D').agg(
            {'profit': 'sum', 'trade_date': 'min', 'sl_hit_count': 'min', 'other_sl_hit': 'max', 'week_day': 'min'})
        trade_df_list.append(per_day_df)
        all_trades.extend(ind_trades)
    # count_days_above_threshold = analyze_profit_series(trade_df_list)
    all_trades_df = pd.DataFrame(all_trades)
    all_trades_df.index = pd.to_datetime(all_trades_df.trade_date)
    per_day_df = all_trades_df.resample('1D').agg(
        {'profit': 'sum', 'trade_date': 'min', 'sl_hit_count': 'min', 'other_sl_hit': 'max', 'week_day': 'min'})
    per_day_df = per_day_df[per_day_df.profit != 0]

    # filtering by week_day if passed
    if week_day > -1:
        per_day_df = per_day_df[per_day_df.week_day == week_day]
    per_day_df['profit'] = per_day_df['profit'] / len(list_trade_params)
    # if "all" in file_name:
    #     r.profit = r.profit / 2
    per_day_df.index = pd.to_datetime(per_day_df.trade_date)

    per_month_df = per_day_df.resample('M').agg(
        {'profit': 'sum', 'trade_date': 'min', 'sl_hit_count': 'min', 'other_sl_hit': 'max'})
    result['negative_months_count'] = len(per_month_df[per_month_df.profit < 0])
    # result['negative_months'] = ",".join(map(str, per_month_df[per_month_df.profit < 0].profit.values))
    result['lowest_monthly_profit'] = round(per_month_df.sort_values('profit').profit.values[0])
    result['tot_profit'] = round(per_day_df.profit.sum())

    result['mean_day_profit'] = round(per_day_df["profit"].mean())
    result['std_day_profit'] = round(per_day_df["profit"].std())
    result['negative_days_count'] = len(per_day_df[per_day_df.profit < 0])

    by_weekly_df = per_day_df[['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    per_day_df['Cumulative'] = per_day_df.profit.cumsum().round(2)
    per_day_df['HighValue'] = per_day_df['Cumulative'].cummax()
    per_day_df['DrawDown'] = per_day_df['Cumulative'] - per_day_df['HighValue']
    result['drawdown'] = round(per_day_df.sort_values('DrawDown').DrawDown.values[0])

    # risk reward
    # result['win_days'] = len(per_day_df[per_day_df.profit > 0])
    win_days_count = len(per_day_df[per_day_df.profit > 0])
    # result['loss_days'] = len(per_day_df[per_day_df.profit < 0])
    loss_days_count = len(per_day_df[per_day_df.profit < 0])
    # result['win_days_mean'] = round(per_day_df[per_day_df.profit > 0]['profit'].mean())
    win_days_mean = round(per_day_df[per_day_df.profit > 0]['profit'].mean())
    # result['loss_days_mean'] = round(per_day_df[per_day_df.profit < 0]['profit'].mean())
    loss_days_mean = round(per_day_df[per_day_df.profit < 0]['profit'].mean())
    result['win_loss_day_ratio'] = round(win_days_count / loss_days_count)
    result['rr_ratio'] = round(abs(win_days_mean / loss_days_mean))

    # getting percentiles
    describe = per_month_df['profit'].describe()
    result['75'] = round(describe['75%'])
    result['50'] = round(describe['50%'])
    result['25'] = round(describe['25%'])

    # getting yearly break down
    per_year_df = per_day_df.resample('Y').agg(
        {'profit': 'sum', 'trade_date': 'min', 'sl_hit_count': 'min', 'other_sl_hit': 'max'})
    for year_index in range(len(per_year_df['profit'])):
        result[f'year:{year_index}'] = round(per_year_df['profit'][year_index])

    # getting the weekly data
    by_week_df = per_day_df[['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    for week_index in range(len(by_week_df['profit']['sum'])):
        week_df_index = by_week_df['profit']['sum'].index[week_index]
        result[f'day:{week_df_index}'] = round(by_week_df['profit']['sum'][week_df_index])
        # if week_index in by_week_df['profit']['sum']:
        #     result[f'day:{week_index}'] = round(by_week_df['profit']['sum'][week_index])
        # else:
        #     print("ee")
    # for week_day_index in by_week_df['profit']['sum']:
    #     print(by_week_df['profit']['sum'][week_day_index])
    # result['mon'] = round(by_week_df['profit']['sum'][0])
    # result['tue'] = round(by_week_df['profit']['sum'][1])
    # result['wed'] = round(by_week_df['profit']['sum'][2])
    # result['thu'] = round(by_week_df['profit']['sum'][3])
    # result['fri'] = round(by_week_df['profit']['sum'][4])

    # lowest and highest
    result['max'] = round(per_day_df.sort_values('profit', ascending=False).profit.values[0])
    result['min'] = round(per_day_df.sort_values('profit').profit.values[0])
    # finding the longest losing streak
    per_day_df['loss'] = per_day_df['profit'] < 0
    per_day_df['streak'] = per_day_df['loss'].groupby(
        (per_day_df['loss'] != per_day_df['loss'].shift()).cumsum()).cumcount() + 1
    result['max_losing_streak'] = round(
        per_day_df[per_day_df.loss == True].sort_values('streak', ascending=False).streak.values[0])
    if unique_id == "":
        if len(list_trade_params) > 1:
            merge = pd.merge(trade_df_list[0], trade_df_list[1], how='inner', left_index=True, right_index=True)
            correlate_value = merge['profit_x'].corr(merge['profit_y'])
            result['correlation'] = round(correlate_value, 3)
            result[
                'id'] = f'{list_trade_params[0][0]}@{list_trade_params[0][1]}||{list_trade_params[1][0]}@{list_trade_params[1][1]}'
        else:
            result[
                'id'] = f'{list_trade_params[0][0]}@{list_trade_params[0][1]}'
    else:
        result['id'] = unique_id
    # per_day_df[['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    # per_day_df[per_day_df.sl_hit_count == 2][['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    # per_day_df[per_day_df.profit < 0][['profit', 'week_day']].groupby(['week_day']).agg(['mean', 'sum', 'count'])
    return result


class IntervalSl:
    def __init__(self, interval, sl):
        self.interval = interval
        self.sl = sl


def get_non_correlated_groups():
    non_correlated_groups: [[IntervalSl, IntervalSl]] = []
    all_interval_sl_list = get_all_interval_sl_list()
    for index, lead_elem in enumerate(all_interval_sl_list):
        for child_index in range(index + 1, len(all_interval_sl_list)):
            child_elem = all_interval_sl_list[child_index]

            # print(elem, trade_intervals[child_index], )
            time_in_mins = get_diff_in_mins(lead_elem.interval, child_elem.interval)
            if time_in_mins >= 30:
                non_correlated_groups.append([lead_elem, child_elem])
    print(all_interval_sl_list, non_correlated_groups)
    return non_correlated_groups


def get_all_interval_sl_list():
    trade_intervals = ["0920", "0940", "1000", "1020", "1040",
                       "1100", "1120", "1140", "1200", "1220", "1240", "1300", "1320", "1340", "1400"]
    sl_list = [.2, .3, .4, .5, .6]
    all_interval_sl_list: List[IntervalSl] = []

    for interval_index, interval_elem in enumerate(trade_intervals):
        for sl_index, sl_elem in enumerate(sl_list):
            all_interval_sl_list.append(IntervalSl(interval_elem, sl_elem))
    return all_interval_sl_list


def analyze_trade_data(file_suffix: str, week_day):
    non_correlated_groups = get_non_correlated_groups()
    # non_correlated_groups = non_correlated_groups[:100]
    analysis_results = []
    for group_index, group in enumerate(non_correlated_groups):
        analysis_result = analyze_file([[group[0].interval, group[0].sl], [group[1].interval, group[1].sl]],
                                       week_day, file_suffix)
        analysis_results.append(analysis_result)
        print(f'current index :{group_index} size:{len(non_correlated_groups)}')
    indexes = [i for i in range(len(analysis_results))]
    trade_data_analysis_df = pd.DataFrame(analysis_results, indexes)
    write_pickle_data(f'trade_data_analysis{file_suffix}_{week_day}_df', trade_data_analysis_df)


def analyze_single_entry_trade_dat():
    all_interval_sl_list = get_all_interval_sl_list()
    analysis_results = []
    for entry_index, entry in enumerate(all_interval_sl_list):
        analysis_result = analyze_file([[entry.interval, entry.sl]], -1, "")
        analysis_results.append(analysis_result)
        print(f'current index :{entry_index}')
    indexes = [i for i in range(len(analysis_results))]
    trade_data_analysis_df = pd.DataFrame(analysis_results, indexes)
    write_pickle_data('trade_data_single_entry_analysis_df', trade_data_analysis_df)


def analyze_week_day_trade_data(weekday: int):
    # 0920@0.2||1020@0.2
    # 0940@0.2||1020@0.2
    # 0920@0.3||1020@0.2
    analysis_results = []
    analysis_result = analyze_file([["0920", .2], ["1020", .2]], 0, "")
    analysis_results.append(analysis_result)
    analysis_result = analyze_file([["0940", .2], ["1020", .2]], 0, "")
    analysis_results.append(analysis_result)
    analysis_result = analyze_file([["0920", .3], ["1020", .2]], 0, "")
    analysis_results.append(analysis_result)
    trade_data_analysis_df = pd.DataFrame(analysis_results, [0, 1, 2])
    write_pickle_data(f'week_day_df_{weekday}', trade_data_analysis_df)


def analyze_indv_trade_data():
    # day 0 0920@0.2||1020@0.2 0940@0.2||1040@0.2 1000@0.3||1100@0.2 1000@0.2||1220@0.3
    analysis_results = []
    # 0940@0.6||1040@0.6
    # 0940@0.5||1040@0.6
    # 1040@0.6||1120@0.6
    analysis_result = analyze_file([["0940", .6], ["1040", .6]], 2, "", "first")
    analysis_results.append(analysis_result)
    analysis_result = analyze_file([["0940", .5], ["1040", .6]], 2, "", "second")
    analysis_results.append(analysis_result)
    analysis_result = analyze_file([["1040", .6], ["1120", .6]], 2, "", "third")
    analysis_results.append(analysis_result)

    trade_data_analysis_df = pd.DataFrame(analysis_results, [0, 1, 2])
    write_pickle_data('week_day_2_df', trade_data_analysis_df)
    return
    # 0940@0.2||1140@0.2 0940@0.3||1320@0.2  0940@0.3||1140@0.2
    analysis_result = analyze_file([["0940", .2], ["1140", .2], ["0940", .3], ["1320", .3]])
    analysis_result = analyze_file([["0920", .2], ["0940", .2]], -1, "")
    analysis_result = analyze_file([["0940", .2], ["1140", .2]], -1, "")
    print(analysis_result)
    analysis_result = analyze_file([["0940", .3], ["1320", .3]], -1, "")
    print(analysis_result)
    # 0920@0.6||1000@0.6
    # 0940@0.2||1030@0.6
    analysis_result = analyze_file([["0940", .2], ["1030", .6]], 2, "")
    trade_data_analysis_df = pd.DataFrame([analysis_result], [0])
    write_pickle_data('week_day_df', trade_data_analysis_df)

# best combination for each day
# 0940@0.5||1120@0.6 (index : 524) - wednesday condition - negative mon count <5, tot proft >3200,win_loss_d ratio >2, rr ratio>1,year3>0,max loss streak<5
#  1.9 L is the amount placed.
# analyze_indv_trade_data()
# analyze_single_entry_trade_dat()
# analyze_week_day_trade_data(0)
analyze_trade_data("", 2)
# analyze_indv_trade_data()
# 0940@0.2||1140@0.2 -- index 970
# 0940@0.2||1200@0.3 -- index 976
# 0950@0.2||1130@0.3 -- index 1386
# 0940@0.2||1300@0.3 -- index 991
# 0940@0.2||1320@0.2 -- index 995
# 0940@0.3||1320@0.3 -- index 1081

# new

# 925 0940@0.2||1010@0.2
# 1030 0940@0.3||1050@0.2
# analyze_trade_data()
# correlate_groups = [
#     ["0920", "1030", "1040", "1050", "1100", "1110", "1120", "1130"],
#     ["0930", "1030", "1040", "1050", "1100", "1110", "1120", "1130"],
#     ["0940", "1040", "1050", "1100", "1110", "1120", "1130"],
#     ["0950", "1050", "1100", "1110", "1120", "1130"],
#     ["1000", "1100", "1110", "1120", "1130"],
#     ["1010", "1110", "1120", "1130"],
#     ["1020", "1120", "1130"],
#     ["1030", "1130"],
# ]
# sl_list = [.2, .3, .4, .5, .6]
#
# analysis_results = []
# for sl in sl_list:
#     for group_index in range(len(start_time_groups) - 1):
#         start_time_group
#         analysis_result = analyze_file([[start_time_groups, .2], ['1130', .2]])
# trade_data_analysis_df = pd.DataFrame(result, ["eee"])
# print("")
