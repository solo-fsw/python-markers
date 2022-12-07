import unittest
import time
import marker_management

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

if __name__ == '__main__':
    unittest.main()
    # TODO: add more tests (find_device)