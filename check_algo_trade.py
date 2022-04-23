import time

from zerodha_algo_trader import ZerodhaBrokingAlgo

start_time = time.time()
check_interval = 60

zerodha = ZerodhaBrokingAlgo(is_testing=False, sleep_time=5)

while True:
    local_start_time = time.time()
    print("about to check")
    zerodha.analyze_existing_positions()
    local_end_time = time.time()
    print(f'done checking; time taken:{round(local_end_time-local_start_time)}')
    time.sleep(check_interval - ((time.time() - start_time) % check_interval))
    local_end_time = time.time()
    print(f'done with sleep; time taken:{round(local_end_time - local_start_time)}')


