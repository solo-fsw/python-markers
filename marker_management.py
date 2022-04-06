"""Core Library for Sending Markers

This module contains code for sending markers using various devices available at the FSW.

Devices:
    UsbParMar
    LPT
    EVA


FOR DEV:

 > TRY TO THINK OF A BETTER NAME FOR "UsbParMar" and "EVA"!
 > Markers are defined here:
    https://physiodatatoolbox.leidenuniv.nl/docs/user-guide/epochs.html#markers
    https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/


 Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

from abc import ABC, abstractmethod
import utils.GS_timing as timing

# Address string indicating that the device is being faked/spoofed:
FAKE_ADDRESS = 'FAKE'

class MarkerManager:
    """Sends markers to a given device.

    An instance of this class is tied to a device, and sends controls it to send markers.

    Available devices:
        UsbParMar:
            This mode uses the "UsbParMar" gadget to send markers. The device_address
            param must be its COM address (e.g. COM3).
        LPT:
            This mode uses the printerport (aka LPT port) to send markers. The device_address
            param must be a string indicating its name (e.g. "LPT1"), or a string indicating its

    """
    


    def __init__(self, device_type, device_address, report_marker_errors = True, time_function_us = lambda : timing.micros()):
        """Builds the marker class, and the device interface class used to talk to the device."""


        # Note, add ability to forward KW arguments to the DeviceInterface constructor.

        # Throw error if arguments are incorrect, or if a class with same type and address already exists.

        # Instantiate the correct DeviceInterface subclass:
        self.device_interface = type(device_type, 
              (), 
              {"device_address": device_address
               })

        # Reset marker on init (the marker tracking table assumes that the device has no active markers after init):
        self._current_value = 0
        self.device_interface._set_value(0)

        # Log timestamp of creation (use GS_Timing microseconds):
        self._time_function_us = time_function_us
        self._start_time = time_function_us()

        self.marker_list = list()
        self.report_marker_errors = report_marker_errors
        self.concurrent_marker_threshold_ms = 10


        # In the future, add an optional Tkinter always-on-top GUI that shows the current marker value, the bit states,
        # the device props, etc, a table with the markers, etc.
        self.gui = None

    @property
    def device_type(self):
        """Returns the device type."""
        return type(self.device_interface).__name__


    def close(self, value):
        """Closes the connection to the device."""
        self.device_interface._close()


    def set_value(self, value):
        """Sets value."""

        # Throw marker errors if self.report_marker_errors is true:
        #   Double markers:
        #    If the value is not zero (zeros are not markers) and the value is equal to the current value,
        #    the same value is sent twice with no effect.
        #   Too concurrent markers:
        #    If a marker was sent less then concurrent_marker_threshold_ms after the previous, throw error.
        #    Don't count zeros.


        # Regardless of report_marker_errors, throw error is marker is outside of range (0 - 255).


        self.device_interface._set_value(value)
        self._current_value = value

        # Calculate the marker time relative to the self.start_time, and log the marker:
        marker_time = self._time_function_us()
        self.marker_list.append({'value': value, 'time': marker_time})


    
    def is_fake(self):
        return self.device_interface.is_fake()

    def send_marker_pulse(self, value, duration_ms = 100):
        """Sends a short marker pulse"""
        pass


    def set_bits(self, bits):
        """Generic function for toggling bits.

        E.g. markers.set_bits('00000001') sets all bits except the last to LOW.
        Use EVA endianess convention.

        """

        # Calculate the value from the bits, call set_value().
        value = 9999
        self.set_value(value)


    def set_bit(self, bit, state):
        """Toggle a single bit.

        Toggle a single bit, leave other bits intact. Use EVA bit numbering convention.

        """
        value = 9999
        self.set_value(value)


    def gen_marker_table(self):
        """Returns a table (e.g. dataframe) with a list of all markers:

        The table should have, in chronological order, the marker value, and its start and end time, duration.
        The end time and duration should be infinite if the current value is non-zero (the current marker has not yet ended).

        A table with the summaries of all markers should also be returned, it should have a list of all the unique values, and their how many times they were sent."""
        pass


    def print_marker_table(self):
        """Pretty prints the gen_marker_table data."""
        pass

    
    def save_marker_table(self):
        """Saves the gen_marker_table data as TSV file(s)."""
        pass


class DeviceInterface(ABC):
    """This defines the interface for connecting to a device.

    Device-type specific classes that manage the connection to a marker device
    must subclass this class and implement its abstract methods.

    Note, the subclass constructors must throw errors if the specified parameters cannot be resolved.
    E.g., no device with the specified address exist, or it it is not of the expected type.

    """
    
    @property
    @abstractmethod
    def device_address(self):
        """Returns the address of the device."""
        pass


    @property
    @abstractmethod
    def device_properties(self):
        """Returns the properties of the device (firmware version, name, etc.)."""

        # For props, use list with one elements per prop, with each element having the fields: name, label, value. 

        #  {"name" : "firmware_version", "label" : "Firmware version", "value": "0.4.1"}
        pass


    @abstractmethod
    def _set_value(self, value):
        """Sets the value of the marker device. The Markers.set_value should be user by users since it performs generic checks and logs the markers."""
        pass

    
    @abstractmethod
    def _close(self, value):
        """Closes the connection to the serial device, if necessary."""
        pass


    @property
    def is_fake(self):
        """Returns a bool indication if the device is faked."""
        return self.device_address == FAKE_ADDRESS


class UsbParMar(DeviceInterface):
    """Class for the UsbParMar.

    """

    def __init__(self, device_address):
        
        # Init serial device and configure if necessary.
        self.serial_device = 9999

        # Save attribs:
        self._device_address = device_address

        # Fetch and save device properties.
        self._device_properties = []
    

    def device_address(self):
        return self._device_address


    def device_properties(self):
        return self._device_properties

        
    def _set_value(self, value):
        """Sets the value of the usbParMar device."""
        pass
    

    def _close(self):
        """Closes the serial connection."""
        pass

    
    # Define device-specific methods here, and check the firmware version for compatibility.
    # For instance, as of a future UsbParMar version, the LEDs can be deactivated.
    # Also, as of a future UsbParMar version, a pattern can be specified.



class LPT(DeviceInterface):
    """Class for LPT markers.

     Note, throw error in __init__ if the specified address is not an LPT address.

    """

    # Etc.


# Below are helper functions:

def find_address(device_type, device_name = '', fallback_to_fake = False):
    """ Finds the address of the device.

    If LPT mode, return the address. Throw error if no or multiple LPT addresses are available.

    If UsbParMar mode, find the COM port. If a device_name was specified, check that it (probably a serial number) matches.
    Throw error if multiple COM candidates are available. Empty device name uses any.

    etc.

    However, if fallback_to_fake is true, don't throw error, just returns the address that toggles faking.  

    """

    # Note, use the UsbParMar class directly to connect to available COM devices and fetch their properties.

    address = ''
    return address
