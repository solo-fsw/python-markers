import unittest
import time
import marker_management

class TestTestsFunctional(unittest.TestCase):
    """
    Temporary testclass for ensuring the tests are functional and can be found by the automatic testing github action
    
    """
    
    def test_tests(self):
        self.assertEqual(1, 1)
        
class TestMarkerManagerInitialisation(unittest.TestCase):
    """
    Testclass for testing MarkerManager.__init__()
    
    """

    device_type = "FAKE DEVICE"
        
    def test_unsupported_device(self):
        """
        Tests if the correct error is raised when the device type is not supported (currently: available_devices = {'UsbParMarker', 'Eva', FAKE_DEVICE}).
        
        """
        # Specify device information
        device_type = "NONEXISTANT"
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create unsupported device
            device = marker_management.MarkerManager(device_type)
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "UnsupportedDevice")
        
    def test_device_adress_type(self):
        """
        Tests if the correct error is raised when the device_adress parameter has an incorrect datatype (anything but string).

        """
        # TODO: MarkerManagerError not raised?
        # Specify device information
        for adress in [112, 0.5]:  # Add list, tuple, range?
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect adress type
                device = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type, adress)
            self.assertEqual(str(e.exception.id), "DeviceAdressString")

    def test_crash_on_marker_errors_type(self):
        """
        Tests if the correct error is raised when the crash_on_marker_errors parameter has an incorrect datatype (anything but boolean).

        """
        for crash in ["Nope", 0, 1.0]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect crash_on_marker_errors type
                device = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type, crash_on_marker_errors = crash)
            self.assertEqual(str(e.exception.id), "CrashOnMarkerErrorsBoolean")
            
    def test_time_function_type(self):
        """
        Tests if the correct error is raised when the time_function_ms parameter is not callable (a function).

        """
        for timeing in ["not_a_function", 4, 1.0]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect time_function_ms
                device1 = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type, time_function_ms = timeing)
            self.assertEqual(str(e.exception.id), "TimeFunctionMsCallable")

class TestSetValue(unittest.TestCase):
    """
    Testclass for testing MarkerManager.set_value()
    
    Warning: device needs to be coupled and correct type needs to be entered for this test!
    
    """

    device_type = "FAKE DEVICE"

    def test_marker_value_whole_number(self):
        """
        Tests if the correct error is raised if the marker_value is not the allowed type (int).

        """
        device = marker_management.MarkerManager(TestSetValue.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(66.6)
        self.assertEqual(str(e.exception.id), "ValueWholeNumber")

    def test_marker_value_range(self):
        """
        Tests if the correct error is raised if the marker_value is outside the allowed range (0 - 255).
        
        """
        device = marker_management.MarkerManager(TestSetValue.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(-1)
        self.assertEqual(str(e.exception.id), "ValueOutOfRange")

        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(256)
        self.assertEqual(str(e.exception.id), "ValueOutOfRange")

    def test_marker_value_sent_twice(self):
        """
        Tests if the correct error is raised if the same value is sent twice

        """
        device = marker_management.MarkerManager(TestSetValue.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(100)
            time.sleep(2)
            device.set_value(100)
        self.assertEqual(str(e.exception.id), "MarkerSentTwice")

    def test_concurrent_marker_threshold(self):
        """
        Tests if the correct error is raised if the time between sending two markers is less than concurrent_marker_threshold (standard value: 10ms). 

        """
        device = marker_management.MarkerManager(TestSetValue.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_value(100)
            device.set_value(150)
        self.assertEqual(str(e.exception.id), "ConcurrentMarkerThreshold")
    # TODO: Test device_interface._set_value by closing the connection in the upload?

    # TODO: Test if no error is returned on toggeling is_fatal!

    # TODO: Test correct appending to set_value_list

class TestSetBits(unittest.TestCase):
    """
    Testclass for testing MarkerManager.set_bits()
    
    Warning: device needs to be coupled and correct type needs to be entered for this test!
    
    """

    device_type = "FAKE DEVICE"

    def test_bits_correct_length_and_type(self):
        """
        Tests if the correct error is raised if the bits are too long, too short (not lenght 8), or not the correct datatype (only string allowed).
        
        """
        device = marker_management.MarkerManager(TestSetBits.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bits('0000000011')
        self.assertEqual(str(e.exception.id), "BitTypeLength")

        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bits('00001')
        self.assertEqual(str(e.exception.id), "BitTypeLength")

        for bits in [11, 0.5]:
            with self.assertRaises(marker_management.MarkerError) as e:
                device.set_bits(bits)
            self.assertEqual(str(e.exception.id), "BitTypeLength")

    def test_bit_0_1(self):
        """
        Tests if the correct error is raised if the bits contain other values than zeros and ones.

        """
        device = marker_management.MarkerManager(TestSetBits.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bits("10123010")
        self.assertEqual(str(e.exception.id), "BitElements")

class TestSetBit(unittest.TestCase):
    """
    Testclass for testing MarkerManager.set_bit()
    
    Warning: device needs to be coupled and correct type needs to be entered for this test!
    
    """

    device_type = "FAKE DEVICE"

    def test_bit_index(self):
        device = marker_management.MarkerManager(TestSetBit.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bit(-1, "on")
        self.assertEqual(str(e.exception.id), "BitTypeRange")

        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bit(0.7, "on")
        self.assertEqual(str(e.exception.id), "BitTypeRange")

    def test_bit_state(self):
        device = marker_management.MarkerManager(TestSetBit.device_type)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bit(4, "zero please")
        self.assertEqual(str(e.exception.id), "BitState")

# TODO: Test marker logging


if __name__ == '__main__':
    unittest.main()
    # TODO: Test if correct input works without errors and returns correct values!
    # TODO: Test general errors