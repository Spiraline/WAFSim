class Block:
    def __init__(self, page_per_block):
        self.page_per_block = page_per_block
        self.lba = [-1 for _ in range(page_per_block)]
        self.valid_bit = [False for _ in range(page_per_block)]
        self.accessTime = -1
        self.weight = 0

        # TODO : For wear-leveling
        self.usage = 0

    def getLiveBlockNum(self):
        return self.valid_bit.count(True)

    def getUtilization(self):
        return self.valid_bit.count(True) / self.page_per_block

    def getCostBenefit(self, ts):
        u = self.valid_bit.count(True) / self.page_per_block
        age = ts - self.accessTime

        return (1 - u) / (2 * u) * age

    def getOurMetric(self):
        pass

    def invalidate(self, idx, ts, _weight = 0):
        if idx >= len(self.lba):
            return -1

        # Actually we don't need to clear lba
        self.lba[idx] = -1

        self.valid_bit[idx] = False

        self.accessTime = ts
        self.weight += _weight

    def read(self, idx, ts):
        if idx >= len(self.lba):
            return -1

        self.accessTime = ts

        # We don't use read value now
        return self.lba[idx]

    def write(self, idx, lba, ts):
        if idx >= len(self.lba):
            return -1

        self.lba[idx] = lba
        self.accessTime = ts

        return 0

    def erase(self):
        for idx in range(self.page_per_block):
            self.lba[idx] = -1
            self.valid_bit[idx] = False
        self.accessTime = -1
        self.weight = 0
        self.usage = 0