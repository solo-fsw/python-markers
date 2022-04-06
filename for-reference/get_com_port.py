from init_and_close_serial_device import init_serial_device
from init_and_close_serial_device import close_serial_device


def get_com_port(device_name):
    # Finds the com port address of UsbParMarker or SignalGenerator
    # Note, to find the com port address of the SignalGenerator, the signal_generator module is necessary
    # and to find the com port address of the UsbParMarker, the usb_par_marker module is necessary

    # Input: device_name = 'UsbParMarker' or 'SignalGenerator'
    # Output: com_ports = the com port address(es) to which the serial device is connected.

    # Get serial port addresses
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()

    # init:
    port_names = []
    com_ports = []

    # Loop through ports and collect port names:
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))
        port_names.append(port)

    # when devices are found, get their actual name
    if len(port_names) != 0:

        if device_name == 'UsbParMarker':

            from usb_par_marker import send_command

            # loop through ports
            for port in port_names:

                # Open port with baudrate of 4800 to be able to get the name of the device:
                ser_device = init_serial_device(port, 4800, 1)

                if type(ser_device) == str:
                    continue

                # Ping the device:
                data = send_command(ser_device, 'P')
                print('data: ' + str(data))

                # Check if UsbParMarker is found:
                if 'UsbParMarker' in data:
                    com_ports.append(port)
                    print('UsbParMarker found')

                # close port
                close_serial_device(ser_device)

        elif device_name == 'SignalGenerator':

            # import module signal_generator
            from signal_generator import send_pulse_train

            # loop through ports
            for port in port_names:

                # open port wth baudrate 4800 (note that the signal_generator uses a baudrate of 115200 normally)
                ser_device = init_serial_device(port, 4800, 2)

                if type(ser_device) == str:
                    continue

                # send pulse and get data
                data = send_pulse_train(ser_device, current=0, ton=1, toff=1, repeat=1)
                print('data: ' + str(data))
                # If the data contains 'Serial', 'Ver' and 'samples' it is assumed we are dealing with a SignalGenerator
                if 'Serial' in data and 'Ver' in data and 'samples':
                    com_ports.append(port)

                # close port
                close_serial_device(ser_device)

    if len(com_ports) == 0:
        com_ports = 'FAKECOM'
    elif len(com_ports) == 1:
        com_ports = com_ports[0]

    return com_ports


# # Test functions:
# com_ports_usbparmar = get_com_port('UsbParMarker')
# print('com_ports_usbparmar: ' + str(com_ports_usbparmar))
# com_ports_siggen = get_com_port('SignalGenerator')
# print('com_ports_siggen: ' + str(com_ports_siggen))





