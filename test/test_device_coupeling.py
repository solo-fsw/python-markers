import unittest
import time
import marker_management
from unittest.mock import MagicMock, Mock, patch

class TestDeviceCoupeling(unittest.TestCase):
    """
    Tests functions and checks that need to have a device coupled to the computer to be testable.
    
    """
    def test_tests(self):
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()
    # TODO: add tests that require hardware to be connected