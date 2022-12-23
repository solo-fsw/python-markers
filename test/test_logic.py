import unittest
import time
import marker_management
import pandas
from unittest.mock import patch, Mock, MagicMock

def mock_responses(responses, default_response=None):
  return lambda x=None: responses[x] if x in responses else default_response

        
class TestMarkerManagerInitialisation(unittest.TestCase):
    """
    Testclass for testing MarkerManager.__init__()
    
    """

    device_type = marker_management.FAKE_DEVICE
        
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
    
    """

    device_type = marker_management.FAKE_DEVICE

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
    
    """

    device_type = marker_management.FAKE_DEVICE

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
    
    """

    device_type = marker_management.FAKE_DEVICE

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

class TestGenMarkerTable(unittest.TestCase):
    """
    Testclass for testing MarkerManager.gen_marker_table()
    
    """

    device_type = marker_management.FAKE_DEVICE

    def test_logging_marker_table_one(self):
        device = marker_management.MarkerManager(TestGenMarkerTable.device_type, crash_on_marker_errors = True)

        device.set_value(100)
        time.sleep(1)
        device.set_value(0)
        marker_df, _, _ = device.gen_marker_table()

        self.assertEqual(len(marker_df), 1)
        self.assertEqual(marker_df.at[0, 'value'], 100)
        self.assertEqual(marker_df.at[0, 'occurrence'], 1)
        self.assertGreaterEqual(marker_df.at[0, 'duration_ms'], 999.9)

    def test_logging_marker_table_more(self):
        device = marker_management.MarkerManager(TestGenMarkerTable.device_type, crash_on_marker_errors = True)

        device.set_value(100)
        time.sleep(1)
        device.set_value(0)
        time.sleep(1)
        device.set_value(222)
        time.sleep(2)
        device.set_value(100)
        marker_df, _, _ = device.gen_marker_table()
        
        self.assertEqual(len(marker_df), 3)
        self.assertEqual(marker_df.at[2, 'duration_ms'], float('inf'))
        self.assertEqual(marker_df.at[2, 'end_time_s'], float('inf'))
        self.assertEqual(marker_df.at[2, 'occurrence'], 2)

    def test_summary_table(self):
        device = marker_management.MarkerManager(TestGenMarkerTable.device_type, crash_on_marker_errors = True)

        device.set_value(100)
        time.sleep(1)
        device.set_value(0)
        time.sleep(1)
        device.set_value(222)
        time.sleep(2)
        device.set_value(100)
        _, summary_df, _ = device.gen_marker_table()

        self.assertEqual(len(summary_df), 2)
        self.assertEqual(summary_df.at[1, 'value'], 222)
        self.assertEqual(summary_df.at[1, 'occurrence'], 1)
        self.assertEqual(summary_df.at[2, 'value'], 100)
        self.assertEqual(summary_df.at[2, 'occurrence'], 2)

    def test_error_table_empty(self):
        device = marker_management.MarkerManager(TestGenMarkerTable.device_type, crash_on_marker_errors = False)

        device.set_value(100)
        time.sleep(1)
        device.set_value(0)
        _, _, error_df = device.gen_marker_table()

        self.assertEqual(len(error_df), 0)

    def test_error_table_filled(self):
        device = marker_management.MarkerManager(TestGenMarkerTable.device_type, crash_on_marker_errors = False)

        device.set_value(100)
        device.set_value(0)
        device.set_value(200)
        time.sleep(1)
        device.set_value(200)
        _, _, error_df = device.gen_marker_table()

        self.assertEqual(len(error_df), 3)
        self.assertEqual(error_df.error[0], "Marker with value 0 was sent within 10 ms after previous marker with value 100")
        self.assertEqual(error_df.error[1], "Marker with value 200 was sent within 10 ms after previous marker with value 0")
        self.assertEqual(error_df.error[2], "Marker with value 200 is sent twice in a row.")

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
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties = Mock(return_value={"Device": "UsbParMarker", "Serialno": ""})
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="104")  # TODO: Ensure UsbParmMarker is not connected while running this test
        self.assertEqual(str(e.exception.id), "NoSerialMatch")

    def test_multiple_connections(self):
        # TODO: Never raises an error? Never even reaches if connected?
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1"), ("B", "2b", "USB VID:PID=2341:2")]
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties.side_effect = [{"Device": "UsbParMarker", "Serialno": "1"}, {"Device": "UsbParMarker", "Serialno": "2"}]
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="")  # TODO: Ensure UsbParmMarker is not connected while running this test
        self.assertEqual(str(e.exception.id), "MultipleConnections")

    def test_connection_error(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1"), ("A", "1a", "USB VID:PID=2341:1")]
                mock_serial_class = MagicMock()
                mock_serial_class._close.side_effect = ["No error first time around", Exception("This is an error"), "This is not"]
                mock_serial_class.device_properties.side_effect = [{"Device": "UsbParMarker", "Serialno": "1"}, {"Device": "UsbParMarker", "Serialno": "2"}]
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="")
        self.assertEqual(str(e.exception.id), "NoConnection")

    def test_correct_information_mock(self):
        with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1")]
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties.return_value = {"Version": "0001", "Serialno": "1", "Device": "UsbParMarker"}
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="1")
        correct = {"device": {"Version": "0001", "Serialno": "1", "Device": "UsbParMarker"}, "com_port": "A"}
        self.assertEqual(answer, correct)

    def test_correct_information_fake(self):
        answer = marker_management.find_device(device_type="", fallback_to_fake=True)
        correct = {"device": {"Version": "0000000", "Serialno": "0000000", "Device": marker_management.FAKE_DEVICE}, "com_port": marker_management.FAKE_ADDRESS}
        self.assertEqual(answer, correct)

# info[device] = current.device)properties()
# info[com_port] = port

if __name__ == '__main__':
    unittest.main()
    # TODO: Test if correct input works without errors and returns correct values!
    # TODO: Test general errors