import unittest as unittest
import serial
import os
try:
    from unittest import mock
except ImportError:
    import mock

from pv_logger import kaco

class HighlevelTest(unittest.TestCase):
    def get_rows(self):
        rows = kaco.sqlite.session.query(kaco.sqlite.History).all()
        rows_converted = [kaco.sqlite.history_to_dict(row) for row in rows]
        for item in rows_converted:
            print(item)

        return rows_converted

    def remove_all_rows(self):
        kaco.sqlite.session.query(kaco.sqlite.History).delete()

    def test_loop(self):
        kaco.main_loop()

        rows = self.get_rows()
        self.remove_all_rows()

        self.assertEqual(rows[0]['fields']['last_request_status'], 'error')
        self.assertEqual(len(rows), 1)

    @mock.patch('serial.Serial', spec=serial.Serial)
    def test_answers(self, serial_mock):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        kaco.Config.config['port'] = os.path.join(dir_path, 'test_ttyUSB*')

        # reset mock state
        self.serial_mock_in_waiting_index = 0
        self.serial_mock_return_index = 0

        instance = serial_mock.return_value
        instance.inWaiting.side_effect = self.serial_mock_in_waiting
        instance.readline.side_effect = self.serial_mock_return

        kaco.main_loop()

        rows = self.get_rows()
        self.remove_all_rows()

        # assume that if 3 answers and one status is written
        # everything was working
        self.assertEqual(len(rows), 4)

    def serial_mock_in_waiting(self):
        """return 1 or 0 based on number of calls"""
        # each inverter will be asked 2 questions
        # all together are 2*num of inverters
        should_return = [1, 0]*6

        index = self.serial_mock_in_waiting_index
        self.serial_mock_in_waiting_index += 1

        if index > len(should_return) - 1:
            return 0
        else:
            return should_return[index]

    def serial_mock_return(self):
        """return answer based on number of calls"""
        should_return = [
            '*010 4 585.9 10.17 5958 229.5 24.90 5720 36 17614 d 9600I',
            '2286 4184 42 581 8:46 11:04 11:04',
            '*020 4 585.9 10.17 5958 229.5 24.90 5720 36 17614 d 9600I',
            '2286 4184 42 581 8:46 11:04 11:04',
            '*030 4 585.9 10.17 5958 229.5 24.90 5720 36 17614 d 9600I',
            '2286 4184 42 581 8:46 11:04 11:04',
        ]

        index = self.serial_mock_return_index
        self.serial_mock_return_index += 1

        return should_return[index]
