def parseIntExp(num_str):
    if num_str.find('e') != -1:
        return int(num_str.split('e')[0]) * pow(10, int(num_str.split('e')[1]))
    elif num_str.isdecimal():
        return int(num_str)
    else:
        print('[Error] Can not parse string %s' % num_str)
        exit(1)

def parseIntPrefix(num_str):
    if num_str[-1] == 'T':
        return int(num_str[:-1]) * 1024 * 1024 * 1024
    if num_str[-1] == 'G':
        return int(num_str[:-1]) * 1024 * 1024
    if num_str[-1] == 'M':
        return int(num_str[:-1]) * 1024 * 1024
    if num_str[-1] == 'K':
        return int(num_str[:-1]) * 1024
    elif num_str.isdecimal():
        return int(num_str)
    else:
        print('[Error] Can not parse string %s' % num_str)
        exit(1)

def encodePrefix(num):
    coeff = num
    prefix_idx = 0
    prefix_list = ['', 'K', 'M', 'G', 'T']

    while coeff >= 1024:
        coeff //= 1024
        prefix_idx += 1
    
    return str(coeff) + prefix_list[prefix_idx]

def parseReq(req_str, page_size = parseIntPrefix('8K')):
    ts, addr, size, opcode = map(int, req_str.split())

    lba_list = []
    base_lba = addr // page_size

    for i in range(size // page_size + 1):
        lba_list.append(base_lba + i)

    if opcode == 0:
        op = 'write'
    else:
        op = 'read'

    return op, lba_list, ts