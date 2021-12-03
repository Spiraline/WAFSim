import configparser
from workload.workload_generator import WorkLoad
from ssd.ssd import SSD

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])
    max_tick = int(config['Simulator']['simulation_time'])

    ssd = SSD(config['SSD'])

    # for tick in range(max_tick):
    #     op, lba = wl.getNextOperation()



    

    