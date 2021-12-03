import configparser
from workload.workload_generator import WorkLoad

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config/config')

    wl = WorkLoad(config['Workload'])

    for _ in range(int(config['Simulator']['simulation_time'])):
        print(wl.getNextOperation())

    

    