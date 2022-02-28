from .flash_memory import Block

class FTL:
    def __init__(self, config):
        Block.idx = 0
        self.block_num = int(config['block_num'])
        self.block_num_contain_op = int(self.block_num / (1 - float(config['op_ratio'])))
        self.page_per_block = int(config['page_per_block'])
        self.page_num = self.block_num * self.page_per_block

        ### SSD data structure
        self.mapping_table = [-1 for _ in range(self.page_num)]
        self.flash = [Block(self.page_per_block) for _ in range(self.block_num_contain_op)]

        ### SSD parameter
        self.victim_selection_policy = config['victim_selection_policy']

        self.U = int(config['utilization_factor'])
        self.H = int(config['hotness_factor'])
        self.D = int(config['decay_factor'])

        # gc threshold in page number scale
        self.gc_start_threshold = int(float(config['gc_start_threshold']) * self.block_num)
        self.gc_end_threshold = int(float(config['gc_end_threshold']) * self.block_num)
        
        ### For convinience
        # 0 is selected for current pbn
        self.__free_pbn = [i for i in range(1, self.block_num)]
        self.__current_pbn = 0
        self.__active_pbn = []
        # For over-provisioning
        self.__op_pbn = [i for i in range(self.block_num, self.block_num_contain_op)]
        self.__next_ppn = 0

        ### For debugging
        self.gc_cnt = 0

        # victim utilization histogram
        if config['debug_victim_hist'] in ['True', 'true', 1]:
            self.victim_hist_flag = True
            
            # w/o memory overflow (0.001 scale)
            # self.victim_utilization = [0 for _ in range(1000)]
            self.victim_utilization = []
        else:
            self.victim_hist_flag = False

        # Debug final utilization
        if config['debug_final_u'] in ['True', 'true', 1]:
            self.final_u_flag = True
        else:
            self.final_u_flag = False
        
        # self.debug_gc = int(config['debug_gc_utilization'])
        # self.sim_tag = config['simulation_tag']
        # if self.debug_gc != 0:
        #     with open(self.victim_selection_policy + '_gc_u_' + self.sim_tag + '.csv', 'w') as _:
        #         pass

        # self.debug_gc_stat = int(config['debug_gc_stat'])
        # if self.debug_gc_stat != 0:
        #     with open(self.victim_selection_policy + '_gc_stat_' + self.sim_tag + '.csv', 'w') as f:
        #         f.write('valid_page_copy,waf,live_page_num\n')
        
        self.requested_write_pages = 0
        self.actual_write_pages = 0

    def clearMetric(self):
        self.gc_cnt = 0
        # self.victim_utilization = [0 for _ in range(1000)]
        self.victim_utilization = []
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
        valid_page_copy = 0
        self.gc_cnt += 1
        ### 1. sort active blocks by metric
        # Cost-benefit
        if self.victim_selection_policy == 'CB':
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : -self.flash[pbn].getCostBenefit(ts))
        # CAT (Cost-Age-Time)
        elif self.victim_selection_policy == 'CAT':
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : -self.flash[pbn].getCostAgeTime(ts))
        # LC-CB
        elif self.victim_selection_policy == 'LC-CB':
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : self.flash[pbn].getLCCBMetric(self.U))
        # Default : Greedy
        else:
            candidate_blk = sorted(self.__active_pbn,
                            key = lambda pbn : self.flash[pbn].getLivePageNum())

        while len(self.__free_pbn) < self.gc_end_threshold:
            if len(candidate_blk) == 0:
                print('[WARN] No blocks to GC! Stop GC')
                break

            ### 2. select a victim block
            victim_idx = candidate_blk[0]
            victim = self.flash[victim_idx]
            del candidate_blk[0]
            # if u of victim block is 1, return and warn
            if victim.getLivePageNum() == self.page_per_block:
                print('[WARN] All active blocks have utilizaion 1! Stop GC')
                break
            
            if self.victim_hist_flag:
                # u = int(victim.getUtilization() * 1000)
                # self.victim_utilization[u] += 1
                self.victim_utilization.append(victim.getUtilization())

            ### 3. copy valid pages
            for offset in range(self.page_per_block):
                if victim.valid_bit[offset]:
                    lba = victim.lba[offset]
                    self.mapping_table[lba] = self.__next_ppn
                    new_pbn = self.__next_ppn // self.page_per_block
                    new_off = self.__next_ppn % self.page_per_block
                    self.flash[new_pbn].write(new_off, lba, victim.access_time, victim.invalid_time)
                    self.actual_write_pages += 1
                    self.updatePPN()
                    valid_page_copy += 1

            ### 4. erase block
            victim.erase()

            ### 5. update free block idx
            self.__active_pbn.remove(victim_idx)
            self.__free_pbn.append(victim_idx)

        ### (for LC-CB) clear weight to 0
        if self.victim_selection_policy == 'LC-CB':
            for blk_idx in self.__active_pbn:
                self.flash[blk_idx].setWeight(0)

        # if self.debug_gc_stat != 0:
        #     with open(self.victim_selection_policy + '_gc_stat_' + self.sim_tag + '.csv', 'a') as f:
        #         live_page_num = 0
        #         for pbn in self.__active_pbn:
        #             live_page_num += self.flash[pbn].getLivePageNum()
        #         waf = self.actual_write_pages / self.requested_write_pages
        #         f.write('%d,%f,%s' % (valid_page_copy, waf, live_page_num))
        #         f.write('\n')

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
                if self.victim_selection_policy == 'LC-CB':
                    addWeight = (self.flash[prev_pbn].getLivePageNum() - 1) >> self.H
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
            # TODO : should add weight if workload have erase op
            self.flash[pbn].invalidate(off, ts, 0)
            self.mapping_table[lba] = -1
        # Invalid op
        else:
            return -1

        ### Activate GC when needed
        if len(self.__free_pbn) < self.gc_start_threshold:
            # print('[Log] GC start (Free block # : %d, threshold : %d)' % (len(self.__free_pbn), self.gc_start_threshold))
            self.garbageCollection(ts)