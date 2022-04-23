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
import serial.tools.list_ports as serialport
import sys
import pandas as pd
import serial
import plotly.figure_factory as ff

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
            param must be a string indicating its name (e.g. LPT1)
        EVA:

    """
    
    def __init__(self, device_type, device_address, report_marker_errors = True, time_function_us = lambda : timing.micros(), **kwargs):
        """Builds the marker class, and the device interface class used to talk to the device."""


        # Note, add ability to forward KW arguments to the DeviceInterface constructor.

        # Throw error if arguments are incorrect, or if a class with same type and address already exists.

        # Instantiate the correct DeviceInterface subclass:
        self.device_interface = type(device_type, 
              (object,), 
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
        '''
            Sets value of the marker and adds the entry to the marker list.
            Validates the value of the passed marker when report_marker_errors = True.

            :raises RunTimeError:
                When concurrent markers are passed in a very short time interval.

            :raises ValueError:
                When marker value is out-of-range(0 - 255).

            :prompts:
                When markers aren't recognized (i.e. marker value = 0).
                When double markers are passed.
        '''

        # Validate the passed marker:
        while self.report_marker_errors == True:
            if (self._time_function_us() - self.marker_list[-1]['onset']) < self.concurrent_marker_threshold_ms:    # TODO: needs better implementation
                raise RuntimeError("Concurrent markers were passed too swiftly, the concurrent marker threshold is", self.concurrent_marker_threshold_ms, "ms.")
            elif value == self._current_value:
                print("Double Markers returned.")

        # Regardless of report_marker_errors, throw error is marker is outside of range (0 - 255).
        if value > 255 or value < 0:
            raise ValueError("Marker value out of range (0 - 255).")
        elif value == 0:
            print("No marker registered since passed value is: ", value)

        # Set value of the marker:
        self.device_interface._set_value(value)
        self._current_value = value

        # Calculate occurence:
        occurence = sum(1 for entry in self.marker_list[:]['value'] if entry == value)

        # Calculate the marker time relative to the self.start_time, and log the marker:
        marker_time = self._time_function_us()
        duration = marker_time - self._start_time
        offset_time = marker_time + duration

        # Create a list of dictionaries containing marker data:
        self.marker_list.append({'value': value, 'onset': marker_time, 'offset': offset_time, 'duration': duration, 'occurence': occurence})


    
    def is_fake(self):
        return self.device_interface.is_fake()

    def send_marker_pulse(self, value, duration_ms = 100):
        '''
            Sends a short marker pulse.
        '''
        # TODO: What is a marker pulse
        pass


    def set_bits(self, bits):
        """Generic function for toggling bits.

        E.g. markers.set_bits('00000001') sets all bits except the last to LOW.
        Use EVA endianess convention.

        """
        # TODO: Is it supposed to be random?
        # Calculate the value from the bits, call set_value().
        value = 9999
        self.set_value(value)


    def set_bit(self, bit, state):
        """Toggle a single bit.

        Toggle a single bit, leave other bits intact. Use EVA bit numbering convention.

        """

        #TODO: Which bit? Random?
        value = 9999
        self.set_value(value)


    def gen_marker_table(self, data_list):
        '''Returns a table (e.g. dataframe) with a list of all markers:

        The table should have, in chronological order, the marker value, and its start and end time, duration.
        The end time and duration should be infinite if the current value is non-zero (the current marker has not yet ended).

        A table with the summaries of all markers should also be returned, it should have a list of all the unique values, and their how many times they were sent.
        '''
        log_table = pd.DataFrame(data = data_list)
        self.log_table = log_table

        # Summaries table:
        summary = log_table
        summary = summary[['value', 'occurence']]
        summary = summary.drop_duplicates(subset = ['value'], keep = 'last')

        self.summaries = summary

        return log_table, summary


    def print_marker_table(self):
        '''
            Pretty prints the gen_marker_table data.
        '''
        # Get Marker table:
        data = self.gen_marker_table()[0]

        # Initialize a figure:
        fig = ff.create_table(data)
        
        # Print the table:
        fig.show()

        # TODO: Plot the markers as a digital signal

    
    def save_marker_table(self):
        '''
            Saves the gen_marker_table data as TSV file(s).
        '''
        
        # Get Marker table:
        data = self.gen_marker_table()[0]

        # Save as TSV file:
        data.to_csv('marker_file.tsv', sep = '\n') 


class DeviceInterface(ABC):
    """This defines the interface for connecting to a device.

    Device-type specific classes that manage the connection to a marker device
    must subclass this class and implement its abstract methods.

    Note, the subclass constructors must throw errors if the specified parameters cannot be resolved.
    E.g., no device with the specified address exist, or it it is not of the expected type.

    """

    # forward KW arguments from MarkerManager abstract class:
    def __init__(self, **kwargs):
        self.device_address = kwargs.pop('device_address', self.device_address())
        self.device_properties = kwargs.pop('device_properties', self.device_properties())
        super().__init__(**kwargs)
    
    @property
    @abstractmethod
    def device_address(self):
        """Returns the address of the device."""
        ports = serial.tools.list_ports.comports()

        # init:
        port_names = []

        # Loop through ports and collect port names:
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
            port_names.append(port)

        # Retrieving the actual device names:
        for port in port_names:
            # while port opens and responds, it is the corerct port
            while port.open()


    @property
    @abstractmethod
    def device_properties(self, port_name, baudrate):
        """Returns the properties of the device (firmware version, name, etc.)."""
        properties = []

        while True:
            ser = serial.Serial(port = port_name, baudrate = baudrate)
        # For props, use list with one elements per prop, with each element having the fields: name, label, value. 

        #  {"name" : "firmware_version", "label" : "Firmware version", "value": "0.4.1"}
        pass


    @abstractmethod
    def _set_value(self, value):
        """Sets the value of the marker device. The Markers.set_value should be user by users since it performs generic checks and logs the markers."""
        pass

    
    @abstractmethod
    def _close(self, device_name):
        """Closes the connection to the serial device, if necessary."""
        pass


    @property
    def is_fake(self):
        """Returns a bool indication if the device is faked."""
        return self.device_address == FAKE_ADDRESS


class UsbParMar(DeviceInterface):
    '''
        Class for USB Par Marker devices.
    '''

    def __init__(self, device_address, **kwargs):
        '''
        
            ::params::
                device_address: The COM port address of the connected USB device (eg: COM5, COM6).
        '''
        
        # Init serial device and configure if necessary.
        self.serial_device = serial.Serial(device_address)

        # Save attribs:
        self._device_address = device_address

        # Fetch and save device properties.
        self._device_properties = []
        super().__init__(**kwargs)

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


class EVA(DeviceInterface):
    '''
        Class for EVA device.

        :notes:
            active mode: Biopac acts as output for markers. (deault)
            passive mode: Biopac acts as input for markers.
            To put the device in data mode: Open the COM port with configurations as - 115200 baud, 8 bits, none parity, 1 stop bit (115200,8,N,1).
            To switch to command mode(CMD LED turns ON): Open the COM port with the configurations as - 4800,8,N,1.
            Command mode commands (case sensistive commands):
                V - version gives info about the device
                S - puts the device in passive mode
                A - puts the device in active mode
                P - ping thr device to check for activity
 
    '''
    def __init__(self, device_address, **kwargs):
        
        self._serial_device = 9999

        self._device_address = device_address

        self.device_properties = []
        super().__init__(**kwargs)

# Below are helper functions:

def find_address(device_type, device_name = '', fallback_to_fake = False):
    """ Finds the address of the device.

    If LPT mode, return the address. Throw error if no or multiple LPT addresses are available.

    If UsbParMar mode, find the COM port. If a device_name was specified, check that it (probably a serial number) matches.
    Throw error if multiple COM candidates are available. Empty device name uses any.

    etc.

    However, if fallback_to_fake is true, don't throw error, just returns the address that toggles faking.  
    TODO: Check device_name matching. Q: what is the device_name?

    """
    count = 0    # counter variable for detecting whether requested device is connected or not

    if device_type == UsbParMar:
        available_com_ports = com_ports()
        if len(available_com_ports) == 1:
            s_device = serial.Serial(available_com_ports)
            if s_device.isOpen():
                if device_name != '':
                    if device_name != s_device._port_handle:
                        count += 1
                    pass
                address = s_device.port
                s_device.close()
        else:
            for port in available_com_ports:
                s_device = serial.Serial(port)
                if s_device.isOpen():
                    address = s_device.port
                    s_device.close()

        if count != 0:
            raise Exception("Connected device(s) did not match the requested device.")
            
    elif device_type == LPT:
        address = 00     # TODO: access parallel port by calling helper function lpt_ports() 

    # Note, use the UsbParMar class directly to connect to available COM devices and fetch their properties.

    # Fake address is passed:
    if fallback_to_fake == True:
        address = FAKE_ADDRESS
    
    address = ''
    return address

# configure system and ports:
def com_ports():
    '''
    Checks for FSW devices connected via a COM port on the system.

        ::params::
            port_address: the COM address (eg: COM4). 
            s_device: active serial device object.
            desired_names: a list of device names(/descriptions) as required. 

        :raises EnvironmentError:
            On unsupported or unknown platforms.
        :raises ImportError:
            When no COM ports are deteced.
        :raises Exception:
            When multiple devices are connected.
        :returns:
            A list of the active FSW devices connected via COM ports.
    '''
    # Detect all available COM ports and for OS compatibility:
    if sys.platform.startswith('win'):
        com_ports = serialport.comports()
    else:
        raise EnvironmentError('Unsupported platform deteced.')

    device_count = 0
    port_name = []
    desired_names = ['USB Serial Device', 'Ardruino', 'Lombardo']

    for port in com_ports:
        try:
            if (desired_names[0] or desired_names[1] or desired_names[2]) in port.description:
                s_device = serial.Serial(port.device)
                if s_device.isOpen():
                    device_count += 1
                    port_name.append(s_device.port)
                    s_device.close()
        except (OSError, serial.SerialException):
            pass
    
    # Check for active devices and throw errors accordingly:
    if device_count == 0:
        raise ImportError("Device not connected. No active COM ports were recognized.")
    elif device_count > 1:
        raise Exception("Multiple devices detected. Found", device_count, "active COM ports.")

    return port_name


def lpt_ports():
    '''
        Access the LPT parallel port using:
            1) psychopy.parallel.ParallelPort()
            2) parallel
            3) wmi
    '''
    pass