from zerodha_algo_trader import ZerodhaBrokingAlgo

zerodha = ZerodhaBrokingAlgo(is_testing=False, sleep_time=5)
# todo delete the file u created while testing
# zerodha.load_straddles_from_file()
# zerodha.generate_straddle_from_existing_zerodha_position()
zerodha.place_straddle_order(1.6, 25)
# zerodha.analyze_existing_positions()
# get_latest_b_nifty('33')
# prepare_option_legs()
# generate_ticker_symbol()
# zerodha.zerodha_api.get_zerodha_open_positions()
# zerodha.zerodha_api.get_zerodha_open_orders()
# get_latest_b_nifty("e")
# zerodha.attach_zerodha_order([])