# Example of using the marker_management module.

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
