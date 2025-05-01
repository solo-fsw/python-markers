""" Sending Markers Example

This script contains an explanation and examples on how to use the marker_management module.

"""

# Import required modules for current example:
import python_markers.marker_management as mark
import python_markers.GS_timing as timing
import os

""" Finding the Marker Device

    The find_device function is a helper function of the marker_management module and will try 
    to find the marker device (when attached to the PC). It takes the following arguments:
        - device_type: The device_type can be 'UsbParMarker' or 'Eva'. When the device type is not 
            specified, any marker device that is attached to the PC will be found.
        - serial_no and com_port: Optionally, the serial number or COM port can be specified when 
            a specific device needs to be found. This can be useful when multiple of the same marker 
            devices are connected to one PC.
        - fallback_to_fake: When fallback_to_fake is set to True, the device_info of a fake device 
            will be returned when the marker device cannot be found. When fallback_to_fake is set to 
            False, an error will be thrown when the marker device cannot be found.

    The find_device function will output relevant device information (device_info), which contains 
    the following: 
        - com_port: The COM port address the marker device is connected to. This address is necessary to 
            use the marker_manager.
        - device: Information about the device:
            - Version: The hardware and software version of the device.
            - Serialno: The serial number of the device.
            - Device: The device type (UsbParMarker or Eva).

"""

# In the current example, the device_info of any marker device attached to the PC is attempted 
# to be found. When no marker device is found, an error will be thrown.
device_info = mark.find_device(device_type='', serial_no='', com_port='', fallback_to_fake=False)

# To check, the device_info is printed:
print('COM port address: ' + device_info['com_port'])
print('Device version: ' + device_info['device']['Version'])
print('Device serial number: ' + device_info['device']['Serialno'])
print('Device type: ' + device_info['device']['Device'])


""" Initializing the MarkerManager

    Initializing the MarkerManager class will create a marker_manager object, which can then be 
    used to send markers. 

    The following arguments are required:
        - marker_device_type: The device type can be 'UsbParMarker' or 'Eva'. 
        - marker_address: The COM port address the marker device is attached to.
        Note that you can set the marker_device_type to 'FAKE DEVICE' and the marker_address to 'FAKE' 
        to create a dummy/fake marker_manager. This  can be used when no actual marker device is attached 
        to the PC.
        - crash_on_marker_errors: When crash_on_marker_errors is set to true, the script will crash when:
            - Double markers are sent: The same marker value is sent twice in a row.
            - Concurrent markers are sent: If a marker was sent less than 10 ms after the previous marker.
            - Marker error: If the marker could not be sent to the marker device for whatever reason.
        When the crash_on_marker_errors is set to false, the script will not crash and the errors are saved 
        in the errors table, which can be obtained with the gen_marker_table method (see below).

    Regardless of the crash_on_marker_errors setting, the script will always crash when the marker is 
    not a whole number or out of the range of 0 - 255.

"""

# Use the device_info that was obtained with the find_device function:
cur_device_type = device_info['device']['Device']
cur_device_address = device_info['com_port']

# Create the marker_manager object. In the current example, the script will not 
# crash when a marker error occurs.
marker_manager = mark.MarkerManager(device_type=cur_device_type, 
                                    device_address=cur_device_address, 
                                    crash_on_marker_errors=False)

# Important device information is saved in the marker_manager after initializing.
# To check, this device information is printed:
print('Device address: ' + marker_manager.device_address)
print('Device version: ' + marker_manager.device_properties['Version'])
print('Device serial number: ' + marker_manager.device_properties['Serialno'])
print('Device type: ' + marker_manager.device_properties['Device'])


""" Sending Markers
    
    The set_value method is used to send markers. The value remains high until a 0 is sent.
    Make sure the marker has an appropriate duration (at least 10 ms is advised).
    The marker value should be a whole number ranging from 0 - 255.

"""
# As an example, sending the marker sequence below will result in two errors that are saved 
# in the error table, namely double markers and concurrent markers. Because we set crash_on_marker_errors 
# to False in the marker_manager, the script will not crash, but does save the errors.
marker_manager.set_value(255)
timing.delay(100)
marker_manager.set_value(0)
timing.delay(1000)
marker_manager.set_value(3)
timing.delay(100)
marker_manager.set_value(0)
timing.delay(1000)
marker_manager.set_value(3)
timing.delay(100)
marker_manager.set_value(0)
timing.delay(1000)
marker_manager.set_value(2)
timing.delay(100)
marker_manager.set_value(2)
timing.delay(5)
marker_manager.set_value(0)
timing.delay(1000)


""" Generating Marker Tables
    
    After sending the desired markers, marker tables can be generated, saved and/or printed.
    
    The gen_marker_table method is used to create data frames with marker information. 
    This method does not take any arguments. The following data frames can be created:
        - marker_table: This is a dataframe that contains, in chronological order, 
            the marker value, its start and end time, duration and occurrence. The 
            end time and duration are infinite if the current value is non-zero (the
            current marker has not yet ended). 
        - marker_summary: The summary dataframe has a list of all unique values and how many 
            times they were sent (total occurrences).
        - errors: The error dataframe has a list of all non-fatal errors and their times.

    The marker tables can be saved in a tsv file with the save_marker_table method. This method
    can take the following arguments:
        - filename: The filename of the tsv file. When left unspecified, the filename will be the current
            date and time plus "_marker_table.tsv". 
        - location: The location where the tsv file should be saved. Make sure that you have
            writing permissions in this location. When left unspecified, the current working directory is used.  
        - more_info: More information that will be placed in the header of the tsv file. This should be 
            a dict with key-value pairs.

    The marker tables can also be printed with the print_marker_table method. This method does
    not take any arguments.
        
"""

# Generate marker tables, save them in the current directory, and print them.
marker_table, marker_summary, errors = marker_manager.gen_marker_table()
marker_manager.save_marker_table(filename='', location=os.getcwd(), more_info='')
marker_manager.print_marker_table()


""" Closing the Marker Device
    
    Use the close method to close the marker device. 
    This needs to be done at the end of the experiment.

"""

# Close the device.
marker_manager.close()
