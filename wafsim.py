import configparser
from util.workload_generator import WorkLoad
from util.config_parser import parseIntExp
from ssd.ftl import FTL
import matplotlib.pyplot as plt
from random import randint

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])
    max_tick = parseIntExp(config['Simulator']['simulation_time'])
    iter_num = parseIntExp(config['Simulator']['iter_num'])

    fill_tick = 0
    invalid_tick = 0
    if config['Simulator']['warmup_type'] != '':
        lba_size = int(config['Workload']['lba_size'])
        fill_tick = int(lba_size * float(config['Simulator']['fill_ratio']))
        invalid_tick = int(lba_size * float(config['Simulator']['invalid_ratio']))

    total_gc_cnt = 0
    total_waf = 0

    # with open(config['SSD']['victim_selection_policy'] + '_result.csv', 'w') as f:
    #     f.write('gc_cnt, waf\n')

    for i in range(iter_num):
        ssd = FTL(config['SSD'])
        
        # TODO : implement random fill warm-up
        if config['Simulator']['warmup_type'] != '':
            if config['Simulator']['warmup_type'] == '0':
                for tick in range(fill_tick):
                    ssd.execute('write', tick, tick)
                
                for tick in range(invalid_tick):
                    lba = randint(0, fill_tick)
                    ssd.execute('erase', lba, fill_tick+tick)
            ssd.clearMetric()

        for tick in range(fill_tick + invalid_tick, fill_tick + invalid_tick + max_tick):
            op, lba = wl.getNextOperation()
            ssd.execute(op, lba, tick)

        waf = ssd.actual_write_pages / ssd.requested_write_pages
        total_gc_cnt += ssd.gc_cnt
        total_waf += waf
        print("[Iteration %d] GC : %d, WAF : %f" % (i, ssd.gc_cnt, waf))

        # debug only first iteration
        config['SSD']['debug_gc_utilization'] = '0'
        config['SSD']['debug_gc_stat'] = '0'

    with open(config['SSD']['victim_selection_policy'] + '_result_' + config['SSD']['simulation_tag'] + '.csv', 'w') as f:
        avg_gc_cnt = total_gc_cnt / iter_num
        avg_waf = total_waf / iter_num
        f.write('gc_cnt, waf\n')
        f.write('%f, %f\n' % (avg_gc_cnt, avg_waf))
    
    # plt.plot([i for i in range(1000)], ssd.victim_utilization)
    # plt.hist(ssd.victim_utilization)
    # plt.show()