import configparser
from util.workload_generator import WorkLoad
from util.parse_helper import *
from ssd.ftl import FTL
import matplotlib.pyplot as plt
from random import randint
from os.path import exists

if __name__ == "__main__":
    if not exists('config/config'):
        print('[Error] No configuration file. Please make config/config file')
        exit(1)

    config = configparser.ConfigParser()
    config.read('config/config')

    ### 0. Parse Configuration
    config['SSD']['block_num'] = str(parseIntPrefix(config['SSD']['block_num']))
    config['SSD']['page_per_block'] = str(parseIntPrefix(config['SSD']['page_per_block']))
    config['SSD']['page_size'] = str(parseIntPrefix(config['SSD']['page_size']))
    config['SSD']['simulation_tag'] = config['Simulator']['simulation_tag']

    lba_num = config.getint('SSD', 'block_num') * config.getint('SSD', 'page_per_block')
    ssd_capacity = config.getint('SSD', 'page_size') * lba_num

    ### Initialize statistics
    total_gc_cnt = 0
    total_waf = 0

    warmup_fill_tick = 0
    warmup_invalid_tick = 0
    if config['Simulator']['warmup_type'] != '':
        warmup_fill_tick = int(lba_num * config.getfloat('Simulator','fill_ratio'))
        warmup_invalid_tick = int(lba_num * config.getfloat('Simulator','invalid_ratio'))

    ### 1. Start trace simulation
    if config['Simulator']['simulation_type'] == 'Trace':
        if not exists(config.get('Trace', 'file_path')):
            print('[Error] No such trace file. Please check config/config file')
            exit(1)

        trace_file = open(config.get('Trace', 'file_path'), 'r')

        ### 1-1. Check SSD size is larger than trace's max address
        trace_max_addr = int(trace_file.readline())

        if ssd_capacity < trace_max_addr:
            print('[Error] SSD capacity is smaller than trace')
            print('SSD capacity:\t\t%d (%s) bytes' % (ssd_capacity, encodePrefix(ssd_capacity)))
            print('max addr in trace:\t%d (%s) bytes' % (trace_max_addr, encodePrefix(trace_max_addr)))
            exit(1)

        ### 1-2. Warm-up
        if warmup_fill_tick != 0:
            pass

        trace_file.close()

    ### 2. Start synthetic simulation
    elif config['Simulator']['simulation_type'] == 'Synthetic':
        config['Synthetic']['lba_num'] = str(lba_num)
        wl = WorkLoad(config['Synthetic'])

        max_tick = parseIntExp(config['Synthetic']['simulation_time'])
        iter_num = parseIntExp(config['Synthetic']['iter_num'])

        result_file = open(config['SSD']['victim_selection_policy'] + '_result_' + config['Simulator']['simulation_tag'] + '.csv', 'w')

        ### Iterate for iter_num times
        for i in range(iter_num):
            print("[Info] Iteration %d starts" % i)
            ### 2-1. configure SSD
            ssd = FTL(config['SSD'])
            
            # TODO : implement random fill warm-up
            if config['Simulator']['warmup_type'] != '':
                if config['Simulator']['warmup_type'] == '0':
                    for tick in range(warmup_fill_tick):
                        ssd.execute('write', tick, tick)
                    
                    for tick in range(warmup_invalid_tick):
                        lba = randint(0, warmup_fill_tick)
                        ssd.execute('erase', lba, warmup_fill_tick+tick)
                ssd.clearMetric()

            for tick in range(warmup_fill_tick + warmup_invalid_tick, warmup_fill_tick + warmup_invalid_tick + max_tick):
                op, lba = wl.getNextOperation()
                ssd.execute(op, lba, tick)

            waf = ssd.actual_write_pages / ssd.requested_write_pages
            total_gc_cnt += ssd.gc_cnt
            total_waf += waf
            print("[Info] Iteration %d ends | GC : %d, WAF : %f" % (i, ssd.gc_cnt, waf))
            result_file.write('%f, %f\n' % (ssd.gc_cnt, waf))

            # debug only first iteration
            config['SSD']['debug_gc_utilization'] = '0'
            config['SSD']['debug_gc_stat'] = '0'
        
        result_file.close()

        with open(config['SSD']['victim_selection_policy'] + '_result_' + config['Simulator']['simulation_tag'] + '.csv', 'w') as f:
            avg_gc_cnt = total_gc_cnt / iter_num
            avg_waf = total_waf / iter_num
            f.write('gc_cnt, waf\n')
            f.write('%f, %f\n' % (avg_gc_cnt, avg_waf))
    else:
        print('[Error] Invalid simulation type. Check config file')
        exit(1)
    
    # plt.plot([i for i in range(1000)], ssd.victim_utilization)
    # plt.hist(ssd.victim_utilization)
    # plt.show()