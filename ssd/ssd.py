from .ftl import FTL
from .flash_memory import Block

class SSD:
    def __init__(self, config):
        self.page_num = int(config['block_num']) * int(config['page_per_block'])

        # SSD data structure
        self.mapping_table = [-1 for _ in range(self.page_num)]
        self.ftl = FTL(config)

        # gc threshold in page number scale
        self.gc_start_threshold = int(float(config['gc_start_threshold']) * self.page_num)
        self.gc_end_threshold = int(float(config['gc_end_threshold']) * self.page_num)

        # For debugging
        self.gc_cnt = 0
        self.copied_valid_page = 0
        self.utilization_for_victim_block = []
        self.requested_write_pages = 0
        self.actual_write_pages = 0
        self.WAF = 0

    def operate(op, lba, ts):
        pass