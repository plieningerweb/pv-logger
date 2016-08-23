import logging
import traceback

from sqlite_influx import Config
from pyyasdi.objects import Plant

logger = logging.getLogger(__name__)

def read_all_inverter(wdog_manager):
    logger.info("read all inverters")

    measurements = {}
    try:
        plant = Plant(debug=1,
            max_devices=Config.config['sma_rs485_max_devices'])

        # if we make it till here without Exception, RS485 port was found
        wdog_manager.update_result('port_found', True)

        data = plant.data_all(parameter_channel=False)
        measurements.update(data)

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
