import logging
import traceback

from sqlite_influx import Config
from kacors485 import kacors485

logger = logging.getLogger(__name__)

def read_inverter(kaco, inverter_id):
    #read inverter with address i
    inv_data = kaco.readInverterAndParse(int(inverter_id))

    logger.info("read inverter {}: {}".format(inverter_id, inv_data))

    return inv_data

def read_all_inverter(wdog_manager):
    logger.info("read all inverters")

    measurements = {}
    try:
        kaco = kacors485.KacoRS485(Config.config['kaco_port'])

        # if we make it till here without Exception, RS485 port was found
        wdog_manager.update_result('port_found', True)

        inverters = Config.config['kaco_inverter_ids']
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
