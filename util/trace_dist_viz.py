### Trace Distribution Visualizer

import argparse
import matplotlib.pyplot as plt
from parse_helper import *
from tqdm import tqdm
from os.path import exists, isfile, join, basename
from os import makedirs, listdir

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, type=str)
    parser.add_argument('--page_size', '-p', default='8K', type=str)
    parser.add_argument('--tqdm', '-t', action='store_true')

    makedirs('res', exist_ok=True)

    args = parser.parse_args()

    if not exists(args.input):
        print('[System] Path does not exist! %s' % args.input)
        exit(1)

    trace_list = []
    if isfile(args.input):
        if args.input.split('.')[-1] != 'trace':
            print('[System] File is not trace file! %s' % args.input)
            exit(1)
        else:
            trace_list.append(args.input)
    else:
        for name in listdir(args.input):
            if name.split('.')[-1] == 'trace':
                trace_list.append(join(args.input, name))

    page_size = parseIntPrefix(args.page_size)

    read_ratio_file = open('res/rw_ratio.csv', 'w')
    read_ratio_file.write('trace,read_num,write_num,write_ratio,max_LBA,LBA_in_use,utilization\n')

    for trace_path in trace_list:
        LBA_list = []
        read_num = 0
        write_num = 0
        LBA_in_use = set()
        trace_name = basename(trace_path).split('.')[0]
        
        with open(trace_path, 'r') as trace_file:
            req_num = int(trace_file.readline())
            trace_max_addr = int(trace_file.readline())
            if args.tqdm:
                progress = tqdm(total=req_num)
                progress.set_description(trace_name)
            for req in range(req_num):
                op, LBAs = parseReq(trace_file.readline(), page_size)
                if op == 'write':
                    write_num += 1
                    for LBA in LBAs:
                        LBA_in_use.add(LBA)
                        LBA_list.append(LBA)
                else:
                    read_num += 1
                if args.tqdm:
                    progress.update(1)
            if args.tqdm:
                progress.close()

        max_LBA = trace_max_addr // page_size
        utilization = len(LBA_in_use) / max_LBA * 100
        write_ratio = write_num / (read_num + write_num) * 100

        read_ratio_file.write('%s,%d,%d,%f,%d,%d,%f\n'
            % (trace_name, read_num, write_num, write_ratio,
                max_LBA,len(LBA_in_use),utilization))

        fig, ax = plt.subplots()
        plt.hist(LBA_list, bins=500)
        plt.savefig("res/%s-dist.png" % trace_name)
        plt.close(fig)