import unittest as unittest
try:
    from unittest import mock
except ImportError:
    import mock

from pv_logger import logger as pvlogger

pvlogger.Config.config['inverter_type'] = 'sma_rs485'

class HighlevelTest(unittest.TestCase):
    def get_rows(self):
        rows = pvlogger.sqlite.session.query(pvlogger.sqlite.History).all()
        rows_converted = [pvlogger.sqlite.history_to_dict(row) for row in rows]
        for item in rows_converted:
            print(item)

        return rows_converted

    def remove_all_rows(self):
        pvlogger.sqlite.session.query(pvlogger.sqlite.History).delete()

    def test_loop(self):
        pvlogger.main_loop()

        rows = self.get_rows()
        self.remove_all_rows()

        self.assertEqual(rows[0]['fields']['last_request_status'], 'error')
        self.assertEqual(len(rows), 2)

        sma_rs485_loaded = ('sma_rs485.py' in repr(rows[0]['fields']))
        self.assertEqual(sma_rs485_loaded, True)
