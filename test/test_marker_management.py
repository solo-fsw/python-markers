import unittest
import marker_management

class TestTestsFunctional(unittest.TestCase):

    def test_tests(self):
        self.assertEqual(1, 1)
        
class TestMarkerManagerInitialisation(unittest.TestCase):
    
    def test_duplicate_device(self):
        """
        Tests if the correct error is raised when the same device (identical type and adress) is added twice.

        Returns
        -------
        None.

        """
        # Specify adress
        adress = 12345
        # Create first class
        init1 = marker_management.MarkerManager("Eva", device_adress=adress)
        # Catch the error
        with self.assertRaises(marker_management.MarkerManagerError) as e:
            init2 = marker_management.MarkerManager("Eva", device_adress= adress)
        self.assertEquals(str(e.id), "DuplicateDevice")

if __name__ == '__main__':
    unittest.main()