"""read data from kacors485, cache them locally in sqlite
and finally sync them to remote InfluxDB server (assume local ssh tunnel)"""

import yaml
import logging
import time
import os
import datetime

from sqlite_influx import Config

# setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# setup config first, before we import the other stuff
config_file = 'config.yaml'
with open(config_file, 'r') as stream:
    logger.info("read config file {}".format(os.path.abspath(config_file)))
    config_yaml = yaml.load(stream)
Config.config.update(config_yaml)

# now import helpers, which initialize database
# based on config data
from sqlite_influx import sqlite
from pv_logger import watchdog
from pv_logger import kaco, sma_rs485

wdog_manager = watchdog.Manager()
# setup checks at import, because also in functions used (not only in main)
check_conf = Config.config['checks']['internet_connection']
wdog_manager.register_check('internet_connection',
    datetime.timedelta(seconds=check_conf['interval_seconds']),
    min_fails_in_row=check_conf['min_fails_in_row'],
    callback=watchdog.test_internet_connection)

check_conf = Config.config['checks']['port_found']
wdog_manager.register_check('port_found',
    datetime.timedelta(seconds=check_conf['interval_seconds']),
    min_fails_in_row=check_conf['min_fails_in_row'])


def read_data():
    inverter_type = Config.config['inverter_type']
    if inverter_type == 'kaco':
        return kaco.read_all_inverter(wdog_manager)
    elif inverter_type == 'sma_rs485':
        return sma_rs485.read_all_inverter(wdog_manager)

def main_loop():
    # get measurements
    measurements = read_data()

    # append more information
    uptime_app = datetime.datetime.now() - wdog_manager.start_time
    measurements['uptime'] = {
        'node': str(watchdog.get_uptime()),
        'app': str(uptime_app)
    }

    # store measurements
    sqlite.store_dicts(measurements)

    sqlite.sync_to_influx()
    sqlite.archive(Config.config['archive_older_than_days'])

    # run watchdog manager
    wdog_manager.run()

def main():
    # run main loop
    while True:
        main_loop()
        time.sleep(Config.config['read_interval_seconds'])

if __name__ == '__main__':
    main()
