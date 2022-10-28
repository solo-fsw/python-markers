"""Core Library for Sending Markers

This module contains code for sending markers using various devices available at the FSW.

Devices:
    UsbParMar
    EVA

FOR DEV:

 > Markers are defined here:
    https://physiodatatoolbox.leidenuniv.nl/docs/user-guide/epochs.html#markers
    https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/


 Style Guide:
   http://google.github.io/styleguide/pyguide.html


Notes:
    Only Python 3 supported
    Only Windows supported

"""

from abc import ABC, abstractmethod
import serial
import time
import json
import pandas
import re
import sys
from serial.tools.list_ports import comports
from prettytable import PrettyTable

# Address string indicating that the device is being faked/spoofed:
FAKE_ADDRESS = 'FAKE'
except_factory = BaseException


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

    def __init__(self, device_type, device_address='', fallback_to_fake=False, crash_on_marker_errors=True,
                 time_function_us=lambda: time.time() * 1000000):
        """Builds the marker class, and the device interface class used to talk to the device."""


        # Note, add ability to forward KW arguments to the DeviceInterface constructor.

        # Todo: check if class with same type and address already exists

        # Check device type
        if not (device_type == 'UsbParMar'
                or device_type == 'EVA'):
            raise except_factory(f"device_type can only be UsbParMar or EVA, got: {device_type}")

        # Check device address (not required when fake device is used):
        if not fallback_to_fake and device_address == '':
            raise except_factory("Missing required argument: 'device_address'")

        if not type(device_address) == str:
            raise except_factory(f"device_address should be str, got {type(device_address)}")

        # Check fallback_to_fake
        if not type(fallback_to_fake == bool):
            raise except_factory(f"fallback_to_fake should be bool, got {type(fallback_to_fake)}")

        # Check report_marker_errors
        if not type(crash_on_marker_errors == bool):
            raise except_factory(f"report_marker_errors should be bool, got {type(crash_on_marker_errors)}")

        # Check time function
        if not callable(time_function_us):
            raise except_factory("time_function_us should be function")

        # Set fake address when fallback to fake:
        if fallback_to_fake:
            device_address = FAKE_ADDRESS
        if device_address == 'FAKE':
            fallback_to_fake = True

        # Instantiate the correct DeviceInterface subclass (doesn't work):
        # self.device_interface = type(device_type, (), {"device_address": device_address})

        # Instantiate the correct DeviceInterface subclass
        self.device_type = device_type
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
        self.crash_on_marker_errors = crash_on_marker_errors
        self.concurrent_marker_threshold_ms = 10

        self.marker_df = pandas.DataFrame()
        self.summary = pandas.DataFrame()

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
        # Regardless of report_marker_errors, throw error is marker is outside of range (0 - 255).

        marker_error = ''

        # # Value should be int:
        if not type(value) == int:
            raise except_factory("Marker value should be integer.")

        # Value should be between 0 and 255
        if value > 255 or value < 0:
            raise except_factory("Marker value out of range (0 - 255).")

        # The same value should not be sent twice (except 0, that doesn't matter):
        if not len(self.marker_list) == 0 and not value == 0:

            last_value = self.marker_list[-1]['value']

            if value == last_value:

                twice_error = f"Marker with value {value} is sent twice in a row."

                if self.crash_on_marker_errors:
                    raise except_factory(twice_error)
                else:
                    marker_error = twice_error

        # Two values should be separated by at least the concurrent marker threshold
        if not len(self.marker_list) == 0:
            last_start_time = self.marker_list[-1]['start_time_us']

            if (self._time_function_us() - last_start_time) < (self.concurrent_marker_threshold_ms*1000):

                concurrent_error = f"Marker was sent within {self.concurrent_marker_threshold_ms} ms after last marker "

                if self.crash_on_marker_errors:
                    raise except_factory(concurrent_error)
                else:
                    marker_error = concurrent_error

        # Send marker
        try:
            self.device_interface._set_value(value)
        except:
            no_marker_error = "Could not send marker."
            if self.crash_on_marker_errors:
                raise except_factory(no_marker_error)
            else:
                marker_error = no_marker_error
                self.fallback_to_fake = True

        self._current_value = value

        # Calculate the marker time relative to the self.start_time, and log the marker:
        marker_time_us = self._time_function_us()
        self.marker_list.append({'value': value, 'start_time_us': marker_time_us, 'marker_error': marker_error})

    def send_marker_pulse(self, value, duration_ms=100):
        """Sends a short marker pulse (blocking), and resets to 0 afterwards"""
        self.set_value(value)
        time.sleep(duration_ms/1000)
        self.set_value(0)

    def set_bits(self, bits):
        """Generic function for toggling bits.

        E.g. markers.set_bits('00000001') sets all bits except the last to LOW.
        Use EVA endianess convention.

        LSB is the right one
        MSB is the left one
        """
        # Todo: set bits

        # Calculate the value from the bits, call set_value().
        value = 9999
        self.set_value(value)

    def set_bit(self, bit, state):
        """Toggle a single bit.

        Toggle a single bit, leave other bits intact. Use EVA bit numbering convention.

        0 - 7

        """
        # Todo: set bit

        value = 9999
        self.set_value(value)

    def gen_marker_table(self):
        """Returns a table (e.g. dataframe) with a list of all markers:

        The table has, in chronological order, the marker value, and its start and end time, duration and occurrence.
        The end time and duration are infinite if the current value is non-zero (the current marker has not yet ended).

        A table with the summaries of all markers is also returned, it has a list of all the unique values,
        and how many times they were sent (total occurrences)."""

        marker_df = pandas.DataFrame(self.marker_list)

        # Save end time (marker ends when next value is set)
        marker_df["end_time_us"] = marker_df["start_time_us"].shift(-1)

        # Remove the 0 markers
        zero_index = marker_df[marker_df["value"] == 0].index
        marker_df.drop(zero_index, inplace=True)
        marker_df.reset_index(drop=True, inplace=True)

        # When the last marker was a non-zero value, set end time to infinite
        if pandas.isna(marker_df["end_time_us"].values[-1]):
            marker_df["end_time_us"].values[-1] = float('inf')

        # Save duration
        marker_df["duration_us"] = marker_df["end_time_us"] - marker_df["start_time_us"]

        # Save marker occurrences:
        marker_df["occurrence"] = 0
        marker_occur_dict = {}
        for index in marker_df.index:
            cur_value = marker_df.at[index, 'value']
            if marker_occur_dict.get(cur_value) is None:
                occurrence = 1
            else:
                occurrence = marker_occur_dict.get(cur_value) + 1
            marker_occur_dict[cur_value] = occurrence
            marker_df.at[index, "occurrence"] = occurrence

        marker_df = marker_df[['value', 'start_time_us', 'end_time_us', 'duration_us', 'occurrence', 'marker_error']]

        # Create summary
        summary = marker_df['value'].value_counts()
        summary = summary.to_frame()
        summary.reset_index(inplace=True)
        summary = summary.rename(columns={'value': 'total_occurrences', 'index': 'value'})

        self.marker_df = marker_df
        self.summary = summary

        return self.marker_df, self.summary

    def print_marker_table(self):
        """Pretty prints the gen_marker_table data."""
        self.gen_marker_table()
        print(PrettyTable(self.summary, headers='keys', tablefmt='fancy_grid'))
        print(PrettyTable(self.marker_df, headers='keys', tablefmt='fancy_grid'))
    
    def save_marker_table(self):
        """Saves the marker table and summary as TSV files."""
        # Todo: save header info in tsv files and make better file names
        self.gen_marker_table()
        self.marker_df.to_csv('marker_table.tsv', sep='\t', index=False)
        self.summary.to_csv('marker_summary.tsv', sep='\t', index=False)


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
        # Aren't regular key value pairs better:
        # {"Version":"HW1:SW1.2","Serialno":"S01234","Device":"UsbParMar"}
        pass


    @abstractmethod
    def _set_value(self, value):
        """Sets the value of the marker device. The Markers.set_value
        should be used by users since it performs generic checks and
        logs the markers."""
        pass

    
    @abstractmethod
    def _close(self):
        """Closes the connection to the serial device, if necessary."""
        pass


    @property
    @abstractmethod
    def is_fake(self):
        """Returns a bool indication if the device is faked."""
        pass


class UsbParMar(DeviceInterface):
    """Class for the UsbParMar.

    """

    def __init__(self, device_address, fallback_to_fake):

        # Save attribs:
        self._device_address = device_address
        self._fallback_to_fake = fallback_to_fake

        if not fallback_to_fake:

            # Open device in command mode:
            self.command_mode()
            time.sleep(0.1)

            #  Should be: {"name" : "firmware_version", "label" : "Firmware version", "value": "0.4.1"}
            # Aren't regular key value pairs better:
            # {"Version":"HW1:SW1.2","Serialno":"S01234","Device":"UsbParMar"}
            properties = self.get_info()

            if properties == "":
                raise except_factory("Serial device did not respond.")
            if "Serialno" not in properties:
                raise except_factory("Serialno missing.")

            # Close device
            self.serial_device.close()
            time.sleep(0.1)

            # Open device in data mode:
            self.data_mode()
            time.sleep(0.1)

        # fall_back_to_fake:
        else:
            properties = {"Version": "0000000",
                          "Serialno": "0000000",
                          "Device": "FAKE UsbParMar"}

        self._device_properties = properties

    def device_address(self):
        """Returns device address."""
        return self._device_address

    def device_properties(self):
        """Returns device properties."""
        return self._device_properties

    def _set_value(self, value):
        """Sets the value of the usbParMar device."""
        if not self._fallback_to_fake:
            value_byte = value.to_bytes(1, 'big')
            self.serial_device.write(value_byte)

    def _close(self):
        """Closes the serial connection."""
        if not self._fallback_to_fake:
            self.serial_device.close()

    def is_fake(self):
        """Returns bool indicating whether the device is fake or not."""
        return self._fallback_to_fake

    def command_mode(self):
        """Opens serial device in command mode."""
        command_params = {"baudrate": 4800, "bytesize": 8
                            , "parity": 'N', "stopbits": 1
                            , "timeout": 2}
        self.open_serial_device(command_params)

    def data_mode(self):
        """Opens serial device in data mode."""
        data_params = {"baudrate": 115200, "bytesize": 8
                            , "parity": 'N', "stopbits": 1
                            , "timeout": 2}
        self.open_serial_device(data_params)

    def open_serial_device(self, params):
        """Opens serial device with specified baudrate."""
        # Create serial device.
        try:
            self.serial_device = serial.Serial(self._device_address, **params)
        except:
            raise except_factory('Could not open serial device')

    def send_command(self, command):
        """Sends command to serial device."""
        if not self.serial_device.baudrate == 4800:
            raise except_factory("Serial device not in command mode.")
        if not self.serial_device.is_open:
            raise except_factory("Serial device not open.")
        if not type(command) == str:
            raise except_factory("Command should be a string.")
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

    def get_info(self):
        """Get info from serial device"""
        info = self.send_command('V')
        return info

    def ping(self):
        """Ping serial device"""
        ping_answer = self.send_command('P')
        return ping_answer

    def leds_on(self):
        """Turns led lights on"""
        leds_on_answer = self.send_command('L')
        return leds_on_answer

    def leds_off(self):
        """Turns led lights on"""
        leds_off_answer = self.send_command('O')
        return leds_off_answer

    # Define device-specific methods here, and check the firmware version for compatibility.
    # For instance, as of a future UsbParMar version, the LEDs can be deactivated.
    # Also, as of a future UsbParMar version, a pattern can be specified.


class EVA(DeviceInterface):
    """Class for EVA device.

    """

    def __init__(self, device_address, fallback_to_fake):

        # Save attribs:
        self._device_address = device_address
        self._fallback_to_fake = fallback_to_fake

        if not fallback_to_fake:

            # Open device in command mode:
            self.command_mode()
            time.sleep(0.1)

            #  Should be: {"name" : "firmware_version", "label" : "Firmware version", "value": "0.4.1"}
            # Aren't regular key value pairs better:
            # {"Version":"HW1:SW1.2","Serialno":"S01234","Device":"UsbParMar"}
            properties = self.get_info()

            if properties == "":
                raise except_factory("Serial device did not respond.")
            if "Serialno" not in properties:
                raise except_factory("Serialno missing.")

            # Close device
            self.serial_device.close()
            time.sleep(0.1)

            # Open device in data mode:
            self.data_mode()
            time.sleep(0.1)

        # fall_back_to_fake:
        else:
            properties = {"Version": "0000000",
                          "Serialno": "0000000",
                          "Device": "FAKE EVA"}

        self._device_properties = properties

    def device_address(self):
        """Returns device address."""
        return self._device_address

    def device_properties(self):
        """Returns device properties."""
        return self._device_properties

    def _set_value(self, value):
        """Sets the value of the usbParMar device."""
        if not self._fallback_to_fake:
            value_byte = value.to_bytes(1, 'big')
            self.serial_device.write(value_byte)

    def _close(self):
        """Closes the serial connection."""
        if not self._fallback_to_fake:
            self.serial_device.close()

    def is_fake(self):
        """Returns bool indicating whether the device is fake or not."""
        return self._fallback_to_fake

    def command_mode(self):
        """Opens serial device in command mode."""
        command_params = {"baudrate": 4800, "bytesize": 8
            , "parity": 'N', "stopbits": 1
            , "timeout": 2}
        self.open_serial_device(command_params)

    def data_mode(self):
        """Opens serial device in data mode."""
        data_params = {"baudrate": 115200, "bytesize": 8
            , "parity": 'N', "stopbits": 1
            , "timeout": 2}
        self.open_serial_device(data_params)

    def open_serial_device(self, params):
        """Opens serial device with specified baudrate."""
        # Create serial device.
        try:
            self.serial_device = serial.Serial(self._device_address, **params)
        except:
            raise except_factory('Could not open serial device')

    def send_command(self, command):
        """Sends command to serial device."""
        if not self.serial_device.baudrate == 4800:
            raise except_factory("Serial device not in command mode.")
        if not self.serial_device.is_open:
            raise except_factory("Serial device not open.")
        if not type(command) == str:
            raise except_factory("Command should be a string.")
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

    def get_info(self):
        """Get info from serial device"""
        info = self.send_command('V')
        return info

    def ping(self):
        """Ping serial device"""
        ping_answer = self.send_command('P')
        return ping_answer

    def set_active_mode(self):
        """Set into active mode"""
        active_mode = self.send_command('A')
        return active_mode

    def set_passive_mode(self):
        """Set into active mode"""
        passive_mode = self.send_command('S')
        return passive_mode

    def get_mode(self):
        """Get mode (active or passive)"""
        mode = self.send_command('M')
        return mode


# Below are helper functions:
def gen_com_filters(port_regex = '^.*$'
                , sn_regex = '^.*$'
                , com_dev_desc_regex = '^.*$'
                , com_dev_hwid_regex = '^USB VID:PID=2341:.*$'):

    # Return the COM filters:
    return {
        "port_regex": port_regex
        , "sn_regex": sn_regex
        , "com_dev_desc_regex": com_dev_desc_regex
        , "com_dev_hwid_regex": com_dev_hwid_regex}


def find_device(device_type, serial_no='ANY', com_port='ANY', fallback_to_fake=False):
    """ Finds the address of the device.

    If UsbParMar mode or EVA mode, find the COM port. If a device_name was specified, check that the
    serial number matches.
    Throw error if multiple COM candidates are available. Empty device name uses any.

    However, if fallback_to_fake is true, don't throw error, just returns the address that toggles faking.  

    """

    # Check device type
    if not (device_type == 'UsbParMar'
            or device_type == 'EVA'):
        raise except_factory("Only UsbParMar and EVA supported.")

    info = {}

    # Create filters
    sn_regexp = "^.*$"
    port_regexp = "^.*$"
    if not serial_no == 'ANY':
        sn_regexp = "^" + serial_no + "$"
    if not com_port == 'ANY':
        port_regexp = "^" + com_port + "$"
    com_filters = gen_com_filters(port_regex=port_regexp, sn_regex=sn_regexp)

    # Support a fake COM device request:
    if fallback_to_fake:
        if device_type == 'UsbParMar':
            info['device']['version'] = '0000000'
            info['device']['Serialno'] = '0000000'
            info['device']['Device'] = 'FAKE UsbParMar'
            info["com_port"] = 'FAKE'
        elif device_type == 'EVA':
            info['device']['version'] = '0000000'
            info['device']['Serialno'] = '0000000'
            info['device']['Device'] = 'FAKE EVA'
            info["com_port"] = 'FAKE'
        return info

    # Params:
    connected = False
    port_hit = False
    desc_hit = False
    hwid_hit = False
    serial_hit = False
    port_list = []

    # Loop through ports
    for port, desc, hwid in comports():

        # Check filters:
        port_matches_request = re.match(com_filters['port_regex'], port) != None
        com_dev_desc_matches = re.match(com_filters['com_dev_desc_regex'], desc) != None
        com_dev_hwid_matches = re.match(com_filters['com_dev_hwid_regex'], hwid) != None

        if port_matches_request:
            port_hit = True
        if com_dev_desc_matches:
            desc_hit = True
        if com_dev_hwid_matches:
            hwid_hit = True
        if not (port_matches_request
                and com_dev_desc_matches
                and com_dev_hwid_matches):
            continue

        # save ports in list
        port_list.append(port)

    # Check:
    if len(port_list) == 0:
        raise except_factory("No device matched the specified COM address.")
    if not port_hit:
        raise except_factory("No device matched the specified COM address.")
    if not desc_hit:
        raise except_factory("No device matched the specified COM description.")
    if not hwid_hit:
        raise except_factory("No device matched the specified HW ID.")

    if device_type == 'UsbParMar':

        # Loop through ports and check devices
        for port in port_list:

            try:
                usbparmar_device = UsbParMar(port, fallback_to_fake)
                info["device"] = usbparmar_device._device_properties

                # Check filter
                serial_matches_request = re.match(com_filters['sn_regex'], info['device']['Serialno']) != None

                if serial_matches_request:
                    serial_hit = True

                if connected:
                    except_factory("Multiple matching devices found.")

                info["com_port"] = port
                connected = True

            except:
                try:
                    UsbParMar._close()
                except:
                    pass
                raise except_factory(f'Could not connect to "{port}" because: {sys.exc_info()[1]}')

    elif device_type == 'EVA':
        # Loop through ports and check devices
        for port in port_list:

            try:
                eva_device = EVA(port, fallback_to_fake)
                info["device"] = eva_device._device_properties

                # Check filter
                serial_matches_request = re.match(com_filters['sn_regex'], info['device']['Serialno']) != None

                if serial_matches_request:
                    serial_hit = True

                if connected:
                    except_factory("Multiple matching devices found.")

                info["com_port"] = port
                connected = True

            except:
                try:
                    UsbParMar._close()
                except:
                    pass
                raise except_factory(f'Could not connect to "{port}" because: {sys.exc_info()[1]}')

    if not serial_hit:
        raise except_factory("No device matched the specified serial number.")
    if not connected:
        raise except_factory("No suitable COM devices found.")

    return info
