# Webcam Motion Detector tests

import datetime
import filecmp
import logging
import os
import shutil
import sys
import tempfile
import time
import unittest

from drivers.webcam_mock_driver import WebcamMockDriver
from webcam_motion_config import WebcamMotionConfig
from webcam_motion_detector import WebcamMotionDetector

PATH_1: str = 'webcam_motion_detection_1.jpg'
PATH_2: str = 'webcam_motion_detection_2.jpg'


class TestDetector(unittest.TestCase):
    config: WebcamMotionConfig = None
    driver: WebcamMockDriver = None
    logger: logging.Logger = None

    @classmethod
    def setUpClass(cls):
        print('=' * 80)
        print('Test case: ' + cls.__name__)
        print('Setup test case...')
        cls.config: WebcamMotionConfig = WebcamMotionConfig()
        cls.driver: WebcamMockDriver = WebcamMockDriver('0')
        cls.logger: logging.Logger = logging.getLogger("Webcam HTTP server")
        cls.logger.setLevel(logging.INFO)
        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler: logging.Handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        cls.logger.addHandler(console_handler)
        cls.config.set_test(True)
        cls.config.set_smtp_from('nobody@domain.com')
        cls.config.set_smtp_to('nobody@domain.com')
        cls.config.set_smtp_server('smtp.domain.com')

    @classmethod
    def tearDownClass(cls):
        print('-' * 80)
        print('Cleanup test case...')
        print('=' * 80)

    def setUp(self):
        print('-' * 80)

    def test_nothing_detected(self):
        print('test_nothing_detected')
        detector : WebcamMotionDetector = WebcamMotionDetector(TestDetector.logger, TestDetector.config, TestDetector.driver)
        detector.start()
        time.sleep(4)
        detector.stop()

    def test_nothing_detected_with_default_config(self):
        print('test_nothing_detected_with_default_config')
        detector : WebcamMotionDetector = WebcamMotionDetector(TestDetector.logger, TestDetector.config, TestDetector.driver)
        detector.start()
        time.sleep(4)
        detector.stop()

    def test_detected(self):
        print('test_detected')
        detector: WebcamMotionDetector = WebcamMotionDetector(TestDetector.logger, TestDetector.config, TestDetector.driver)
        detector.start()
        time.sleep(4)
        detector.stop()

    def test_detected_with_default_config(self):
        print('test_detected_with_default_config')
        detector: WebcamMotionDetector = WebcamMotionDetector(TestDetector.logger, TestDetector.config, TestDetector.driver)
        detector.start()
        time.sleep(4)
        detector.stop()


if __name__ == '__main__':
    unittest.main()