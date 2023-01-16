import unittest
import time
import marker_management
import pandas
from unittest.mock import patch, Mock, MagicMock


def mock_responses(responses, default_response=None):
  return lambda x=None: responses[x] if x in responses else default_response

class TestDuplicateDevice(unittest.TestCase):
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and address) is added twice.

        """

        device_type = "UsbParMarker"
        mock_instance_class = MagicMock()
        mock_instance_class.device_properties.return_value = {"Device": device_type}
        mock_instance_class.device_address.return_value = "123"
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            with patch("marker_management.UsbParMarker", return_value=mock_instance_class) as mock_instance:
                device1 = marker_management.MarkerManager(device_type, device_address="123")
                # Create duplicate class
                device2 = marker_management.MarkerManager(device_type, device_address="123")
            # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "DuplicateDevice")

        
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
        device_type = "nonexistent"
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            # Create unsupported device
            device = marker_management.MarkerManager(device_type)
        # Check if the correct error was raised
        self.assertEqual(str(e.exception.id), "UnsupportedDevice")
        
    def test_device_address_type(self):
        """
        Tests if the correct error is raised when the device_address parameter has an incorrect datatype (anything but string).

        """
        # Specify device information
        for address in [112]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect address type
                device = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type, address)
            self.assertEqual(str(e.exception.id), "DeviceAddressString")

    def test_crash_on_marker_errors_type(self):
        """
        Tests if the correct error is raised when the crash_on_marker_errors parameter has an incorrect datatype (anything but boolean).

        """         
        for crash_var in ["Nope", 0, 1.0]:
            # Catch the error
            with self.assertRaises(marker_management.MarkerManagerError) as e:
                # Create class with incorrect crash_on_marker_errors type
                device = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type, crash_on_marker_errors = crash_var)
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

    def test_correct_marker_manager(self):
        device = marker_management.MarkerManager(TestMarkerManagerInitialisation.device_type)
        self.assertIsInstance(device, marker_management.MarkerManager)

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

    def test_is_fatal(self):
        """
        Tests if the nonfatal errors are supressed if crash_on_marker_errors = False

        """
        device = marker_management.MarkerManager(TestSetValue.device_type, crash_on_marker_errors=False)
        # Concurrent marker threshold
        device.set_value(100)
        device.set_value(150)
        time.sleep(1)
        # Value sent twice
        device.set_value(100)
        time.sleep(2)
        device.set_value(100)

    def test_set_value_list(self):
        device = marker_management.MarkerManager(TestSetValue.device_type, crash_on_marker_errors=False)
        device.set_value(100)
        device.set_value(150)
        device.set_value(100)
        device.set_value(200)
        answer = [device.set_value_list[x]["value"] for x in range(len(list(device.set_value_list)))]
        correct = [0, 100, 150, 100, 200]
        self.assertEqual(answer, correct)

    def test_set_value_correct(self):
        device = marker_management.MarkerManager(TestSetValue.device_type)
        device.set_value(100)
        time.sleep(1)
        device.set_value(0)
        time.sleep(1)
        for i in range(10):
            device.set_value(35)
            time.sleep(1)
            device.set_value(0)
            time.sleep(1)

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

    def test_set_bits_correct(self):
        device = marker_management.MarkerManager(TestSetBits.device_type, crash_on_marker_errors=True)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bits('00000001')
            time.sleep(1)
            device.set_value(1)
        self.assertEqual(str(e.exception.id), "MarkerSentTwice")

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

    def test_set_bit_correct(self):
        device = marker_management.MarkerManager(TestSetBit.device_type, crash_on_marker_errors=True)
        with self.assertRaises(marker_management.MarkerError) as e:
            device.set_bit(7, 'on')
            time.sleep(1)
            device.set_value(1)
        self.assertEqual(str(e.exception.id), "MarkerSentTwice")

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
            answer = marker_management.find_device(device_type = "NONEXISTENT")
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
                answer = marker_management.find_device(device_type="UsbParMarker")
        self.assertEqual(str(e.exception.id), "NoDeviceMatch")

    def test_no_serial_match(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1")]
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties = {"Device": "UsbParMarker", "Serialno": "1"}
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="104")
        self.assertEqual(str(e.exception.id), "NoDeviceMatch")

    def test_multiple_connections(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1"), ("B", "2b", "USB VID:PID=2341:2")]
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties = {"Device": "UsbParMarker", "Serialno": "1"}
                mock_serial_class._close.return_value = None
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="1")
        self.assertEqual(str(e.exception.id), "MultipleConnections")

    def test_connection_error(self):
        with self.assertRaises(marker_management.FindDeviceError) as e:
            with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1"), ("A", "1a", "USB VID:PID=2341:1")]
                mock_serial_class = MagicMock()
                mock_serial_class._close.side_effect = ["No error first time around", Exception("This is an error"), "This is not"]
                mock_serial_class.device_properties = {"Device": "UsbParMarker", "Serialno": "1"}
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="")
        self.assertEqual(str(e.exception.id), "NoConnection")

    def test_correct_information_mock(self):
        with patch("marker_management.comports") as mock_comports:
                mock_comports.return_value = [("A", "1a", "USB VID:PID=2341:1")]
                mock_serial_class = MagicMock()
                mock_serial_class.device_properties = {"Version": "0001", "Serialno": "1", "Device": "UsbParMarker"}
                with patch("marker_management.SerialDevice", return_value=mock_serial_class) as mock_serial:
                    answer = marker_management.find_device(device_type="UsbParMarker", serial_no="1")
        correct = {"device": {"Version": "0001", "Serialno": "1", "Device": "UsbParMarker"}, "com_port": "A"}
        self.assertEqual(answer, correct)

    def test_correct_information_fake(self):
        answer = marker_management.find_device(device_type="", fallback_to_fake=True)
        correct = {"device": {"Version": "0000000", "Serialno": "0000000", "Device": marker_management.FAKE_DEVICE}, "com_port": marker_management.FAKE_ADDRESS}
        self.assertEqual(answer, correct)

class TestSerialDevice(unittest.TestCase):

    def test_empty_properties(self):
        with self.assertRaises(marker_management.SerialError) as e:
            with patch("marker_management.SerialDevice.command_mode") as mock_command_mode:
                with patch("marker_management.SerialDevice.get_info") as mock_get_info:
                    mock_get_info.return_value = ""
                    device = marker_management.SerialDevice("104")
        self.assertEqual(str(e.exception.id), "NoResponse")

    def test_serialno_missing(self):
        with self.assertRaises(marker_management.SerialError) as e:
            with patch("marker_management.SerialDevice.command_mode") as mock_command_mode:
                with patch("marker_management.SerialDevice.get_info") as mock_get_info:
                    mock_get_info.return_value = "not the correct format"
                    device = marker_management.SerialDevice("104")
        self.assertEqual(str(e.exception.id), "NoSerialNo")

    def test_open_serial_device(self):
        with self.assertRaises(marker_management.SerialError) as e:
            device = marker_management.SerialDevice("104")
        self.assertEqual(str(e.exception.id), "NoSerialDeviceMade")

    def test_wrong_baudrate(self):
        with self.assertRaises(marker_management.SerialError) as e:
            mock_serial_device = MagicMock()
            mock_serial_device.baudrate = 20
            with patch("marker_management.serial.Serial", return_value=mock_serial_device) as mock_serial:
                device = marker_management.SerialDevice("104")
        self.assertEqual(str(e.exception.id), "BaudrateNotCommandmode")

    def test_serial_device_closed(self):
       with self.assertRaises(marker_management.SerialError) as e:
           mock_serial_device = MagicMock()
           mock_serial_device.baudrate = 4800
           mock_serial_device.is_open = False
           with patch("marker_management.serial.Serial", return_value=mock_serial_device) as mock_serial:
                device = marker_management.SerialDevice("104")
       self.assertEqual(str(e.exception.id), "SerialDeviceClosed")

    def test_command_wrong_type(self):
        with self.assertRaises(marker_management.SerialError) as e:
           mock_serial_device = MagicMock()
           mock_serial_device.baudrate = 4800
           mock_serial_device.is_open = True
           mock_serial_device.readline.return_value = 'testsetset'.encode()
           with patch("marker_management.serial.Serial", return_value=mock_serial_device) as mock_serial:
             with patch("marker_management.SerialDevice.get_info") as mock_get_info:
                    mock_get_info.return_value = ["Serialno"]
                    device = marker_management.SerialDevice("104")
                    device.send_command(12)
        self.assertEqual(str(e.exception.id), "CommandType")

    def test_correct_serial_device(self):
        mock_serial_device = MagicMock()
        mock_serial_device.baudrate = 4800
        mock_serial_device.is_open = True
        mock_serial_device.readline.return_value = 'testsetset'.encode()
        with patch("marker_management.serial.Serial", return_value=mock_serial_device) as mock_serial:
            with patch("marker_management.SerialDevice.get_info") as mock_get_info:
                mock_get_info.return_value = ["Serialno"]
                device = marker_management.SerialDevice("104")


if __name__ == '__main__':
    unittest.main()