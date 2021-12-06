class Block:
    idx = 0
    def __init__(self, page_per_block):
        self.id = Block.idx + 1
        Block.idx += 1
        self.page_per_block = page_per_block
        self.lba = [-1 for _ in range(page_per_block)]
        self.valid_bit = [False for _ in range(page_per_block)]
        self.access_time = -1
        self.invalid_time = -1
        self.erase_count = 0

        # age for LC-CB and expandability
        self.weight = 0

        # TODO : For wear-leveling
        self.usage = 0

    def __str__(self):
        return_str = "Block %d\n" % (self.id)
        return_str += "access_time : %d, invalid_time : %d, weight : %d\n" % (self.access_time, self.invalid_time, self.weight)
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
        age = ts - self.invalid_time

        # Set to very small value if u == 0
        if u == 0:
            u = 0.01 / self.page_per_block

        return (1 - u) / (2 * u) * age

    def getCostAgeTime(self, ts):
        u = self.valid_bit.count(True) / self.page_per_block
        age = ts - self.access_time
        erase_count = self.erase_count

        if u == 0:
            u = 0.01 / self.page_per_block
        if erase_count == 0:
            erase_count = 0.01

        # TODO : different in every paper
        return (1 - u) / (2 * u) * age / self.erase_count

    def getLCCBMetric(self, A):
        return self.valid_bit.count(True) << A + self.weight

    def setWeight(self, value):
        self.weight = value

    def invalidate(self, offset, ts, addWeight = 0):
        if offset >= len(self.lba):
            return -1

        # Actually we don't need to clear lba
        self.lba[offset] = -1

        self.access_time = ts
        self.invalid_time = ts
        self.valid_bit[offset] = False
        self.weight += addWeight

    def read(self, offset, ts):
        if offset >= len(self.lba):
            return -1

        self.access_time = ts

        # We don't use read value now
        return self.lba[offset]

    def write(self, offset, lba, ts, invalid_time = -1):
        if offset >= len(self.lba):
            return -1

        self.lba[offset] = lba
        self.valid_bit[offset] = True

        # Normal write
        if invalid_time == -1:
            self.access_time = ts
        # Valid page copy in GC
        # In this case, ts = access_time from copied page        
        else:
            if ts > self.access_time:
                self.access_time = ts
            if invalid_time > self.invalid_time:
                self.invalid_time = invalid_time

        return 0

    def erase(self):
        for offset in range(self.page_per_block):
            self.lba[offset] = -1
            self.valid_bit[offset] = False
        self.access_time = -1
        self.invalid_time = -1
        self.weight = 0
        self.usage = 0
        self.erase_count += 1