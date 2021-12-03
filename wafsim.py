import configparser
from workload.workload_generator import WorkLoad
from ssd.ftl import FTL

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])
    max_tick = int(config['Simulator']['simulation_time'])

    ssd = FTL(config['SSD'])

    for tick in range(max_tick):
        op, lba = wl.getNextOperation()
        ssd.execute(op, lba, tick)

    for blk in ssd.flash:
        print(blk)