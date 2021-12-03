class Block:
    idx = 0
    def __init__(self, page_per_block):
        self.id = Block.idx + 1
        Block.idx += 1
        self.page_per_block = page_per_block
        self.lba = [-1 for _ in range(page_per_block)]
        self.valid_bit = [False for _ in range(page_per_block)]
        self.accessTime = -1

        # weight for ours and expandability
        self.weight = 0

        # TODO : For wear-leveling
        self.usage = 0

    def __str__(self):
        return_str = "Block %d\n" % (self.id)
        return_str += "accessTime : %d, weight : %d\n" % (self.accessTime, self.weight)
        return_str += "valid\tLBA\n"
        for offset in range(self.page_per_block):
            return_str += "%s\t%s\n" % (self.valid_bit[offset], self.lba[offset])

        return return_str

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

    def updateWeight(self, value):
        self.weight = value

    def invalidate(self, offset, ts, addWeight = 0):
        if offset >= len(self.lba):
            return -1

        # Actually we don't need to clear lba
        self.lba[offset] = -1

        self.valid_bit[offset] = False
        self.accessTime = ts
        self.weight += addWeight

    def read(self, offset, ts):
        if offset >= len(self.lba):
            return -1

        self.accessTime = ts

        # We don't use read value now
        return self.lba[offset]

    def write(self, offset, lba, ts):
        if offset >= len(self.lba):
            return -1

        self.lba[offset] = lba
        self.valid_bit[offset] = True
        self.accessTime = ts

        return 0

    def erase(self):
        for offset in range(self.page_per_block):
            self.lba[offset] = -1
            self.valid_bit[offset] = False
        self.accessTime = -1
        self.weight = 0
        self.usage = 0