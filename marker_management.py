"""Core Library for Sending Markers

This module contains code for sending markers using various devices available at the FSW.

Devices:
    UsbParMarker
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
import utils.GS_timing as timing
import serial
import datetime
import json
import pandas
import re
import sys
import os
import csv
from serial.tools.list_ports import comports
from prettytable import PrettyTable

# Address string indicating that the device is being faked/spoofed:
FAKE_ADDRESS = 'FAKE'
FAKE_DEVICE = 'FAKE DEVICE'

# Indicate devices here
available_devices = {'UsbParMarker', 'EVA', FAKE_DEVICE}


class MarkerManager:
    """Sends markers to a given device.

    An instance of this class is tied to a device, and sends controls and sends markers.

    Available devices:
        UsbParMarker:
            This mode uses the "UsbParMarker" gadget to send markers. The device_address
            param must be its COM address (e.g. COM3).
        EVA:
            This mode uses the "EVA" gadget to send markers. The device_address
            param must be its COM address (e.g. COM3).

    """

    # Log class instances:
    marker_manager_instances = []

    def __init__(self, device_type, device_address=FAKE_ADDRESS, crash_on_marker_errors=True,
                 time_function_us=lambda: timing.micros(), **kwargs):
        """Builds the marker class, and the device interface class used to talk to the device."""

        # MarkerManager checks
        try:

            # Check if class with same type and address (except fake) already exists
            if not len(MarkerManager.marker_manager_instances) == 0 and not device_address == FAKE_ADDRESS:

                for instance in MarkerManager.marker_manager_instances:

                    instance_properties = instance.device_interface.device_properties()
                    instance_address = instance.device_interface.device_address()

                    if instance_address == device_address and instance_properties['Device'] == device_type:
                        err_msg = "class of same type and with same address already exists"
                        raise MarkerManagerError(err_msg)

            # Check device type
            if device_type not in available_devices:
                err_msg = f"device_type can only be {available_devices}, got: {device_type}"
                raise MarkerManagerError(err_msg)

            # Check device address
            if not type(device_address) == str:
                err_msg = f"device_address should be str, got {type(device_address)}"
                raise MarkerManagerError(err_msg)

            # Check report_marker_errors
            if not type(crash_on_marker_errors == bool):
                err_msg = f"report_marker_errors should be bool, got {type(crash_on_marker_errors)}"
                raise MarkerManagerError(err_msg)

            # Check time function
            if not callable(time_function_us):
                err_msg = "time_function_us should be function"
                raise MarkerManagerError(err_msg)

        except MarkerManagerError as e:
            raise e

        except Exception as e:
            raise BaseException(f'Unknown error: {e}')

        # Instantiate the correct DeviceInterface subclass
        self.device_type = device_type
        if self.device_type == 'UsbParMarker':
            self.device_interface = UsbParMarker(device_address)
        elif self.device_type == 'EVA':
            self.device_interface = EVA(device_address)
        # Create general serial device when device is fake
        elif self.device_type == FAKE_DEVICE:
            self.device_interface = SerialDevice(FAKE_ADDRESS)

        # Log timestamp of creation (use GS_Timing microseconds):
        self._time_function_us = time_function_us
        self._start_time = time_function_us()

        self.set_value_list = list()
        self.error_list = list()
        self.crash_on_marker_errors = crash_on_marker_errors
        self.concurrent_marker_threshold_ms = 10

        self.marker_df = pandas.DataFrame()
        self.summary_df = pandas.DataFrame()
        self.error_df = pandas.DataFrame()

        # Reset marker on init (the marker tracking table assumes that the device has no active markers after init):
        self._current_value = 0
        self.set_value(0)

        # In the future, add an optional Tkinter always-on-top GUI that shows the current marker value, the bit states,
        # the device props, etc, a table with the markers, etc.
        self.gui = None

        MarkerManager.marker_manager_instances.append(self)

    @property
    def device_address(self):
        """Returns the device address"""
        return self.device_interface.device_address()

    @property
    def device_properties(self):
        """Returns the device properties"""
        return self.device_interface.device_properties()

    def close(self):
        """Closes the connection to the device."""
        self.device_interface._close()

    def set_value(self, value):
        """Sets the marker value.

        The current marker value and current time are saved in self.set_value_list

        The following fatal marker errors are thrown:
          - If the value is not a whole number
          - If the value is outside of range (0 - 255)

        The following non-fatal marker errors are thrown if self.crash_on_marker_errors is true,
            else they are stored in self.error_list:
          - Double markers:
             If the value is not zero (zeros are not markers) and the value is equal to the current value,
             the same value is sent twice in a row with no effect.
          - Concurrent markers:
             If a marker was sent less than concurrent_marker_threshold_ms after the previous.
          - Marker error:
             If the marker could not be sent to the marker device for whatever reason.
        """

        # Check and send marker:
        try:

            # Value should be int (whole number):
            if not whole_number(value):
                err_msg = "Marker value should be whole number."
                is_fatal = True
                raise MarkerError(err_msg, is_fatal)
            
            # Value should be between 0 and 255:
            if value > 255 or value < 0:
                err_msg = "Marker value out of range (0 - 255)."
                is_fatal = True
                raise MarkerError(err_msg, is_fatal)

            # The same value should not be sent twice (except 0, that doesn't matter):
            if not len(self.set_value_list) == 0 and not value == 0:
                last_value = self.set_value_list[-1]['value']
                if value == last_value:

                    err_msg = f"Marker with value {value} is sent twice in a row."
                    is_fatal = False
                    raise MarkerError(err_msg, is_fatal)

            # Two values should be separated by at least the concurrent marker threshold:
            if not len(self.set_value_list) == 0:
                last_start_time = self.set_value_list[-1]['time_us']
                last_value = self.set_value_list[-1]['value']
                if (self._time_function_us() - last_start_time) < (self.concurrent_marker_threshold_ms * 1000):
                    err_msg = f"Marker with value {value} was sent within {self.concurrent_marker_threshold_ms} " \
                              f"ms after previous marker with value {last_value}"
                    is_fatal = False
                    raise MarkerError(err_msg, is_fatal)

            # Send marker:
            try:
                self.device_interface._set_value(value)
            except Exception as e:
                err_msg = f"Could not send marker: {e}."
                is_fatal = False
                raise MarkerError(err_msg, is_fatal)

        except MarkerError as e:
            # Save error
            self.error_list.append({'time_us': self._time_function_us(), 'error': e.message})
            if e.is_fatal or self.crash_on_marker_errors:
                raise e
                
        except Exception as e:
            raise BaseException(f'Unknown error: {e}')

        # Save marker value
        self._current_value = value

        # Calculate the marker time relative to the self.start_time, and log the marker:
        marker_time_us = self._time_function_us()
        self.set_value_list.append({'value': value, 'time_us': marker_time_us})

    def send_marker_pulse(self, value, duration_ms=100):
        """Sends a short marker pulse (blocking), and resets to 0 afterwards"""
        self.set_value(value)
        timing.delay(duration_ms)
        self.set_value(0)

    def set_bits(self, bits):
        """
        Generic function for toggling bits.

        E.g. markers.set_bits('00000001') sets all bits except the last to LOW.

        This function expects a string of 8 chars representing the bits in big-endian order (MSB left)
        """

        # Check that bits consist of string with 8 chars:
        if not type(bits) == str and len(bits) != 8:
            err_msg = "bits should be str containing characters"
            raise MarkerManagerError(err_msg)

        # Check that the 8 chars consist of zeros and/or ones:
        find_all_bits = re.findall('[0-1]', bits)
        if not len(find_all_bits) == 8:
            err_msg = "bits should be 8 str characters consisting of 0 or 1, e.g. '00000001'"
            raise MarkerManagerError(err_msg)

        # Convert bits to int and set value
        value = int(bits, 2)
        self.set_value(value)

    def set_bit(self, bit, state):
        """Toggle a single bit.

        Toggle a single bit, leave other bits intact.

        Use EVA bit numbering convention: 0 - 7 -> 0 is MSB?

        """

        if not whole_number(bit) or bit < 0 or bit > 7:
            err_msg = "bit should be whole number between 0 and 7"
            raise MarkerManagerError(err_msg)

        # Convert current value to 8 bit string
        cur_bits = format(self._current_value, '#010b')[2:]

        # Set concerning bit dependent on state:
        if state == 'on':
            new_bits = cur_bits[:bit] + '1' + cur_bits[bit + 1:]
        elif state == 'off':
            new_bits = cur_bits[:bit] + '0' + cur_bits[bit + 1:]
        else:
            err_msg = "set_bit state can only be 'on' or 'off'"
            raise MarkerManagerError(err_msg)

        # Convert 8 bit string to int and set_value:
        value = int(new_bits, 2)
        self.set_value(value)

    def gen_marker_table(self):
        """
        Returns three dataframes:
          - marker dataframe
                This dataframe has, in chronological order, the marker value, its start and end time, duration and
                occurrence. The end time and duration are infinite if the current value is non-zero (the current marker
                has not yet ended).
          - summary dataframe
                The summary dataframe has a list of all unique values and how many times they were sent (total
                occurrences).
          - error dataframe
                The error dataframe has a list of all non-fatal errors and their times.
        """

        set_value_df = pandas.DataFrame(self.set_value_list)

        last_value = None
        marker_counter = 0

        df_cols = ['value', 'start_time_us', 'end_time_us', 'duration_us', 'occurrence']
        marker_df = pandas.DataFrame(columns=df_cols)

        # Get marker start and end time
        # - The marker start is defined as marker value change from zero to non-zero or from non-zero to non-zero
        # - The marker end is defined as a marker value change from non-zero to zero or from non-zero to non-zero
        for index in set_value_df.index:

            cur_value = set_value_df.at[index, 'value']

            # Value changes
            if cur_value != last_value:

                # Value changed to 0 and it is not the first value (first value is always set to 0 at init)
                if cur_value == 0 and last_value is not None:

                    # end marker
                    cur_marker_end_time = set_value_df.at[index, 'time_us']
                    marker_df.at[marker_counter, 'end_time_us'] = cur_marker_end_time
                    marker_counter = marker_counter + 1

                # Value changed from 0 to non-zero
                elif cur_value != 0 and last_value == 0:

                    # start marker:
                    cur_marker_value = cur_value
                    cur_marker_start_time = set_value_df.at[index, 'time_us']
                    marker_df.at[marker_counter, 'value'] = cur_marker_value
                    marker_df.at[marker_counter, 'start_time_us'] = cur_marker_start_time

                # Value changed from non-zero to non-zero
                elif cur_value != 0 and last_value != 0:

                    # end marker:
                    cur_marker_end_time = set_value_df.at[index, 'time_us']
                    marker_df.at[marker_counter, 'end_time_us'] = cur_marker_end_time
                    marker_counter = marker_counter + 1

                    # start marker:
                    cur_marker_value = cur_value
                    cur_marker_start_time = set_value_df.at[index, 'time_us']
                    marker_df.at[marker_counter, 'value'] = cur_marker_value
                    marker_df.at[marker_counter, 'start_time_us'] = cur_marker_start_time

            last_value = cur_value

        # When the last marker was a non-zero value, set end time to infinite
        if pandas.isna(marker_df["end_time_us"].values[-1]):
            marker_df["end_time_us"].values[-1] = float('inf')

        # Save duration
        marker_df["duration_us"] = marker_df["end_time_us"] - marker_df["start_time_us"]

        # Save marker occurrences:
        marker_occur_dict = {}
        for index in marker_df.index:
            cur_value = marker_df.at[index, 'value']
            if marker_occur_dict.get(cur_value) is None:
                occurrence = 1
            else:
                occurrence = marker_occur_dict.get(cur_value) + 1
            marker_occur_dict[cur_value] = occurrence
            marker_df.loc[index, "occurrence"] = occurrence

        # Create summary
        summary = marker_df[['value', 'occurrence']]
        summary = summary.drop_duplicates(subset=['value'], keep='last')

        # Save table dataframes:
        self.marker_df = marker_df
        self.summary_df = summary
        self.error_df = pandas.DataFrame(self.error_list)

        return self.marker_df, self.summary_df, self.error_df

    def print_marker_table(self):
        """Prints the marker table, summary table and error table, generated with gen_marker_table."""

        # Generate most up-to-date marker table
        self.gen_marker_table()

        # Create pretty tables:
        summary_table = PrettyTable()
        summary_table.title = "Summary table"
        summary_table.field_names = list(self.summary_df.columns)
        for row in self.summary_df.itertuples():
            summary_table.add_row(row[1:])

        marker_table = PrettyTable()
        marker_table.title = "Marker table"
        marker_table.field_names = list(self.marker_df.columns)
        for row in self.marker_df.itertuples():
            marker_table.add_row(row[1:])

        error_table = PrettyTable()
        error_table.title = "Error table"
        error_table.field_names = list(self.error_df.columns)
        for row in self.error_df.itertuples():
            error_table.add_row(row[1:])

        # summary_table.set_style(SINGLE_BORDER)
        # marker_table.set_style(SINGLE_BORDER)
        # error_table.set_style(SINGLE_BORDER)

        # Print tables
        print(error_table)
        print(summary_table)
        print(marker_table)

    def save_marker_table(self, location=os.getcwd()):
        """Saves the marker table, summary table and error table in one TSV file."""

        # Generate most up-to-date marker table
        self.gen_marker_table()

        # Check if location has writing permission
        if not os.access(location, os.W_OK):
            err_msg = f'No writing permissions in {location}. Marker table cannot be saved.'
            raise MarkerManagerError(err_msg)

        else:

            # Create filename
            cur_date_time = datetime.datetime.now()
            date_n = cur_date_time.strftime("%Y%m%d%H%M%S")
            fn = date_n + '_marker_table.tsv'
            full_fn = location + '\\' + fn

            # Get date
            date_str = cur_date_time.strftime("%Y-%m-%d %H:%M:%S")

            # Convert data to series
            self.summary_df.squeeze()
            self.marker_df.squeeze()
            self.error_df.squeeze()

            # Write data to tsv file
            with open(full_fn, 'w', newline='') as file_out:
                writer = csv.writer(file_out, delimiter='\t')
                writer.writerow(['Date: ' + date_str])
                writer.writerow(['Device: ' + self.device_properties.get('Device')])
                writer.writerow(['Serialno: ' + self.device_properties.get('Serialno')])
                writer.writerow(['Version: ' + self.device_properties.get('Version')])
                writer.writerow('')
                writer.writerow(self.summary_df.head())
                writer.writerows(self.summary_df.values)
                writer.writerow('')
                writer.writerow(self.marker_df.head())
                writer.writerows(self.marker_df.values)
                writer.writerow('')
                writer.writerow(self.error_df.head())
                writer.writerows(self.error_df.values)


class MarkerError(Exception):
    def __init__(self, message, is_fatal):
        super().__init__(message)

        self.message = message
        self.is_fatal = is_fatal


class MarkerManagerError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class FindDeviceError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class SerialError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


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
        """
        Returns the properties of the device as follows (values are examples):
         {"Version":"HW1:SW1.1","Serialno":"S01234","Device":"UsbParMar"}
        """
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
    def is_fake(self):
        """Returns a bool indication if the device is faked."""
        return self.device_address == FAKE_ADDRESS


class SerialDevice(DeviceInterface):

    def __init__(self, device_address):

        # Save attribs:
        self._device_address = device_address

        if not device_address == FAKE_ADDRESS:

            # Open device in command mode:
            self.command_mode()
            timing.delay(100)

            # Example: {"Version":"HW1:SW1.2","Serialno":"S01234","Device":"UsbParMar"}
            properties = self.get_info()

            if properties == "":
                err_msg = "Serial device did not respond."
                raise SerialError(err_msg)
            if "Serialno" not in properties:
                err_msg = "Serialno missing."
                raise SerialError(err_msg)

            # Close device
            self.serial_device.close()
            timing.delay(100)

            # Open device in data mode:
            self.data_mode()
            timing.delay(100)

        # return fake device
        else:
            properties = {"Version": "0000000",
                          "Serialno": "0000000",
                          "Device": "FAKE device"}

        self._device_properties = properties

    def device_address(self):
        """Returns device address."""
        return self._device_address

    def device_properties(self):
        """Returns device properties."""
        return self._device_properties

    def _set_value(self, value):
        """Sets the value of the usbParMar device."""
        if not self._device_address == FAKE_ADDRESS:
            value_byte = value.to_bytes(1, 'big')
            self.serial_device.write(value_byte)

    def _close(self):
        """Closes the serial connection."""
        if not self._device_address == FAKE_ADDRESS:
            self.serial_device.close()

    def command_mode(self):
        """Opens serial device in command mode."""
        command_params = {"baudrate": 4800, "bytesize": 8,
                          "parity": 'N', "stopbits": 1,
                          "timeout": 2}
        self.open_serial_device(command_params)

    def data_mode(self):
        """Opens serial device in data mode."""
        data_params = {"baudrate": 115200, "bytesize": 8,
                       "parity": 'N', "stopbits": 1,
                       "timeout": 2}
        self.open_serial_device(data_params)

    def open_serial_device(self, params):
        """Opens serial device with specified baudrate."""
        # Create serial device.
        try:
            self.serial_device = serial.Serial(self._device_address, **params)
        except:
            err_msg = "Could not open serial device"
            raise SerialError(err_msg)

    def send_command(self, command):
        """Sends command to serial device."""
        if not self.serial_device.baudrate == 4800:
            err_msg = "Serial device not in command mode."
            raise SerialError(err_msg)
        if not self.serial_device.is_open:
            err_msg = "Serial device not open."
            raise SerialError(err_msg)
        if not type(command) == str:
            err_msg = "Command should be a string."
            raise SerialError(err_msg)
        else:

            # Send command
            self.serial_device.flushInput()
            self.serial_device.write(command.encode())
            timing.delay(100)

            # Get reply
            data = self.serial_device.readline()

            decoded_data = data.decode('utf-8')

            # If reply is json string, decode it
            try:
                json.loads(decoded_data)
            except ValueError:
                pass
            else:
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

    def get_hw_version(self):
        properties = self.device_properties()
        version = properties.get('Version')
        hw_version = re.search('HW(.*):', version)
        return hw_version.group(1)

    def get_sw_version(self):
        properties = self.device_properties()
        version = properties.get('Version')
        sw_version = re.search('SW(.*)', version)
        return sw_version.group(1)


class UsbParMarker(SerialDevice):
    """Class for the UsbParMarker.
    Note, the subclass constructors must throw errors if the specified parameters cannot be resolved.
    E.g., no device with the specified address exist, or it it is not of the expected type.
    """

    def leds_on(self):
        """Turns led lights on"""
        sw_version = self.get_sw_version()
        if float(sw_version) < 1.3:
            leds_on_answer = 'Check firmware version, could not turn on leds'
        else:
            leds_on_answer = self.send_command('L')
        return leds_on_answer

    def leds_off(self):
        """Turns led lights on"""
        sw_version = self.get_sw_version()
        if float(sw_version) < 1.3:
            leds_off_answer = 'Check firmware version, could not turn off leds'
        else:
            leds_off_answer = self.send_command('O')
        return leds_off_answer


class EVA(SerialDevice):
    """Class for EVA device.
    Note, the subclass constructors must throw errors if the specified parameters cannot be resolved.
    E.g., no device with the specified address exist, or it it is not of the expected type.

    """
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


def whole_number(value):
    if isinstance(value, int) or \
            (isinstance(value, float) and value.is_integer()):
        return True
    else:
        return False


# Helper functions:
def gen_com_filters(device_regex='^.*$',
                    port_regex='^.*$',
                    sn_regex='^.*$',
                    com_dev_desc_regex='^.*$',
                    com_dev_hwid_regex='^USB VID:PID=2341:.*$'):

    # Return the COM filters:
    return {
        "device_regex": device_regex,
        "port_regex": port_regex,
        "sn_regex": sn_regex,
        "com_dev_desc_regex": com_dev_desc_regex,
        "com_dev_hwid_regex": com_dev_hwid_regex}


def find_device(device_type='', serial_no='', com_port='', fallback_to_fake=False):
    """ Finds the address of the device.

    If UsbParMarker mode or EVA mode, find the COM port. If a device_name was specified, check that the
    serial number matches.
    Throw error if multiple COM candidates are available.

    However, if fallback_to_fake is true, don't throw error, just returns the address that toggles faking.  

    """

    # Check device type
    if device_type not in available_devices and device_type != '':
        raise FindDeviceError(f"Only {available_devices} supported.")

    info = {}

    # Create filters
    device_regexp = "^.*$"
    sn_regexp = "^.*$"
    port_regexp = "^.*$"

    if not device_type == '':
        device_regexp = "^" + device_type + "$"
    if not serial_no == '':
        sn_regexp = "^" + serial_no + "$"
    if not com_port == '':
        port_regexp = "^" + com_port + "$"

    com_filters = gen_com_filters(device_regex=device_regexp,
                                  port_regex=port_regexp,
                                  sn_regex=sn_regexp)

    # Params:
    connected = False
    port_hit = False
    device_hit = False
    serial_hit = False
    multiple_hit = False
    connection_error = False
    connection_error_port = ''
    connection_error_info = ''
    port_list = []

    # Loop through ports
    for port, desc, hwid in comports():

        # Check filters:
        port_matches_request = re.match(com_filters['port_regex'], port) is not None
        com_dev_desc_matches = re.match(com_filters['com_dev_desc_regex'], desc) is not None
        com_dev_hwid_matches = re.match(com_filters['com_dev_hwid_regex'], hwid) is not None

        if not (port_matches_request
                and com_dev_desc_matches
                and com_dev_hwid_matches):
            continue

        # save ports in list
        port_list.append(port)

    if len(port_list) != 0:

        # At least one port with correct port, desc and hwid found
        port_hit = True

        # Loop through ports and check devices
        for port in port_list:

            try:
                # Create general serial device to obtain device info
                cur_device = SerialDevice(port)

            except:
                try:
                    cur_device._close()
                except:
                    pass
                connection_error = True
                connection_error_port = port
                connection_error_info = sys.exc_info()[1]
                continue

            info["device"] = cur_device.device_properties()

            # Check filter
            device_matches_request = re.match(com_filters['device_regex'], info['device']['Device']) is not None
            serial_matches_request = re.match(com_filters['sn_regex'], info['device']['Serialno']) is not None

            if device_matches_request:
                device_hit = True
            if serial_matches_request:
                serial_hit = True
            if connected:
                multiple_hit = True

            info["com_port"] = port
            connected = True

    # Checks:
    try:

        # Check if any port was found:
        if not port_hit:
            err_msg = "No device matched the specified COM address."
            raise FindDeviceError(err_msg)
        if not device_hit:
            err_msg = "No device matched the specified device type."
            raise FindDeviceError(err_msg)
        if not serial_hit:
            err_msg = "No device matched the specified serial number."
            raise FindDeviceError(err_msg)
        if not connected:
            err_msg = "No suitable COM devices found."
            raise FindDeviceError(err_msg)
        if multiple_hit:
            err_msg = "Multiple matching devices found."
            FindDeviceError(err_msg)
        if connection_error:
            err_msg = f'Could not connect to "{connection_error_port}" because: {connection_error_info}'
            raise FindDeviceError(err_msg)

    except FindDeviceError as e:
        if fallback_to_fake:
            info['device'] = {'Version': '0000000',
                              'Serialno': '0000000',
                              'Device': FAKE_DEVICE}
            info["com_port"] = FAKE_ADDRESS
        else:
            raise e

    except Exception as e:
        raise BaseException(f'Unknown error: {e}.')

    return info
