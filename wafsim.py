import configparser
from workload.workload_generator import WorkLoad
from ssd.ftl import FTL
import matplotlib.pyplot as plt

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])
    max_tick = int(config['Simulator']['simulation_time'])

    ssd = FTL(config['SSD'])

    for tick in range(max_tick):
        op, lba = wl.getNextOperation()
        ssd.execute(op, lba, tick)

    waf = ssd.actual_write_pages / ssd.requested_write_pages
    print("GC cnt : ", ssd.gc_cnt)
    print("WAF : ", waf)
    
    # plt.plot([i for i in range(1000)], ssd.victim_utilization)
    # plt.hist(ssd.victim_utilization)
    # plt.show()