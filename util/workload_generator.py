from random import randint, random

class WorkLoad:
    def __init__(self, config):
        self.lba_num = int(config['lba_num'])
        self.workload_type = int(config['workload_type'])
        self.read_ratio = float(config['read_ratio'])
        self.locality = float(config['locality'])
        self.__last_lba = -1

    def __getSeqLBA(self):
        if self.__last_lba == self.lba_num - 1:
            self.__last_lba = 0
        else:
            self.__last_lba += 1
        
        return self.__last_lba

    def __getRandomLBA(self):
        return randint(0, self.lba_num)

    # TODO : should read only writed lba

    def __getHotColdLBA(self):
        hot_idx = int(self.lba_num * self.locality)
        if random() > self.locality:
            # hot data
            return randint(0, hot_idx)
        else:
            return randint(hot_idx, self.lba_num)

    def getNextOperation(self):
        op = -1
        lba = -1
        # seq write
        if self.workload_type == 0:
            op = 'write'
            lba = self.__getSeqLBA()
        elif self.workload_type == 1:
            op = 'write'
            lba = self.__getRandomLBA()
        elif self.workload_type == 2:
            if random() < self.read_ratio:
                op = 'read'
            else:
                op = 'write'
            lba = self.__getRandomLBA()
        elif self.workload_type == 3:
            op = 'write'
            lba = self.__getHotColdLBA()
        
        return op, lba