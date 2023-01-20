# Marker Management # 
The module marker_management.py is meant for sending markers using the various digital output devices used at the FSW.

## Background information ##
> *The background information provided here is an excerpt from the SOLO wiki on markers. For more information on markers and their usage, follow the link to the SOLO wiki provided under __References__.*
 
Measuring physiological signals, such as electrocardiography (ECG), skin conductance, blood pressure, respiration, etc. is common practice within different disciplines of social and behavioral sciences. 
Usually during an experiment, a participant performs a (computer) task and physiological signals are measured simultaneously.
In order to analyze the physiological signals, it is necessary that the physiological signals are segmented into meaningful segments. These segments are usually created based on certain moments in the task.
Markers (which are managed by this python module) signal the occurrence of these moments in an experiment.

Markers are sent by stimulus presentation software such as OpenSesame or E-Prime, from the stimulus pc, via a marker cable (LPT, UsbParMarker, EVA) to the physiology hardware (e.g. Biopac or BioSemi). Markers are recorded as a continuous signal and this signal typically looks as follows:

![Example of a marker signal over time](/images/marker-signal-example.png)

These markers have the following properties:
- **A value (positive non-zero integer):** This is the value or height of the marker.
- **Start and end:** The timepoint at which the marker assumes its value is referred to as the start of a marker. When the marker releases that value is called the end.
- **Duration:** The time between the start and end of a marker is the duration of the marker.
- **Occurrence (number):** The same marker value can be sent multiple times, thus each marker has an occurrence.

At the FSW, markers are typically sent in an 8-bit format using a parallel port. Since the parallel port is no longer implemented in newer devices SOLO developed two devices capable of replacing the parallel port by converting binary signals to decimal signals and thereby facilitating a transition from the parallel port to a usb port. These devices are called _UsbParMarker_ and _Eva_. The marker_management module provides the software necesarry for this conversion.

## Getting started ##


## Using Submodules ##
> *The information provided here is a summary of the information provided by github. For more information on git submodules, follow the link to the git documentation provided under __References__.*

It is strongly recommended to add this repository as a git submodule to your project. This can be done as follows:
1. Adding the submodule
    - To use the a submodule in your repository, first add it using the `git submodule` command:
```
git submodule add <https://github.com/solo-fsw/python-markers.git> marker_management
``` 
1. Update the submodule
    - After adding the submodule to your repository, update it to the latest commit using:
```
git submodule update
```

Using this repository as a git submodule has the following advantages:
- The code will be version controlled, allowing you to track changes in this repository over time
- The code will be easy to set up and use
- Using the submodule allows you to keep your repository light, only including the submodule reference instead of the whole repository

## Examples ##
> *The python example provided below is also available as a python file in the repository (example.py). In the example extra comments were added for additional clarity.*
> 
An example of using the library in python is shown below.
```python
import marker_management as mark
import time
import utils.GS_timing as timing

# Find the address and make the marker_manager object:
marker_device_type = 'Eva'
device_info = mark.find_device(device_type=marker_device_type, fallback_to_fake=True)
marker_address = device_info['com_port']
marker_manager = mark.MarkerManager(marker_device_type, marker_address, crash_on_marker_errors=False)

# Print the address and properties
print(marker_manager.device_address)
print(marker_manager.device_properties)

# Send markers
# (As an example, sending the marker sequence below will result
# in two errors that are saved in the error table)
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

# Generate marker tables, save and print them
marker_table, marker_summary, errors = marker_manager.gen_marker_table()
marker_manager.save_marker_table()
marker_manager.print_marker_table()

# Close device
marker_manager.close()
```
This example shows how python code can be used to create a connection with the device, how to send markers through the device and how to subsequently create a log containing information about the sent markers.


For OpenSesame, the marker_manager module has been implemented in a plugin, which can be found [here](https://github.com/solo-fsw/opensesame_plugin_markers).


## References ##

- [SOLO wiki on markers](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/)
- [OpenSesame Markers plugin](https://github.com/solo-fsw/opensesame_plugin_markers)
- [SOLO wiki on the UsbParMarker](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/UsbParMarker/)
- [UsbParMarker github page](https://github.com/solo-fsw/UsbParMarker)
- [SOLO wiki on Eva](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/EVA/)
- [Eva github page](https://github.com/solo-fsw/Eva)
- [Git documentation on submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)