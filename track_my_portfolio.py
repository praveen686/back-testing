import pandas as pd

from stock_analysis_util import reset_index, set_return_and_cum_return, filter_by_date
from util import get_pickle_data, write_pickle_data


class PortFolioAnalyzer:
    def __init__(self):
        print("")
        self.portfolio_data_dic_with_meta_data = get_pickle_data("my-top-list-historical-data")
        self.ticker_data = None

    def analyze_data(self):
        start_date = "2022-03-15"
        end_date = "2022-03-17"
        print(self)
        portfolio_data_dic = reset_index(self.portfolio_data_dic_with_meta_data)
        portfolio_data_dic = filter_by_date(portfolio_data_dic, start_date, end_date)
        frames_to_be_combined = []
        for symbol in portfolio_data_dic:
            self.ticker_data = portfolio_data_dic[symbol]
            count = self.portfolio_data_dic_with_meta_data[symbol]['count']
            # print(self.portfolio_data_dic[symbol]['count'])
            self.ticker_data['count'] = count
            self.ticker_data['investment'] = count * self.ticker_data['Close']
            frames_to_be_combined.append(self.ticker_data)
        all_combined = pd.concat(frames_to_be_combined).groupby(['id']).sum().reset_index()
        set_return_and_cum_return(all_combined, 'investment')
        return all_combined

    def print_close_for_all(self):
        for key in self.portfolio_data_dic_with_meta_data:
            ticker_data = self.portfolio_data_dic_with_meta_data[key]['data']
            print(f'{key}:{ticker_data.iloc[-1]["Close"]}')


analyzer = PortFolioAnalyzer()
analyzer.print_close_for_all()
# all_combined = analyzer.analyze_data()
# write_pickle_data('portfolio_df', all_combined)
