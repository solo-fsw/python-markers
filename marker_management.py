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
import serial
import time
import json
import pandas

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

    def __init__(self, device_type, device_address, fallback_to_fake=False, report_marker_errors = True, time_function_us = lambda : timing.micros()):
        """Builds the marker class, and the device interface class used to talk to the device."""


        # Note, add ability to forward KW arguments to the DeviceInterface constructor.

        # Throw error if arguments are incorrect, or if a class with same type and address already exists.

        # Instantiate the correct DeviceInterface subclass:
        # self.device_interface = type(device_type, (), {"device_address": device_address})
        # print(self.device_interface)
        self.device_type = device_type

        # Above does not work, below does
        if self.device_type == 'UsbParMar':
            self.device_interface = UsbParMar(device_address, fallback_to_fake)
        elif self.device_type == 'EVA':
            self.device_interface = EVA(device_address, fallback_to_fake)

        # Reset marker on init (the marker tracking table assumes that the device has no active markers after init):
        self._current_value = 0
        self.device_interface._set_value(0)

        # Log timestamp of creation (use GS_Timing microseconds):
        self._time_function_us = time_function_us
        self._start_time = time_function_us()

        self.marker_list = list()
        self.fallback_to_fake = fallback_to_fake
        self.report_marker_errors = report_marker_errors
        self.concurrent_marker_threshold_ms = 10

        # In the future, add an optional Tkinter always-on-top GUI that shows the current marker value, the bit states,
        # the device props, etc, a table with the markers, etc.
        self.gui = None

    @property
    def device_properties(self):
        return self.device_interface.device_properties()

    def close(self):
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

        # Value should be int.

        # Regardless of report_marker_errors, throw error is marker is outside of range (0 - 255).

        self.device_interface._set_value(value)
        self._current_value = value

        # Calculate the marker time relative to the self.start_time, and log the marker:
        marker_time = self._time_function_us()
        self.marker_list.append({'value': value, 'start_time': marker_time})

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

        The table should have, in chronological order, the marker value, and its start and end time, duration and occurence.
        The end time and duration should be infinite if the current value is non-zero (the current marker has not yet ended).

        A table with the summaries of all markers should also be returned, it should have a list of all the unique values,
        and their how many times they were sent."""

        marker_data_frame = pandas.DataFrame(self.marker_list)
        marker_data_frame["end_time"] = marker_data_frame["start_time"].shift(-1)
        zero_index = marker_data_frame[marker_data_frame['value'] == 0].index
        marker_data_frame.drop(zero_index, inplace=True)
        marker_data_frame["duration"] = marker_data_frame["end_time"] - marker_data_frame["start_time"]
        print(marker_data_frame)
        summary = marker_data_frame['value'].value_counts()
        summary = summary.to_frame()
        summary.reset_index(inplace=True)
        summary = summary.rename(columns={'value': 'total_occurences','index': 'value'})
        print(summary)

        # todo: count occurences and put in marker_table


        # todo: if last value of end_time is nan, that means the current value has not been set to 0 and thus the value
        # is still ongoing, set to infinite
        # if marker_data_frame["end_time"].isnull().values.len():
        #

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
    def _close(self):
        """Closes the connection to the serial device, if necessary."""
        pass


    @property
    def is_fake(self):
        """Returns a bool indication if the device is faked."""
        return self.device_address == FAKE_ADDRESS


class UsbParMar(DeviceInterface):
    """Class for the UsbParMar.

    """

    def __init__(self, device_address, fallback_to_fake):

        # Save attribs:
        self._device_address = device_address
        self._fallback_to_fake = fallback_to_fake

        if not fallback_to_fake:

            # Create serial device.
            self.serial_device = serial.Serial()

            # Open device in command mode:
            self.command_mode()
            time.sleep(0.1)

            # Fetch and save device properties.
            properties = self.send_command('V')
            version = properties.get('Version')
            serialno = properties.get('Serialno')
            device = properties.get('Device')

            #  {"name" : "firmware_version", "label" : "Firmware version", "value": "0.4.1"}
            # Aren't regular key value pairs better?
            self._device_properties = [{"name": "firmware_version",
                                        "label": "Firmware version",
                                        "value": version},
                                       {"name": "serial_number",
                                        "label": "Serial number",
                                        "value": serialno},
                                       {"name": "device_name",
                                        "label": "Device_name",
                                        "value": device}]

            # Close device
            self.serial_device.close()
            time.sleep(0.1)

            # Open device in data mode:
            self.data_mode()
            time.sleep(0.1)

    def device_address(self):
        """Returns device address."""
        return self._device_address

    def device_properties(self):
        """Returns device properties."""
        return self._device_properties

    def _set_value(self, value):
        """Sets the value of the usbParMar device."""
        self.serial_device.write(bytearray([value]))

    def _close(self):
        """Closes the serial connection."""
        self.serial_device.close()

    def command_mode(self):
        """Opens serial device in command mode."""
        self.open_serial_device(4800)

    def data_mode(self):
        """Opens serial device in data mode."""
        self.open_serial_device(115200)

    def open_serial_device(self, baudrate):
        """Opens serial device with specified baudrate."""
        self.serial_device.port = self._device_address
        self.serial_device.baudrate = baudrate
        self.serial_device.bytesize = 8
        self.serial_device.parity = 'N'
        self.serial_device.stopbits = 1
        self.serial_device.timeout = 2
        self.serial_device.write_timeout = 0
        self.serial_device.open()

    def send_command(self, command):
        if not self.serial_device.baudrate == 4800:
            return 'ERROR, serial device not in commmand mode'
        if not self.serial_device.is_open:
            return 'ERROR, serial device is not open'
        if not type(command) == str:
            return 'ERROR, command should be a string'
        else:

            def is_json(json_string):
                try:
                    json_object = json.loads(json_string)
                except ValueError as e:
                    return False
                return True

            # Send command
            self.serial_device.flushInput()
            self.serial_device.write(command.encode())
            time.sleep(0.1)

            # Get reply
            data = self.serial_device.readline()
            decoded_data = data.decode('utf-8')

            # If reply is json string, decode it
            if is_json(decoded_data):
                decoded_data = json.loads(decoded_data)

            return decoded_data

    # Define device-specific methods here, and check the firmware version for compatibility.
    # For instance, as of a future UsbParMar version, the LEDs can be deactivated.
    # Also, as of a future UsbParMar version, a pattern can be specified.



class EVA(DeviceInterface):
    """Class for EVA device.

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


