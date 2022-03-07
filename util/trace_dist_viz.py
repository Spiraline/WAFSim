### Trace Distribution Visualizer

import os
import argparse
import tqdm
import matplotlib.pyplot as plt
from parse_helper import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, type=str)
    parser.add_argument('--page_size', '-p', default='8K', type=str)

    args = parser.parse_args()

    if not os.path.exists(args.input) or not os.path.isfile(args.input):
        print('[System] File does not exist! %s' % args.input)
        exit(1)

    if args.input.split('.')[-1] != 'trace':
        print('[System] File is not trace file! %s' % args.input)
        exit(1)

    page_size = parseIntPrefix(args.page_size)

    LBA_list = []
    
    with open(args.input, 'r') as trace_file:
        req_num = int(trace_file.readline())
        trace_max_addr = int(trace_file.readline())
        for req in tqdm.tqdm(range(req_num)):
            _, LBAs = parseReq(trace_file.readline(), page_size)
            for LBA in LBAs:
                LBA_list.append(LBA)

    plt.hist(LBA_list)
    plt.show()
        