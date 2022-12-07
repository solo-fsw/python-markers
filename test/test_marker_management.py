import unittest
import marker_management

class TestTestsFunctional(unittest.TestCase):
    """
    Temporary testclass for ensuring the tests are functional and can be found by the automatic testing github action
    
    """
    
    def test_tests(self):
        self.assertEqual(1, 1)
        
class TestMarkerManagerInitialisation(unittest.TestCase):
    """
    Testclass for testing the checks in MarkerManager.__init__()
    
    """
    # Tests fail because of wrong adress???
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and adress) is added twice.

        """
        # TODO: MarkerManagerError not raised?
        # Specify device information
        device_type = "Eva"
        adress = "12345"
        # Create first class
        device1 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create duplicate class
            device2 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "DuplicateDevice")
        
    def test_unsupported_device(self):
        """
        Tests if the correct error is raised when the device type is not supported (currently: available_devices = {'UsbParMarker', 'Eva', FAKE_DEVICE}).
        
        """
        # Specify device information
        device_type = "NONEXISTANT"
        adress = "12345"
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create unsupported device
            device1 = marker_management.MarkerManager(device_type, device_adress = adress)
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "UnsupportedDevice")
        
    def test_device_adress_type(self):
        """
        Tests if the correct error is raised when the device_adress parameter has an incorrect datatype (anything but string).

        """
        # TODO: MarkerManagerError not raised?
        # Specify device information
        device_type = "Eva"
        for adress in [112, 0.5]:  # Add list, tuple, range?
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect adress type
                device1 = marker_management.MarkerManager(device_type, device_adress = adress)
            self.assertEqual(str(e.exception.id), "DeviceAdressString")

    def test_crash_on_marker_errors_type(self):
        """
        Tests if the correct error is raised when the crash_on_marker_errors parameter has an incorrect datatype (anything but boolean).

        """
        device_type = "Eva"
        adress = "12345"
        for crash in ["Nope", 0, 1.0]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect crash_on_marker_errors type
                device1 = marker_management.MarkerManager(device_type, device_adress = adress, crash_on_marker_errors = crash)
            self.assertEqual(str(e.exception.id), "CrashOnMarkerErrorsBoolean")
            
    def test_time_function_type(self):
        """
        Tests if the correct error is raised when the time_function_ms parameter is not callable (a function).

        """
        device_type = "Eva"
        adress = "12345"
        for timeing in ["not_a_function", 4, 1.0]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect time_function_ms
                device1 = marker_management.MarkerManager(device_type, adress, time_function_ms = timeing)
            self.assertEqual(str(e.exception.id), "TimeFunctionMsCallable")

class TestSetValue(unittest.TestCase):
    """
    Testclass for testing the checks in MarkerManager.set_value()
    
    Warning: device needs to be coupled and correct type needs to be entered for this test!
    
    """
    def test_marker_value_whole_number(self):
        device = marker_management.MarkerManager("UsbParMarker")  # Incorrect adress!
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(66.6)
        self.assertEqual(str(e.exception.id), "ValueWholeNumber")
    
if __name__ == '__main__':
    unittest.main()