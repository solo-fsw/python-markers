

# Example of using the markers_core module and the UsbParMar gadget.

# Add note about OpenSesame prepare vs run.


import marker_management as mark
import time


# Find the address and make the marker object:
marker_device_type = 'UsbParMar'
device_info = mark.find_com_address(device_type='UsbParMar')
marker_address = device_info['com_port']
marker_manager = mark.MarkerManager(marker_device_type, marker_address, fallback_to_fake=False)

# The marker instance will fallback to using a fake marker device if a suitable one could not be found,
# warn user of this:
# if marker_manager.is_fake():
#     pass

marker_manager.set_value(3)
time.sleep(0.1)
marker_manager.set_value(0)
time.sleep(0.1)
marker_manager.set_value(3)
time.sleep(0.1)
marker_manager.set_value(0)
time.sleep(0.1)
marker_manager.set_value(2)
time.sleep(0.1)
marker_manager.set_value(0)
time.sleep(0.1)

marker_manager.close()

marker_manager.gen_marker_table()
