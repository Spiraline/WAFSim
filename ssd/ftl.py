from .flash_memory import Block

class FTL:
    def __init__(self, config):
        self.block_num = int(config['block_num'])
        self.page_per_block = int(config['page_per_block'])
        self.page_num = self.block_num * self.page_per_block

        ### SSD data structure
        self.mapping_table = [-1 for _ in range(self.page_num)]
        self.flash = [Block(self.page_per_block) for _ in range(self.block_num)]

        ### SSD parameter
        self.victim_selection_policy = int(config['victim_selection_policy'])

        # TODO : rename
        self.A = int(config['A'])
        self.B = int(config['B'])

        # gc threshold in page number scale
        self.gc_start_threshold = int(float(config['gc_start_threshold']) * self.block_num)
        self.gc_end_threshold = int(float(config['gc_end_threshold']) * self.block_num)
        
        ### For convinience
        # 0 is selected for current pbn
        self.__free_pbn = [i for i in range(1, int(self.block_num * (1 - float(config['op_ratio']))))]
        self.__current_pbn = 0
        self.__active_pbn = []
        self.__next_ppn = 0

        ### For debugging
        self.gc_cnt = 0

        # for histogram w/o memory overflow (0.001 scale)
        self.victim_utilization = [0 for _ in range(1000)]

        # self.victim_utilization = []
        self.requested_write_pages = 0
        self.actual_write_pages = 0

    def clearMetric(self):
        self.gc_cnt = 0
        self.victim_utilization = [0 for _ in range(1000)]
        # self.victim_utilization = []
        self.requested_write_pages = 0
        self.actual_write_pages = 0
    
    def updatePPN(self):
        self.__next_ppn += 1
        # if block is full
        if self.__next_ppn % self.page_per_block == 0:
            self.__active_pbn.append(self.__current_pbn)

            # No free block left. Very Dangerous
            if len(self.__free_pbn) == 0:
                self.__current_pbn = -1
                self.__next_ppn = 0
            else:
                self.__current_pbn = self.__free_pbn[0]
                del self.__free_pbn[0]
                self.__next_ppn = self.__current_pbn * self.page_per_block

    def garbageCollection(self, ts):
        self.gc_cnt += 1
        ### 1. sort active blocks by metric
        # Greedy
        if self.victim_selection_policy == 0:
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : self.flash[pbn].getLiveBlockNum())
        # Cost-benefit
        elif self.victim_selection_policy == 1:
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : -self.flash[pbn].getCostBenefit(ts))
        # Ours
        else:
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : self.flash[pbn].getOurMetric(self.A))
        
        # for blk in candidate_blk:
        #     print(self.flash[blk].getLiveBlockNum() , end=' ')
        # print()

        while len(self.__free_pbn) < self.gc_end_threshold:
            if len(candidate_blk) == 0:
                print('[WARN] No blocks to GC! Stop GC')
                break

            ### 2. select a victim block
            victim_idx = candidate_blk[0]
            victim = self.flash[victim_idx]
            del candidate_blk[0]
            # if u of victim block is 1, return and warn
            if victim.getLiveBlockNum() == self.page_per_block:
                print('[WARN] All active blocks have utilizaion 1! Stop GC')
                break

            # TODO : tune resolution
            u = int(victim.getUtilization() * 1000)
            self.victim_utilization[u] += 1
            # self.victim_utilization.append(victim.getUtilization())

            ### 3. copy valid pages
            for offset in range(self.page_per_block):
                accessTime = victim.accessTime
                if victim.valid_bit[offset]:
                    lba = victim.lba[offset]
                    self.mapping_table[lba] = self.__next_ppn
                    new_pbn = self.__next_ppn // self.page_per_block
                    new_off = self.__next_ppn % self.page_per_block
                    self.flash[new_pbn].write(new_off, lba, accessTime)
                    self.actual_write_pages += 1

            ### 4. erase block
            victim.erase()

            ### 5. update free block idx
            self.__active_pbn.remove(victim_idx)
            self.__free_pbn.append(victim_idx)

            ### 6. (for ours) clear weight to 0
            if self.victim_selection_policy == 2:
                for blk_idx in self.__active_pbn:
                    self.flash[blk_idx].setWeight(0)

        # print('GC end.. and now free block number is %d' % (len(self.__free_pbn)))

    def execute(self, op, lba, ts):
        # print(op, lba, ts)
        if lba >= self.page_num:
            print("[Error] Invlaid LBA %d (page # is %d)!" % (lba, self.page_num))
            exit(1)

        if op == 'read':
            ppn = self.mapping_table[lba]
            pbn = ppn // self.page_per_block
            offset = ppn % self.page_per_block
            self.flash[pbn].read(offset, lba, ts)
        elif op == 'write':
            if self.__current_pbn == -1:
                print("[Error] No free page left!")
                exit(1)

            self.requested_write_pages += 1
            self.actual_write_pages += 1
            ppn = self.mapping_table[lba]

            # 1. Invalidate if already mapped
            if ppn != -1:
                prev_pbn = ppn // self.page_per_block
                prev_off = ppn % self.page_per_block
                addWeight = 0
                if self.victim_selection_policy == 2:
                    addWeight = self.flash[prev_pbn].getLiveBlockNum() >> self.B
                self.flash[prev_pbn].invalidate(prev_off, ts, addWeight)

            # 2. 
            self.mapping_table[lba] = self.__next_ppn
            new_pbn = self.__next_ppn // self.page_per_block
            new_off = self.__next_ppn % self.page_per_block
            self.flash[new_pbn].write(new_off, lba, ts)
            # print("mapped", lba, ppn, self.__next_ppn, ts)
            self.updatePPN()
        elif op == 'erase':
            ppn = self.mapping_table[lba]
            pbn = ppn // self.page_per_block
            off = ppn % self.page_per_block
            self.flash[pbn].invalidate(off, ts, 0)
            self.mapping_table[lba] = -1
        # Invalid op
        else:
            return -1

        ### Activate GC when needed
        if len(self.__free_pbn) < self.gc_start_threshold:
            # print('[Log] GC start (Free block # : %d, threshold : %d)' % (len(self.__free_pbn), self.gc_start_threshold))
            self.garbageCollection(ts)