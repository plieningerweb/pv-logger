"""read data from kacors485, cache them locally in sqlite
and finally sync them to remote InfluxDB server (assume local ssh tunnel)"""

import yaml
import logging
import time
import traceback
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
from kacors485 import kacors485
from pv_logger import watchdog

wdog_manager = watchdog.Manager()
# setup checks at import, because also in functions used (not only in main)
check_conf = Config.config['checks']['internet_connection']
wdog_manager.register_check('internet_connection',
    datetime.timedelta(seconds=check_conf['interval_seconds']),
    min_fails_in_row=check_conf['min_fails_in_row'],
    callback=watchdog.test_internet_connection)

check_conf = Config.config['checks']['tty_usb_found']
wdog_manager.register_check('tty_usb_found',
    datetime.timedelta(seconds=check_conf['interval_seconds']),
    min_fails_in_row=check_conf['min_fails_in_row'])

def read_inverter(kaco, inverter_id):
    #read inverter with address i
    inv_data = kaco.readInverterAndParse(int(inverter_id))

    logger.info("read inverter {}: {}".format(inverter_id, inv_data))

    return inv_data

def read_all_inverter():
    logger.info("read all inverters")

    measurements = {}
    try:
        kaco = kacors485.KacoRS485(Config.config['port'])

        # if we make it till here without Exception, RS485 port was found
        wdog_manager.update_result('tty_usb_found', True)

        inverters = Config.config['inverter_ids']
        for i in inverters:
            # read data
            data = read_inverter(kaco, i)

            # convert to measurement format
            measurement = 'inverter'+str(i)
            fields = {k:data[k]['value'] for k in data}

            # add to all measurements
            measurements[measurement] = fields

        kaco.close()

        # set communication info
        measurements['communication'] = {
            'last_request_status': 'ok'
        }
    except Exception:
        trace = traceback.format_exc()
        logger.exception("error while requesting inverters")

        # set communication info
        measurements['communication'] = {
            'last_request_status': 'error',
            'error_msg': trace
        }

    return measurements

def main_loop():
    # get measurements
    measurements = read_all_inverter()

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
