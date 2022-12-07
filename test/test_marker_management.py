import unittest
import marker_management

class TestTestsFunctional(unittest.TestCase):

    def test_tests(self):
        self.assertEqual(1, 1)
        
class TestMarkerManagerInitialisation(unittest.TestCase):
    
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and adress) is added twice.

        """
        # Specify device information
        device_type = "Eva"
        adress = 12345
        # Create first class
        device1 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create duplicate class
            device2 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Check if the correct error was raised
        self.assertEquals(str(e.id), "DuplicateDevice")
        
    def test_unsupported_device(self):
        """
        Tests if the correct error is raised when the device type is not supported (currently: available_devices = {'UsbParMarker', 'Eva', FAKE_DEVICE}).
        
        """
        # Specify device information
        device_type = "Eva"
        adress = 12345
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create unsupported device
            device1 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Check if the correct error was raised
        self.assertEquals(str(e.id), "UnsupportedDevice")
        
    def test_

if __name__ == '__main__':
    unittest.main()