"""Core Library for Sending Markers

This module contains code for sending markers using various devices available at the FSW.

Devices:
    UsbParMarker
    Eva

FOR DEV:
 > Markers are defined here:
    https://physiodatatoolbox.leidenuniv.nl/docs/user-guide/epochs.html#markers
    https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/

 > Style Guide:
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
import warnings

# Current library version
LIB_VERSION = "0.0.1"

# Address string indicating that the device is being faked/spoofed:
FAKE_ADDRESS = 'FAKE'
FAKE_DEVICE = 'FAKE DEVICE'

# Available devices:
#   UsbParMarker:
#       This mode uses the "UsbParMarker" gadget to send markers. The device_address
#       param must be its COM address (e.g. COM3).
#   Eva:
#       This mode uses the "Eva" gadget to send markers. The device_address
#       param must be its COM address (e.g. COM3).
#   FAKE_DEVICE:
#       This mode uses the FAKE_DEVICE
available_devices = {'UsbParMarker', 'Eva', FAKE_DEVICE}


class MarkerManager:
    """Sends markers to a given device.

    An instance of this class is tied to a device, and sends controls and sends markers.

    Attributes:
        device_type:
            string of device type, can only contain one of the devices as defined in available_devices
        device_interface:
            instantiation of the device interface subclass
        _time_function_ms:
            function to get current time in ms
        _start_time:
            time of the current MarkerManager instance creation
        set_value_list:
            list of all set_value calls which includes the value and time
        error_list:
            list of errors that occurred when sending a marker
        crash_on_marker_errors:
            bool indicating whether the script should crash when a marker error occurs
        concurrent_marker_threshold_ms:
            threshold in ms that triggers the concurrent marker error
        marker_df:
            dataframe with all markers (filled when calling gen_marker_table)
        summary_df:
            dataframe with summary of the markers (filled when calling gen_marker_table)
        error_df:
            dataframe with all marker errors (filled when calling gen_marker_table)
        _current_value:
            the current value that is
        gui:
            gui for future purposes (for now: gui = None)
    """

    # Log class instances:
    marker_manager_instances = []

    def __init__(self, device_type, device_address=FAKE_ADDRESS, crash_on_marker_errors=True,
                 time_function_ms=lambda: timing.millis(), **kwargs):
        """Initializes MarkerManager

        Builds the marker class, and the device interface class used to talk to the device.

        Args:
            device_type: see Attributes
            device_address: see Attributes
            crash_on_marker_errors: see Attributes
            time_function_ms: see Attributes

        Raises:
            MarkerManagerError: error when something goes wrong in the MarkerManager
        """

        try:

            if device_type not in available_devices:
                err_msg = f"device_type can only be {available_devices}, got: {device_type}"
                Eid = "UnsupportedDevice"
                raise MarkerManagerError(err_msg, Eid)

            if not isinstance(device_address, str):
                err_msg = f"device_address should be str, got a different type instead"
                Eid = "DeviceAddressString"
                raise MarkerManagerError(err_msg, Eid)

            if not isinstance(crash_on_marker_errors, bool):
                err_msg = f"report_marker_errors should be bool, got {type(crash_on_marker_errors)}"
                Eid = "CrashOnMarkerErrorsBoolean"
                raise MarkerManagerError(err_msg, Eid)

            if not callable(time_function_ms):
                err_msg = "time_function_ms should be function"
                Eid = "TimeFunctionMsCallable"
                raise MarkerManagerError(err_msg, Eid)

            # Check if class with same type and address (except fake) already exists
            if len(MarkerManager.marker_manager_instances) > 0 and device_address != FAKE_ADDRESS:

                for instance in MarkerManager.marker_manager_instances:

                    instance_properties = instance.device_interface.device_properties
                    instance_address = instance.device_interface.device_address

                    if instance_address == device_address and instance_properties['Device'] == device_type:
                        err_msg = "class of same type and with same address already exists"
                        Eid = "DuplicateDevice"
                        raise MarkerManagerError(err_msg, Eid)

        except MarkerManagerError as e:
            raise e

        except Exception as e:
            err_msg = f'Unknown error in MarkerManage initialization: {e}'
            Eid = "BaseException"
            raise MarkerManagerError(err_msg, Eid)
            
        # Instantiate the correct DeviceInterface subclass or create general serial device when device is fake
        self.device_type = device_type
        if self.device_type == 'UsbParMarker':
            self.device_interface = UsbParMarker(device_address)
        elif self.device_type == 'Eva':
            self.device_interface = Eva(device_address)
        elif self.device_type == FAKE_DEVICE:
            self.device_interface = SerialDevice(FAKE_ADDRESS)

        # Log attributes
        self._time_function_ms = time_function_ms
        self._start_time = time_function_ms()

        self.set_value_list = list()
        self.error_list = list()
        self.crash_on_marker_errors = crash_on_marker_errors
        self.concurrent_marker_threshold_ms = 10

        # Reset marker on init (when creating the marker_df in gen_marker_table it is assumed
        # that the device has no active markers after init):
        self._current_value = 0
        self.set_value(0)
        timing.delay(100)

        # In the future, add an optional Tkinter always-on-top GUI that shows the current marker value, the bit states,
        # the device props, etc, a table with the markers, etc.
        self.gui = None

        # Append instance of current marker manager
        MarkerManager.marker_manager_instances.append(self)

    @property
    def device_address(self):
        """Returns the device address"""
        return self.device_interface.device_address

    @property
    def device_properties(self):
        """Returns the device properties"""
        return self.device_interface.device_properties

    def close(self):
        """Closes the connection to the device."""
        self.device_interface._close()

    def set_value(self, value):
        """Sets the marker value.

        The current marker value and current time are saved in self.set_value_list

        Arg:
            value: the marker value

        Raises:
            MarkerError:
                Always raised:
                  - If the value is not a whole number
                  - If the value is outside of range (0 - 255)

                Only when self.crash_on_marker_errors is true (else they are stored in self.error_list):
                  - Double markers:
                     If the value is not zero (zeros are not markers) and the value is equal to the current value,
                     the same value is sent twice in a row with no effect.
                  - Concurrent markers:
                     If a marker was sent less than concurrent_marker_threshold_ms after the previous.
                  - Marker error:
                     If the marker could not be sent to the marker device for whatever reason.
        """

        # Get current time:
        cur_time = self._time_function_ms()

        # Check and send marker:
        try:

            # Value should be int (i.e. whole number):
            if not whole_number(value):
                err_msg = "Marker value should be whole number."
                is_fatal = True
                Eid = "ValueWholeNumber"
                raise MarkerError(err_msg, is_fatal, Eid)

            # Value should be between 0 and 255:
            if value > 255 or value < 0:
                err_msg = "Marker value out of range (0 - 255)."
                is_fatal = True
                Eid = "ValueOutOfRange"
                raise MarkerError(err_msg, is_fatal, Eid)

            # Send marker:
            try:
                self.device_interface._set_value(value)
            except Exception as e:
                err_msg = f"Could not send marker: {e}."
                is_fatal = False
                raise MarkerError(err_msg, is_fatal)

            # The same value should not be sent twice (except 0, that doesn't matter):
            if not len(self.set_value_list) == 0 and not value == 0:
                last_value = self.set_value_list[-1]['value']
                if value == last_value:
                    err_msg = f"Marker with value {value} is sent twice in a row."
                    is_fatal = False
                    Eid = "MarkerSentTwice"
                    raise MarkerError(err_msg, is_fatal, Eid)

            # Two values should be separated by at least the concurrent marker threshold:
            if not len(self.set_value_list) == 0:
                last_start_time = self.set_value_list[-1]['time_ms']
                last_value = self.set_value_list[-1]['value']
                if not (value == 0 and last_value == 0):
                    if (cur_time - last_start_time) < self.concurrent_marker_threshold_ms:
                        err_msg = f"Marker with value {value} was sent within {self.concurrent_marker_threshold_ms} " \
                                  f"ms after previous marker with value {last_value}"
                        is_fatal = False
                        Eid = "ConcurrentMarkerThreshold"
                        raise MarkerError(err_msg, is_fatal, Eid)

        except MarkerError as e:
            # Save error
            self.error_list.append({'time_ms': cur_time, 'error': e.message})
            if e.is_fatal or self.crash_on_marker_errors:
                raise e

        except Exception as e:
            err_msg = f'Unknown error in set_value: {e}'
            Eid = "BaseException"
            raise MarkerError(f'Unknown error: {e}', True, Eid)

        # Save marker value
        self._current_value = value

        # Log the marker:
        self.set_value_list.append({'value': value, 'time_ms': cur_time})

    def send_marker_pulse(self, value, duration_ms=100):
        """Sends a short marker pulse (blocking), and resets to 0 afterwards"""
        self.set_value(value)
        timing.delay(duration_ms)
        self.set_value(0)

    def set_bits(self, bits):
        """Generic function for toggling bits.

        Args:
            bits: a string of 8 chars representing the bits in big-endian order (MSG left). E.g.
                markers.set_bits('00000001') sets all bits except the last to LOW.
        """

        # Check that bits consist of string with 8 chars:
        if type(bits) != str or len(bits) != 8:
            err_msg = "bits should be a string containing 8 characters"
            Eid = "BitTypeLength"
            raise MarkerError(err_msg, True, Eid)

        # Check that the 8 chars consist of zeros and/or ones:
        find_all_bits = re.findall('[0-1]', bits)
        if not len(find_all_bits) == 8:
            err_msg = "bits can only consist of zeros and ones, e.g. '00000001'"
            Eid = "BitElements"
            raise MarkerError(err_msg, True, Eid)

        # Convert bits to int and set value
        value = int(bits, 2)
        self.set_value(value)

    def set_bit(self, bit, state):
        """Toggles a single bit, while leaving other bits intact.

        Args:
            bit: the bit that should be toggled (0 - 7) -> 0 is LSB
            state: 'on' or 'off'
        """

        if not whole_number(bit) or bit < 0 or bit > 7:
            err_msg = "bit should be whole number between 0 and 7"
            Eid = "BitTypeRange"
            raise MarkerError(err_msg, True, Eid)

        # Convert current value to 8 bit string
        cur_bits = format(self._current_value, '#010b')[2:]

        # Set concerning bit dependent on state:
        if state == 'on':
            new_bits = cur_bits[:bit] + '1' + cur_bits[bit + 1:]
        elif state == 'off':
            new_bits = cur_bits[:bit] + '0' + cur_bits[bit + 1:]
        else:
            err_msg = "set_bit state can only be 'on' or 'off'"
            Eid = "BitState"
            raise MarkerError(err_msg, True, Eid)

        # Convert 8 bit string to int and set_value:
        value = int(new_bits, 2)
        self.set_value(value)

    def gen_marker_table(self):
        """Generates marker tables.

        Returns: Three dataframes:
                  - marker dataframe
                        This dataframe has, in chronological order, the marker value, its start and end time, duration
                        and occurrence. The end time and duration are infinite if the current value is non-zero (the
                        current marker has not yet ended).
                  - summary dataframe
                        The summary dataframe has a list of all unique values and how many times they were sent (total
                        occurrences).
                  - error dataframe
                        The error dataframe has a list of all non-fatal errors and their times.
        """

        set_value_df = pandas.DataFrame(self.set_value_list)

        # Assumes that the first value is always set to 0 at init.
        assert set_value_df['value'].iloc[0] == 0

        # init
        last_value = None
        marker_counter = 0
        df_cols = ['value', 'start_time_ms', 'end_time_ms', 'duration_ms', 'occurrence']
        marker_df = pandas.DataFrame(columns=df_cols)

        # Get marker start and end time
        # - The marker start is defined as marker value change from zero to non-zero or from non-zero to non-zero
        # - The marker end is defined as a marker value change from non-zero to zero or from non-zero to non-zero
        for index in set_value_df.index:
            cur_value = set_value_df.at[index, 'value']
            cur_time = set_value_df.at[index, 'time_ms']
            # Value changes
            if cur_value != last_value:
                # Value changed to 0 and it is not the first value
                if cur_value == 0 and last_value is not None:
                    # end marker
                    marker_df.at[marker_counter, 'end_time_ms'] = cur_time
                    marker_counter += 1

                # Value changed from 0 to non-zero
                elif cur_value != 0 and last_value == 0:
                    # start marker:
                    marker_df.at[marker_counter, 'value'] = cur_value
                    marker_df.at[marker_counter, 'start_time_ms'] = cur_time

                # Value changed from non-zero to non-zero
                elif cur_value != 0 and last_value != 0:
                    # end marker:
                    marker_df.at[marker_counter, 'end_time_ms'] = cur_time
                    marker_counter += 1

                    # start marker:
                    marker_df.at[marker_counter, 'value'] = cur_value
                    marker_df.at[marker_counter, 'start_time_ms'] = cur_time

            last_value = cur_value

        # When the last marker was a non-zero value, set end time to infinite
        if pandas.isna(marker_df["end_time_ms"].values[-1]):
            marker_df["end_time_ms"].values[-1] = float('inf')

        # Convert start and end time to seconds:
        marker_df["start_time_s"] = marker_df["start_time_ms"] / 1000
        marker_df["end_time_s"] = marker_df["end_time_ms"] / 1000

        # Save duration
        marker_df["duration_ms"] = marker_df["end_time_ms"] - marker_df["start_time_ms"]
        # Remove ms columns
        marker_df.drop(['end_time_ms', 'start_time_ms'], axis=1, inplace=True)

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

        # Create summary table
        summary_df = marker_df.loc[:, ('value', 'occurrence')]
        summary_df["mean_duration"] = None
        summary_df["min_duration"] = None
        summary_df["max_duration"] = None
        summary_df["total_duration"] = None
        for index, val in enumerate(summary_df.value):
            all_durations = marker_df[summary_df["value"] == val].duration_ms.tolist()
            summary_df.loc[index, 'mean_duration'] = (sum(all_durations)) / len(all_durations)
            summary_df.loc[index, 'min_duration'] = min(all_durations)
            summary_df.loc[index, 'max_duration'] = max(all_durations)
            summary_df.loc[index, 'total_duration'] = sum(all_durations)

        summary_df = summary_df.drop_duplicates(subset=['value'], keep='last')

        # Create error table
        error_df = pandas.DataFrame(self.error_list)
        if len(self.error_list) > 0:
            error_df["time_s"] = error_df["time_ms"] / 1000
            error_df.drop("time_ms", axis=1, inplace=True)

        return marker_df, summary_df, error_df

    def print_marker_table(self):
        """Prints marker table, summary table and error table, generated with gen_marker_table."""

        # Import pretty table when necessary:
        from prettytable import PrettyTable

        # Generate most up-to-date marker table
        marker_df, summary_df, error_df = self.gen_marker_table()

        # Create pretty tables:
        summary_table = PrettyTable()
        summary_table.title = "Summary table"
        summary_table.field_names = list(summary_df.columns)
        for row in summary_df.itertuples():
            summary_table.add_row(row[1:])

        marker_table = PrettyTable()
        marker_table.title = "Marker table"
        marker_table.field_names = list(marker_df.columns)
        for row in marker_df.itertuples():
            marker_table.add_row(row[1:])

        error_table = PrettyTable()
        error_table.title = "Error table"
        error_table.field_names = list(error_df.columns)
        for row in error_df.itertuples():
            error_table.add_row(row[1:])

        # Print tables
        print(error_table)
        print(summary_table)
        print(marker_table)

    def save_marker_table(self, filename="", location=os.getcwd(), more_info=""):
        """Saves the marker table, summary table and error table in one TSV file.

        Args:
            filename: The filename the .tsv should have
            location: The location where the marker table should be saved
            more_info: More information can be added to the header. Should be a dict with key-value pairs.
        Raises:
            MarkerManagerError: When input is not correct or the location has no writing permission.
        """

        # Check input
        if not isinstance(filename, str):
            err_msg = f'filename should be string, got type {type(filename)}'
            raise MarkerManagerError(err_msg)

        if more_info != "" and not isinstance(more_info, dict):
            err_msg = f"more_info should be dict, got {type(more_info)}"
            raise MarkerManagerError(err_msg)

        # Check if location has writing permission
        if not os.access(location, os.W_OK):
            err_msg = f'No writing permissions in {location}. Marker table cannot be saved.'
            raise MarkerManagerError(err_msg)

        # Generate most up-to-date marker table
        marker_df, summary_df, error_df = self.gen_marker_table()

        # Get cur date and time
        cur_date_time = datetime.datetime.now()

        if filename == "":
            # When no filename has been specified, create filename with date
            date_n = cur_date_time.strftime("%Y%m%d%H%M%S")
            fn = date_n + '_marker_table.tsv'
        else:
            fn = filename + '.tsv'

        full_fn = location + '\\' + fn

        # Get date
        date_str = cur_date_time.strftime("%Y-%m-%d %H:%M:%S")

        # Convert data to series
        summary_df.squeeze()
        marker_df.squeeze()
        error_df.squeeze()

        # Write data to tsv file
        with open(full_fn, 'w', newline='') as file_out:
            writer = csv.writer(file_out, delimiter='\t')
            writer.writerow(['Date: ' + date_str])
            writer.writerow(['Library version: ' + LIB_VERSION])
            writer.writerow(['Device: ' + self.device_properties.get('Device')])
            writer.writerow(['Device serialno: ' + self.device_properties.get('Serialno')])
            writer.writerow(['Device version: ' + self.device_properties.get('Version')])
            if isinstance(more_info, dict):
                for key, value in more_info.items():
                    writer.writerow([key + ': ' + str(value)])
            writer.writerow('')
            writer.writerow(['#Summary#'])
            writer.writerow(summary_df.head())
            writer.writerows(summary_df.values)
            writer.writerow('')
            writer.writerow(['#Markers#'])
            writer.writerow(marker_df.head())
            writer.writerows(marker_df.values)
            writer.writerow('')
            writer.writerow(['#Errors#'])
            writer.writerow(error_df.head())
            writer.writerows(error_df.values)


class MarkerError(Exception):
    """"Error sending a marker"""

    def __init__(self, message, is_fatal, Eid):
        super().__init__(message)
        self.message = message
        self.is_fatal = is_fatal
        self.id = Eid


class MarkerManagerError(Exception):
    """Error involving the MarkerManager"""

    def __init__(self, message, Eid):
        super().__init__(message)
        self.message = message
        self.id = Eid


class FindDeviceError(Exception):
    """Error finding the device"""

    def __init__(self, message, Eid):
        super().__init__(message)
        self.message = message
        self.id = Eid


class SerialError(Exception):
    """Error involving the serial device"""

    def __init__(self, message, Eid):
        super().__init__(message)
        self.message = message
        self.id = Eid


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
         {"Version":"HW1:SW1.1","Serialno":"S01234","Device":"UsbParMarker"}
        """
        pass

    @abstractmethod
    def _set_value(self, value):
        """Sets the value of the marker device. The MarkerManager.set_value
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
    """Class for generic Leiden Univ serial device (e.g. Eva, UsbParMarker)

    Attributes:
        _device_address: the serial device address (e.g. COM1)
        _device_properties: the device properties (e.g.
            {"Version":"HW1:SW1.1","Serialno":"S01234","Device":"UsbParMarker"})
        serial_device = the serial device

    """

    def __init__(self, device_address):

        # Save attribs:
        self._device_address = device_address

        if not device_address == FAKE_ADDRESS:

            # Open device:
            self.open_serial_device()
            timing.delay(100)

            # Example: {"Version":"HW1:SW1.2","Serialno":"S01234","Device":"UsbParMar"}
            properties = self.get_info()

            if properties == "":
                err_msg = "Serial device did not respond."
                Eid = "NoResponse"
                raise SerialError(err_msg, Eid)

            if "Serialno" not in properties:
                err_msg = "Serialno missing."
                Eid = "NoSerialNo"
                raise SerialError(err_msg, Eid)

        # return fake device
        else:
            properties = {"Version": "0000000",
                          "Serialno": "0000000",
                          "Device": FAKE_DEVICE}

        self._device_properties = properties

    @property
    def device_address(self):
        """Returns device address."""
        return self._device_address

    @property
    def device_properties(self):
        """Returns device properties."""
        return self._device_properties

    def _set_value(self, value):
        """Sets the value of the serial device."""
        if not self.is_fake:
            value_byte = value.to_bytes(1, 'big')
            self.serial_device.write(value_byte)

    def _close(self):
        """Closes the serial connection."""
        if not self.is_fake:
            self.serial_device.close()

    def open_serial_device(self, params=None):
        """Opens serial device with specified parameters."""

        # Opens in data mode by default
        if params is None:
            params = {"baudrate": 115200, "bytesize": 8,
                      "parity": 'N', "stopbits": 1,
                      "timeout": 2}

        if not self.is_fake:
            # Create serial device.
            try:
                self.serial_device = serial.Serial(self._device_address, **params)
            except:
                err_msg = "Could not open serial device"
                Eid = "NoSerialDeviceMade"
                raise SerialError(err_msg, Eid)

    def command_mode(self):
        command_params = {"baudrate": 4800, "bytesize": 8,
                          "parity": 'N', "stopbits": 1,
                          "timeout": 2}
        self.open_serial_device(params=command_params)

    def send_command(self, command):
        """Sends command to serial device."""

        if self.is_fake:
            err_msg = "Fake device is not allowed to send commands."
            Eid = "FakeDeviceError"
            raise SerialError(err_msg, Eid)

        else:
            # Close device and open in command mode
            self.serial_device.close()
            timing.delay(100)

            self.command_mode()
            timing.delay(100)

            if not self.serial_device.baudrate == 4800:
                err_msg = "Serial device not in command mode."
                Eid = "BaudrateNotCommandmode"
                raise SerialError(err_msg, Eid)
            if not self.serial_device.is_open:
                err_msg = "Serial device not open."
                Eid = "SerialDeviceClosed"
                raise SerialError(err_msg, Eid)
            if not type(command) == str:
                err_msg = "Command should be a string."
                Eid = "CommandType"
                raise SerialError(err_msg, Eid)
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

                # Close device
                self.serial_device.close()
                timing.delay(100)

                # Open device again (in data mode by default)
                self.open_serial_device()
                timing.delay(100)

                return decoded_data

    def get_info(self):
        """Get info from serial device."""
        if not self.is_fake:
            info = self.send_command('V')
        else:
            info = {"Version": "0000000",
                    "Serialno": "0000000",
                    "Device": FAKE_DEVICE}
        return info

    def ping(self):
        """Ping serial device."""
        if not self.is_fake:
            ping_answer = self.send_command('P')
        else:
            ping_answer = "pong, " + FAKE_DEVICE
        return ping_answer

    def get_hw_version(self):
        """Get hardware version."""
        if not self.is_fake:
            properties = self.device_properties
            version = properties.get('Version')
            hw_version = re.search('HW(.*):', version)
            hw_version = hw_version.group(1)
        else:
            hw_version = 0
        return hw_version

    def get_sw_version(self):
        """Get software version."""
        if not self.is_fake:
            properties = self.device_properties
            version = properties.get('Version')
            sw_version = re.search('SW(.*)', version)
            sw_version = sw_version.group(1)
        else:
            sw_version = 0
        return sw_version


class UsbParMarker(SerialDevice):
    """Class for the UsbParMarker."""

    def leds_on(self):
        """Turns led lights on"""
        sw_version = self.get_sw_version()
        if float(sw_version) < 1.3:
            warnings.warn('Check firmware version, could not turn on leds')
            leds_on_answer = 'LedsOff'
        else:
            leds_on_answer = self.send_command('L')
        return leds_on_answer

    def leds_off(self):
        """Turns led lights on"""
        sw_version = self.get_sw_version()
        if float(sw_version) < 1.3:
            warnings.warn('Check firmware version, could not turn off leds')
            leds_off_answer = 'LedsOff'
        else:
            leds_off_answer = self.send_command('O')
        return leds_off_answer


class Eva(SerialDevice):
    """Class for Eva device."""

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


# Helper functions:
def whole_number(value):
    """Evaluate whether value is whole number."""
    try:
        return isinstance(value, int) or \
               (isinstance(value, float) and value.is_integer())
    except:
        raise (MarkerManagerError('error whole number'))


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
    """Finds the address of the device.

    If UsbParMarker mode or Eva mode, find the COM port. If a device_name was specified, check that the
    serial number matches.
    Throw error if multiple COM candidates are available.

    However, if fallback_to_fake is true, don't throw error, just returns the address that toggles faking.

    Args:
        device_type:
            string of device type, can only contain one of the devices as defined in available_devices
        serial_no:
            string containing the serial number of the device
        com_port:
            com port address of the device
        fallback_to_fake:
            bool indicating whether a FAKE device should be used when no device can be found

    Returns:
            info:
                device: dict containing 'Version', 'Serialno', 'Device'['device']
                com_port: the com port address

    Raises:
        FindDeviceError: when fallback_to_fake == False, the FindDeviceError is raised when no device can be found.

    """

    # Check device type
    if device_type not in available_devices and device_type != '':
        Eid = "UnsupportedDevice"
        raise FindDeviceError(f"Only {available_devices} supported.", Eid)

    info = {}
    temp_info = {}

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
    port_hit = False
    device_hit = []
    connection_error = False
    connection_error_port = ''
    connection_error_info = ''
    port_list = []
    connected_port_list = []
    port_n = 0

    # Loop through ports
    ports_listed = comports()
    for port, desc, hwid in ports_listed:

        # Check filters:
        port_matches_request = re.match(com_filters['port_regex'], port) is not None
        com_dev_desc_matches = re.match(com_filters['com_dev_desc_regex'], desc) is not None
        com_dev_hwid_matches = re.match(com_filters['com_dev_hwid_regex'], hwid) is not None

        if not (port_matches_request and com_dev_desc_matches and com_dev_hwid_matches):
            continue

        # save ports in list
        port_list.append(port)

    if len(port_list) != 0:

        # At least one port with correct port, desc and hwid found
        port_hit = True
        port_n += 1

        # Loop through ports and check devices
        for port in port_list:

            try:
                # Create general serial device to obtain device info
                cur_device = SerialDevice(port)
                cur_device._close()
            except:
                try:
                    cur_device._close()
                except:
                    pass
                connection_error = True
                connection_error_port = port
                connection_error_info = sys.exc_info()[1]
                continue

            temp_info["device"] = cur_device.device_properties

            # Check filter
            device_matches_request = re.match(com_filters['device_regex'], temp_info['device']['Device']) is not None
            serial_matches_request = re.match(com_filters['sn_regex'], temp_info['device']['Serialno']) is not None

            # save info when a match was found
            if device_matches_request and serial_matches_request:
                info["device"] = cur_device.device_properties
                device_hit.append(True)
                connected_port_list.append(port)

    # Checks:
    try:

        # Check if any port was found
        if not port_hit:
            err_msg = "No device matched the specified COM address."
            Eid = "NoComMatch"
            raise FindDeviceError(err_msg, Eid)

        # Check if one device was found
        if not device_hit:
            err_msg = "No device matched the specified device type and/or serial number."
            Eid = "NoDeviceMatch"
            raise FindDeviceError(err_msg, Eid)
        else:
            if device_hit.count(True) > 1:
                err_msg = "Multiple matching devices found."
                Eid = "MultipleConnections"
                raise FindDeviceError(err_msg, Eid)

            else:
                device_hit_index = device_hit.index(True)
                info["com_port"] = connected_port_list[device_hit_index]

        # Check if connection error happened
        if connection_error:
            err_msg = f'Could not connect to "{connection_error_port}" because: {connection_error_info}'
            Eid = "NoConnection"
            raise FindDeviceError(err_msg, Eid)

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
