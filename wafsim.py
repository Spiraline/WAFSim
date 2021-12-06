import configparser
from workload.workload_generator import WorkLoad
from ssd.ftl import FTL
import matplotlib.pyplot as plt
from random import randint

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])
    sim_t_str = config['Simulator']['simulation_time']
    if sim_t_str.find('e') != -1:
        max_tick = int(sim_t_str.split('e')[0]) * pow(10, int(sim_t_str.split('e')[1]))
    else:
        max_tick = int(sim_t_str)

    ssd = FTL(config['SSD'])

    fill_tick = 0
    invalid_tick = 0
    
    # TODO : implement random fill warm-up
    if config['Simulator']['warmup_type'] != '':
        lba_size = int(config['Workload']['lba_size'])
        fill_tick = int(lba_size * float(config['Simulator']['fill_ratio']))
        invalid_tick = int(lba_size * float(config['Simulator']['invalid_ratio']))
        if config['Simulator']['warmup_type'] == '0':
            for tick in range(fill_tick):
                ssd.execute('write', tick, tick)
            
            for tick in range(invalid_tick):
                lba = randint(0, fill_tick)
                ssd.execute('erase', lba, fill_tick+tick)
        ssd.clearMetric()

        # for blk in ssd.flash:
        #     print(blk.getUtilization(), end=' ')
        # print()

    for tick in range(fill_tick + invalid_tick, fill_tick + invalid_tick + max_tick):
        op, lba = wl.getNextOperation()
        ssd.execute(op, lba, tick)

    waf = ssd.actual_write_pages / ssd.requested_write_pages
    print("GC cnt : ", ssd.gc_cnt)
    print("WAF : ", waf)
    
    # plt.plot([i for i in range(1000)], ssd.victim_utilization)
    # plt.hist(ssd.victim_utilization)
    # plt.show()