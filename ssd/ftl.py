from .flash_memory import Block

class FTL:
    def __init__(self, config):
        self.block_num = int(config['block_num'])
        self.page_per_block = int(config['page_per_block'])
        self.page_num = self.block_num * self.page_per_block

        # SSD data structure
        self.mapping_table = [-1 for _ in range(self.page_num)]
        self.flash = [Block(self.page_per_block) for _ in range(self.block_num)]

        # gc threshold in page number scale
        self.gc_start_threshold = int(float(config['gc_start_threshold']) * self.page_num)
        self.gc_end_threshold = int(float(config['gc_end_threshold']) * self.page_num)
        self.victim_selection_policy = int(config['victim_selection_policy'])

        # For convinience
        self.free_block_num = self.block_num
        self.free_block_idx = [i for i in range(int(self.block_num * float(config['overprovisioning_ratio'])))]
        self.current_block = 0
        self.active_block_idx = []
        self.next_ppn = 0

        # For debugging
        self.gc_cnt = 0
        self.copied_valid_page = 0
        self.utilization_for_victim_block = []
        self.requested_write_pages = 0
        self.actual_write_pages = 0
        self.WAF = 0
    
    def getNextPPN(self):
        pass

    def garbageCollection(self):
        pass
        # 1. calculate weights for active blocks

        # 2. sort
        candidate_blk = sorted(self.active_block_idx, )

        # 3. select a victim block
        # 4. if u of victim block is 1, return and warn
        # 5. copy valid pages
        # 6. erase block
        # 7. update free block idx
        # 8. (for ours) clear weight to 0

    def execute(self, op, lba, ts):
        if op == 'read':
            ppn = self.mapping_table[lba]
            pbn = ppn // self.page_per_block
            offset = ppn % self.page_per_block
            self.flash[pbn].read(offset, lba, ts)
        elif op == 'write':
            self.requested_write_pages += 1
            self.actual_write_pages += 1
            ppn = self.mapping_table[lba]

            # Unmapped yet
            if ppn == -1:
                self.mapping_table[lba] = self.next_ppn
                new_pbn = self.next_ppn // self.page_per_block
                new_off = self.next_ppn % self.page_per_block
                print("unmapped", lba, ppn, self.next_ppn, ts)
                self.flash[new_pbn].write(new_off, lba, ts)
                self.next_ppn += 1
                # TODO : get next block if block is full
            else:
                prev_pbn = ppn // self.page_per_block
                prev_off = ppn % self.page_per_block
                # TODO : add weight when our metric
                self.flash[prev_pbn].invalidate(prev_off, ts, 0)

                # TODO : GC if needed

                self.mapping_table[lba] = self.next_ppn
                new_pbn = self.next_ppn // self.page_per_block
                new_off = self.next_ppn % self.page_per_block
                self.flash[new_pbn].write(new_off, lba, ts)
                print("mapped", lba, ppn, self.next_ppn, ts)
                self.next_ppn += 1
        # Invalid op
        else:
            return -1
        