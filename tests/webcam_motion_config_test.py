# Webcam Motion Detector Configuration tests

import difflib
import os
import shutil
import tempfile
import unittest
from datetime import datetime, time

import webcam_motion_config as wmc
from webcam_motion_config import Times, WebcamMotionConfig

PATH_1: str = 'webcam_motion_detection_1.json'
PATH_2: str = 'webcam_motion_detection_2.json'


class TestConfig(unittest.TestCase):
    temp_file_1 = None
    temp_file_2 = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print('=' * 80)
        print('Test case: ' + cls.__name__)
        print('Setup test case...')
        temp_dir: str = tempfile.gettempdir()
        cls.temp_file_1 = temp_dir + os.sep + 'TestConfig_' + str(datetime.now().timestamp())
        print('Copying file ' + PATH_1 + ' to ' + cls.temp_file_1)
        shutil.copy(PATH_1, cls.temp_file_1)
        cls.temp_file_2 = temp_dir + os.sep + 'TestConfig_' + str(datetime.now().timestamp())
        print('Copying file ' + PATH_2 + ' to ' + cls.temp_file_2)
        shutil.copy(PATH_2, cls.temp_file_2)

    @classmethod
    def tearDownClass(cls):
        print('-' * 80)
        print('Cleanup test case...')
        if cls.temp_file_1:
            print('Deleting file ' + cls.temp_file_1)
            os.unlink(cls.temp_file_1)
        if cls.temp_file_2:
            print('Deleting file ' + cls.temp_file_2)
            os.unlink(cls.temp_file_2)
        print('=' * 80)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        print('-' * 80)

    def tearDown(self):
        super().tearDown()

    def test_default(self):
        config: WebcamMotionConfig = WebcamMotionConfig()
        self.assertEqual(wmc.DEFAULT_USER, config.get_user(), 'Wrong user')
        self.assertEqual(wmc.DEFAULT_PASSWORD, config.get_password(), 'Wrong user password')
        self.assertEqual(wmc.DEFAULT_NOTIFICATION_DELAY, config.get_notification_delay(), 'Wrong notification delay')
        self.assertEqual(wmc.DEFAULT_VIDEO_DEVICE_NAME, config.get_video_device_name(), 'Wrong video device name')
        self.assertEqual(wmc.DEFAULT_VIDEO_DEVICE_ADDRESS, config.get_video_device_address(), 'Wrong video device address')
        self.assertEqual(False, config.is_graphical(), 'Wrong graphical flag')
        self.assertEqual(False, config.is_test(), 'Wrong test flag')
        self.assertEqual(wmc.DEFAULT_TEMP_DIR, config.get_temp_dir(), 'Wrong temporary directory')
        self.assertEqual(wmc.DEFAULT_HTTP_PORT, config.get_http_port(), 'Wrong HTTP port')
        self.assertEqual(wmc.DEFAULT_LOG_LEVEL, config.get_log_level(), 'Wrong log level')
        self.assertIsNotNone(config.get_mac_addresses(), 'Wrong MAC addresses object')
        self.assertEqual(0, len(config.get_mac_addresses()), 'Wrong MAC addresses count')
        self.assertIsNotNone(config.get_activation_periods(), 'Wrong activation periods object')
        self.assertEqual(7, len(config.get_activation_periods()), 'Wrong activation periods count')
        for day in [0, 1, 2, 3, 4, 5, 6]:
            times: Times = config.get_activation_periods().get(day)
            self.assertEqual(2, len(times), 'Wrong times count')
            self.assertEqual(time(0, 0), times[0], 'Wrong time')
            self.assertEqual(time(23, 59), times[1], 'Wrong time')
        self.assertIsNotNone(config.get_zone(), 'Wrong zone object')
        self.assertEqual(-1, config.get_zone().x1, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().y1, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().x2, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().y2, 'Wrong zone value')

    def test_read(self):
        config: WebcamMotionConfig = WebcamMotionConfig()
        config.read(TestConfig.temp_file_1)
        self.assertEqual('admin', config.get_user(), 'Wrong user')
        self.assertEqual('secret', config.get_password(), 'Wrong user password')
        self.assertEqual(5, config.get_notification_delay(), 'Wrong notification delay')
        self.assertEqual('Camera 1', config.get_video_device_name(), 'Wrong video device name')
        self.assertEqual('0', config.get_video_device_address(), 'Wrong video device address')
        self.assertEqual(True, config.is_graphical(), 'Wrong graphical flag')
        self.assertEqual(True, config.is_test(), 'Wrong test flag')
        self.assertEqual('/tmp/webcam_motion_detection', config.get_temp_dir(), 'Wrong temporary directory')
        self.assertEqual(8080, config.get_http_port(), 'Wrong HTTP port')
        self.assertEqual('DEBUG', config.get_log_level(), 'Wrong log level')
        self.assertIsNotNone(config.get_mac_addresses(), 'Wrong MAC addresses object')
        self.assertTrue('40:40:A7:92:F5:FF' in config.get_mac_addresses(), 'MAC addresses not set')
        self.assertEqual(2, len(config.get_mac_addresses()), 'Wrong MAC addresses count')
        self.assertIsNotNone(config.get_activation_periods(), 'Wrong activation periods object')
        self.assertEqual(7, len(config.get_activation_periods()), 'Wrong activation periods count')
        for day in [0, 1, 2, 3, 4, 5, 6]:
            times: Times = config.get_activation_periods().get(day)
            self.assertEqual(2, len(times), 'Wrong times count')
            self.assertEqual(time(8, 30 + day), times[0], 'Wrong time')
            self.assertEqual(time(23, 30 + day), times[1], 'Wrong time')
        self.assertIsNotNone(config.get_zone(), 'Wrong zone object')
        self.assertEqual(-1, config.get_zone().x1, 'Wrong zone value')
        self.assertEqual(-2, config.get_zone().y1, 'Wrong zone value')
        self.assertEqual(-3, config.get_zone().x2, 'Wrong zone value')
        self.assertEqual(-4, config.get_zone().y2, 'Wrong zone value')

    def test_write(self):
        config: WebcamMotionConfig = WebcamMotionConfig()
        temp_file_2: str = TestConfig.temp_file_1 + '_write'
        config.read(TestConfig.temp_file_1)
        try:
            config.write(temp_file_2)
            # print('Source file: ' + TestConfig.temp_file_1 + '\n')
            with open(TestConfig.temp_file_1) as file1:
                # print(file1.read())
                # print('Written file: ' + temp_file_2 + '\n')
                with open(temp_file_2) as file2:
                    # print(file2.read())
                    diff = difflib.ndiff(file1.readlines(), file2.readlines())
                    delta = ''.join(x for x in diff if x.startswith('+ ') or x.startswith('- '))
                    print('Delta:\n' + delta)
                    self.assertTrue(len(delta) == 0, 'Wrong file content')
        finally:
            if os.path.exists(temp_file_2):
                os.unlink(temp_file_2)

    def test_empty(self):
        print('test_empty')
        config: WebcamMotionConfig = WebcamMotionConfig()
        config.read(TestConfig.temp_file_2)
        self.assertEqual(wmc.DEFAULT_USER, config.get_user(), 'Wrong user')
        self.assertEqual(wmc.DEFAULT_PASSWORD, config.get_password(), 'Wrong user password')
        self.assertEqual(wmc.DEFAULT_NOTIFICATION_DELAY, config.get_notification_delay(), 'Wrong notification delay')
        self.assertEqual(wmc.DEFAULT_VIDEO_DEVICE_NAME, config.get_video_device_name(), 'Wrong video device name')
        self.assertEqual(wmc.DEFAULT_VIDEO_DEVICE_ADDRESS, config.get_video_device_address(), 'Wrong video device address')
        self.assertEqual(False, config.is_graphical(), 'Wrong graphical flag')
        self.assertEqual(False, config.is_test(), 'Wrong test flag')
        self.assertEqual(wmc.DEFAULT_TEMP_DIR, config.get_temp_dir(), 'Wrong temporary directory')
        self.assertEqual(wmc.DEFAULT_HTTP_PORT, config.get_http_port(), 'Wrong HTTP port')
        self.assertEqual(wmc.DEFAULT_LOG_LEVEL, config.get_log_level(), 'Wrong log level')
        self.assertIsNotNone(config.get_mac_addresses(), 'Wrong MAC addresses object')
        self.assertEqual(0, len(config.get_mac_addresses()), 'Wrong MAC addresses count')
        self.assertIsNotNone(config.get_activation_periods(), 'Wrong activation periods object')
        self.assertEqual(7, len(config.get_activation_periods()), 'Wrong activation periods count')
        for day in [0, 1, 2, 3, 4, 5, 6]:
            times: Times = config.get_activation_periods().get(day)
            self.assertEqual(2, len(times), 'Wrong times count')
            self.assertEqual(time(0, 0), times[0], 'Wrong time')
            self.assertEqual(time(23, 59), times[1], 'Wrong time')
        self.assertIsNotNone(config.get_zone(), 'Wrong zone object')
        self.assertEqual(-1, config.get_zone().x1, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().y1, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().x2, 'Wrong zone value')
        self.assertEqual(-1, config.get_zone().y2, 'Wrong zone value')

    def test_invalid(self):
        print('test_invalid')
        config: WebcamMotionConfig = WebcamMotionConfig()
        with self.assertRaises(FileNotFoundError):
            config.read(TestConfig.temp_file_1 + '_invalid')


if __name__ == '__main__':
    unittest.main()
