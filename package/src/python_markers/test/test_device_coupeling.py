import unittest
import time
from python_markers import marker_management
from unittest.mock import MagicMock, Mock, patch

class TestDeviceCoupeling(unittest.TestCase):
    """
    Tests functions and checks that need to have a device coupled to the computer to be testable.
    
    """
    def test_tests(self):
        self.assertEqual(1, 1)

    # def test_find_device_finds_hardware(self):
        # """
        # UsbParMarker connected to laptops left usb port. Information:
        #     device_type: UsbParMarker
        #     port: COM3
        #     desc: USB Serial Device (COM3)
        #     hwid: VID:PID=2341:8036 SER=5&239973E5&0&6 LOCATION=1-6:x.0

        # """
        # answer = marker_management.find_device()
        # self.assertEqual(answer, "test")

if __name__ == '__main__':
    unittest.main()
    # TODO: add tests that require hardware to be connected