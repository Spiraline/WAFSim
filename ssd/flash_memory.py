class Block:
    idx = 0
    def __init__(self, page_per_block):
        self.id = Block.idx + 1
        Block.idx += 1
        self.page_per_block = page_per_block
        self.lba = [-1 for _ in range(page_per_block)]
        self.valid_bit = [False for _ in range(page_per_block)]
        self.accessTime = -1
        self.invalidTime = -1

        # weight for LC-CB and expandability
        self.weight = 0

        # TODO : For wear-leveling
        self.usage = 0

    def __str__(self):
        return_str = "Block %d\n" % (self.id)
        return_str += "accessTime : %d, invalidTime : %d, weight : %d\n" % (self.accessTime, self.invalidTime, self.weight)
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
        age = ts - self.invalidTime

        # Set to very small value if u == 0
        if u == 0:
            u = 0.01 / self.page_per_block

        return (1 - u) / (2 * u) * age

    def getLCCBMetric(self, A):
        return self.valid_bit.count(True) << A + self.weight

    def setWeight(self, value):
        self.weight = value

    def invalidate(self, offset, ts, addWeight = 0):
        if offset >= len(self.lba):
            return -1

        # Actually we don't need to clear lba
        self.lba[offset] = -1

        self.accessTime = ts
        self.invalidTime = ts
        self.valid_bit[offset] = False
        self.weight += addWeight

    def read(self, offset, ts):
        if offset >= len(self.lba):
            return -1

        self.accessTime = ts

        # We don't use read value now
        return self.lba[offset]

    def write(self, offset, lba, ts, invalidTime = -1):
        if offset >= len(self.lba):
            return -1

        self.lba[offset] = lba
        self.valid_bit[offset] = True

        # Normal write
        if invalidTime == -1:
            self.accessTime = ts
        # Valid page copy in GC
        # In this case, ts = accessTime from copied page        
        else:
            if ts > self.accessTime:
                self.accessTime = ts
            if invalidTime > self.invalidTime:
                self.invalidTime = invalidTime

        return 0

    def erase(self):
        for offset in range(self.page_per_block):
            self.lba[offset] = -1
            self.valid_bit[offset] = False
        self.accessTime = -1
        self.invalidTime = -1
        self.weight = 0
        self.usage = 0