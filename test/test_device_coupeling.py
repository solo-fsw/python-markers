import unittest
import time
import marker_management
from unittest.mock import MagicMock, Mock, patch

class TestDeviceCoupeling(unittest.TestCase):
    """
    Tests functions and checks that need to have a device coupled to the computer to be testable.
    
    """
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and adress) is added twice.

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

if __name__ == '__main__':
    unittest.main()
    # TODO: add more tests (find_device)