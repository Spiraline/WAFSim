import configparser
from util.workload_generator import WorkLoad
from util.parse_helper import *
from ssd.ftl import FTL
import matplotlib.pyplot as plt
from random import randint, seed
from os.path import exists, isfile, join, basename
from os import makedirs, listdir

if __name__ == "__main__":
    makedirs('res', exist_ok=True)
    if not exists('config/config'):
        print('[Error] No configuration file. Please make config/config file')
        exit(1)

    config = configparser.ConfigParser()
    config.read('config/config')

    ### Parse Configuration
    config['SSD']['block_num'] = str(parseIntPrefix(config['SSD']['block_num']))
    config['SSD']['page_per_block'] = str(parseIntPrefix(config['SSD']['page_per_block']))
    config['SSD']['page_size'] = str(parseIntPrefix(config['SSD']['page_size']))
    
    config['SSD']['debug_victim_hist'] = config['Simulator']['debug_victim_hist']
    config['SSD']['debug_gc_stat'] = config['Simulator']['debug_gc_stat']

    lba_num = config.getint('SSD', 'block_num') * config.getint('SSD', 'page_per_block')
    page_size = config.getint('SSD', 'page_size')
    ssd_capacity = page_size * lba_num

    if config['Simulator']['seed'] != '':
        seed(config.getint('Simulator', 'seed'))

    warmup_fill_tick = 0
    warmup_invalid_tick = 0
    warmup_type = config['Simulator']['warmup_type']
    if warmup_type != '':
        warmup_fill_tick = lba_num * config.getint('Simulator','fill_percentage') // 100
        warmup_invalid_tick = lba_num * config.getint('Simulator','invalid_percentage') // 100

    ### 1. Start trace simulation
    if config['Simulator']['simulation_type'] == 'Trace':
        trace_path = config.get('Trace', 'trace_path')
        if not exists(trace_path):
            print('[Error] No such trace file/dir %s. Please check config/config file' % trace_path)
            exit(1)
        
        trace_list = []
        if isfile(trace_path):
            trace_list.append(trace_list)
        else:
            for name in listdir(trace_path):
                if name.split('.')[-1] == 'trace':
                    trace_list.append(join(trace_path, name))

        for (idx, trace_file_path) in enumerate(trace_list):
            trace_file = open(trace_file_path, 'r')
            trace_name = basename(trace_file_path).split('.')[0]

            ### 1-1. Check SSD size is larger than trace's max address
            req_num = int(trace_file.readline())
            trace_max_addr = int(trace_file.readline())

            if ssd_capacity < trace_max_addr:
                print('[Error] SSD capacity is smaller than trace')
                print('SSD capacity:\t\t%d (%s) bytes' % (ssd_capacity, encodePrefix(ssd_capacity)))
                print('max addr in trace:\t%d (%s) bytes' % (trace_max_addr, encodePrefix(trace_max_addr)))
                exit(1)

            ssd = FTL(config['SSD'])

            tick = 0

            print("[Info] (%d / %d) Simulation with trace %s starts" % (idx+1, len(trace_list), trace_name))

            ### 1-2. Warm-up
            if warmup_type != '':
                fill_progress = 0
                print("[Info] Warm-up starts")
                if warmup_type == '0':
                    while tick < warmup_fill_tick:
                        curr_fill_progress = (int)(tick / warmup_fill_tick * 10)
                        if fill_progress != curr_fill_progress:
                            fill_progress = curr_fill_progress
                            print('[Info] Warm-up (fill) %d %% Complete' % (fill_progress * 10))
                        ssd.execute('write', tick, tick)
                        tick += 1
                # Random fill
                elif warmup_type == '1':
                    while tick < warmup_fill_tick:
                        curr_fill_progress = (int)(tick / warmup_fill_tick * 10)
                        if fill_progress != curr_fill_progress:
                            fill_progress = curr_fill_progress
                            print('[Info] Warm-up (fill) %d %% Complete' % (fill_progress * 10))
                        lba = randint(0, lba_num-1)

                        # Fill only for unwritten lba
                        if ssd.mapping_table[lba] == -1:
                            ssd.execute('write', lba, tick)
                            tick += 1
                else:
                    print('[Error] Invalid warm-up type')
                    exit(1)
                
                invalid_progress = 0
                # Random invalid
                while tick < warmup_fill_tick + warmup_invalid_tick:
                    curr_invalid_progress = (int)((tick - warmup_fill_tick) / warmup_invalid_tick * 10)
                    if invalid_progress != curr_invalid_progress:
                        invalid_progress = curr_invalid_progress
                        print('[Info] Warm-up (invalidate) %d %% Complete' % (invalid_progress * 10))
                    lba = randint(0, lba_num-1)

                    # Invalid only for written lba
                    if ssd.mapping_table[lba] != -1:
                        ssd.execute('erase', lba, tick)
                        tick += 1
                
                ssd.clearMetric()

            ### 1-3. Simulation
            max_req = req_num * config.getint('Trace', 'execute_percentage') // 100

            sim_progress = 0
            for req in range(max_req):
                curr_sim_progress = (int)(req / max_req * 20)
                if sim_progress != curr_sim_progress:
                    sim_progress = curr_sim_progress
                    print('[Info] Simulation %d %% Complete' % (sim_progress * 5))
                op, lba_list = parseReq(trace_file.readline(), page_size)
                for lba in lba_list:
                    ssd.execute(op, lba, tick)
                    tick += 1

            trace_file.close()

            if ssd.requested_write_pages == 0:
                print("[Info] No write request")
                exit(1)

            waf = ssd.actual_write_pages / ssd.requested_write_pages
            print('[Info] Simulation Complete')
            print('[Info] Req # : %d' % max_req)
            print('[Info] GC : %d, WAF : %f' % (ssd.gc_cnt, waf))

            result_path = 'res/' + config['SSD']['victim_selection_policy'] + '_trace'
            if config['Simulator']['simulation_tag'] != '':
                result_path += '_' + config['Simulator']['simulation_tag']
            result_path += '_result.csv'
            with open(result_path, 'w') as result_file:
                result_file.write('%s, %d, %f\n' % (trace_name, ssd.gc_cnt, waf))
    ### 2. Start synthetic simulation
    elif config['Simulator']['simulation_type'] == 'Synthetic':
        ### Initialize statistics
        total_gc_cnt = 0
        total_waf = 0

        result_path = 'res/' + config['SSD']['victim_selection_policy'] + '_synthetic'
        if config['Simulator']['simulation_tag'] != '':
            result_path += '_' + config['Simulator']['simulation_tag']
        result_path += '_result.csv'
        result_file = open(result_path, 'w')

        config['Synthetic']['lba_num'] = str(lba_num * config.getint('Synthetic', 'working_set_percentage') // 100)
        wl = WorkLoad(config['Synthetic'])

        max_tick = parseIntExp(config['Synthetic']['simulation_time'])
        iteration_num = parseIntExp(config['Synthetic']['iteration_num'])

        ### Iterate for iteration_num times
        for i in range(iteration_num):
            print("[Info] Exp #%d starts" % i)
            ### 2-1. configure SSD
            ssd = FTL(config['SSD'])
            tick = 0
            
            ### 1-2. Warm-up
            if warmup_type != '':
                fill_progress = 0
                print("[Info] Warm-up starts")
                if warmup_type == '0':
                    while tick < warmup_fill_tick:
                        curr_fill_progress = (int)(tick / warmup_fill_tick * 10)
                        if fill_progress != curr_fill_progress:
                            fill_progress = curr_fill_progress
                            print('[Info] Warm-up (fill) %d %% Complete' % (fill_progress * 10))
                        ssd.execute('write', tick, tick)
                        tick += 1
                # Random fill
                elif warmup_type == '1':
                    while tick < warmup_fill_tick:
                        curr_fill_progress = (int)(tick / warmup_fill_tick * 10)
                        if fill_progress != curr_fill_progress:
                            fill_progress = curr_fill_progress
                            print('[Info] Warm-up (fill) %d %% Complete' % (fill_progress * 10))
                        lba = randint(0, lba_num-1)

                        # Fill only for unwritten lba
                        if ssd.mapping_table[lba] == -1:
                            ssd.execute('write', lba, tick)
                            tick += 1
                else:
                    print('[Error] Invalid warm-up type')
                    exit(1)
                
                invalid_progress = 0
                # Random invalid
                while tick < warmup_fill_tick + warmup_invalid_tick:
                    curr_invalid_progress = (int)((tick - warmup_fill_tick) / warmup_invalid_tick * 10)
                    if invalid_progress != curr_invalid_progress:
                        invalid_progress = curr_invalid_progress
                        print('[Info] Warm-up (invalidate) %d %% Complete' % (invalid_progress * 10))
                    lba = randint(0, lba_num-1)

                    # Invalid only for written lba
                    if ssd.mapping_table[lba] != -1:
                        ssd.execute('erase', lba, tick)
                        tick += 1
                
                ssd.clearMetric()

            # 2-3. Simulation
            print("[Info] Simulation with synthetic workload starts")
            sim_progress = 0
            for req in range(max_tick):
                curr_sim_progress = (int)(req / max_tick * 10)
                if sim_progress != curr_sim_progress:
                    sim_progress = curr_sim_progress
                    print('[Info] Simulation %d %% Complete' % (sim_progress * 10))
                op, lba = wl.getNextOperation()
                ssd.execute(op, lba, tick)
                tick += 1

            waf = ssd.actual_write_pages / ssd.requested_write_pages
            total_gc_cnt += ssd.gc_cnt
            total_waf += waf
            print("[Info] Iteration %d ends | GC : %d, WAF : %f" % (i, ssd.gc_cnt, waf))
            result_file.write('%d, %f\n' % (ssd.gc_cnt, waf))

        avg_gc_cnt = total_gc_cnt / iteration_num
        avg_waf = total_waf / iteration_num
        result_file.write('------- Average ---------\n')
        result_file.write('%f, %f\n' % (avg_gc_cnt, avg_waf))

        result_file.close()
    else:
        print('[Error] Invalid simulation type. Check config file')
        exit(1)
    
    if config.getboolean('Simulator', 'debug_victim_hist'):
        # plt.plot([i for i in range(1000)], ssd.victim_utilization)
        # plt.plot(ssd.victim_utilization)
        plt.hist(ssd.victim_utilization, bins=50)
        hist_path = 'res/' + config['SSD']['victim_selection_policy']
        if config['Simulator']['simulation_type'] == 'Trace':
            hist_path += '_' + trace_name
        else:
            hist_path += '_Synthetic'
        if config['Simulator']['simulation_tag'] != '':
            hist_path += '_' + config['Simulator']['simulation_tag']
        hist_path += '_victim_histogram.png'
        plt.savefig(hist_path)

    if config.getboolean('Simulator', 'debug_final_u'):
        final_u_path = 'res/' + config['SSD']['victim_selection_policy']
        if config['Simulator']['simulation_type'] == 'Trace':
            final_u_path += '_' + trace_name
        else:
            final_u_path += '_Synthetic'
        if config['Simulator']['simulation_tag'] != '':
            final_u_path += '_' + config['Simulator']['simulation_tag']
        final_u_path += '_final_u_histogram.png'

        u_list = []
        for blk in ssd.flash:
            u_list.append(blk.getUtilization())
            
        plt.hist(u_list, bins=50)
        plt.savefig(final_u_path)

    if config.getboolean('Simulator', 'debug_gc_stat'):
        gc_stat_path = 'res/' + config['SSD']['victim_selection_policy']
        if config['Simulator']['simulation_type'] == 'Trace':
            gc_stat_path += '_' + trace_name
        else:
            gc_stat_path += '_Synthetic'
        if config['Simulator']['simulation_tag'] != '':
            gc_stat_path += '_' + config['Simulator']['simulation_tag']
        gc_stat_path += '_gc_stat.csv'

        with open(gc_stat_path, 'w') as gc_stat_file:
            gc_stat_file.write('valid_page_copy,waf,live_page_num\n')
            for vp, waf, lpn in ssd.gc_stat_list:
                gc_stat_file.write('%d,%f,%d\n' % (vp, waf, lpn))