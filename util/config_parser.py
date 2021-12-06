def parseIntExp(num_str):
    if num_str.find('e') != -1:
        return int(num_str.split('e')[0]) * pow(10, int(num_str.split('e')[1]))
    elif num_str.isdecimal():
        return int(num_str)
    else:
        print('[Error] Can not parse string %s' % num_str)
        exit(1)