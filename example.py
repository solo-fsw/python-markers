

# Example of using the markers_core module and the UsbParMar gadget.

# Add note about OpenSesame prepare vs run.


import marker_management as mark
import time


# Find the address and make the marker object:
marker_device_type = 'UsbParMar'
marker_address = 'COM3'
marker_manager = mark.MarkerManager(marker_device_type, marker_address, fallback_to_fake=False)
print(marker_manager.device_properties)
print(marker_manager.device_type)

# The marker instance will fallback to using a fake marker device if a suitable one could not be found,
# warn user of this:
# if marker_manager.is_fake():
#     pass

# Send a marker:
marker_manager.set_value(200)

# Do something else here, something that takes more than 10 ms.
time.sleep(2)

# Reset marker:
marker_manager.set_value(0)


# Do something else here, something that takes more than 10 ms.
time.sleep(0.1)

marker_manager.close()