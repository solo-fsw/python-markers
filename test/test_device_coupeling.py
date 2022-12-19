import unittest
import time
import marker_management
from unittest.mock import patch

class TestDeviceCoupeling(unittest.TestCase):
    """
    Tests functions and checks that need to have a device coupled to the computer to be testable.
    
    """
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and adress) is added twice.

        """
        # TODO: MarkerManagerError not raised?
        # TODO: Device can not be fake!
        device_type = "UsbParMarker"
        # Create first class
        device1 = marker_management.MarkerManager(device_type)
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create duplicate class
            device2 = marker_management.MarkerManager(device_type)
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "DuplicateDevice")

class TestFindDevice(unittest.TestCase):

    def test_unsupported_device(self):
        # Catch the error
        with self.assertRaises(marker_management.FindDeviceError) as e:
            # Create unsupported device
            answer = marker_management.find_device(device_type = "NONEXISTANT")
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "UnsupportedDevice")

    def test_no_port_hit(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            answer = marker_management.find_device(com_port="DitIsGeenComPort")
        self.assertEqual(str(e.exception.id), "NoComMatch")

    def test_no_device_match(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1")]
                answer = marker_management.find_device(device_type="UsbParMarker")  # TODO: Ensure UsbParmMarker is not connected while running this test
        self.assertEqual(str(e.exception.id), "NoDeviceMatch")

    def test_no_serial_match(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1")]
                with patch("marker_management.SerialDevice") as mock_serial:
                    mock_serial.return_value = {"Device": "Matches", "Serialno": ""}
                    answer = marker_management.find_device(device_type="UsbParMarker")  # TODO: Ensure UsbParmMarker is not connected while running this test
        self.assertEqual(str(e.exception.id), "NoDeviceMatch")

if __name__ == '__main__':
    unittest.main()
    # TODO: add more tests (find_device)