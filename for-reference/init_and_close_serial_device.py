def init_serial_device(com_port, baudrate, timeout):
    # Initializes the serial port: configure port and open port.

    # Input: com port address (e.g. COM4), baudrate, timeout
    # Output: a serial device

    # NOTE: when the com_port is FAKECOM, a FakeSerial object is created and returned.
    # NOTE: when communication with the serial device fails, the output is a string with an error message

    import serial

    # When the com port address is FAKECOM a FakeSerial object is created.
    if com_port == 'FAKECOM':

        class FakeSerial:
            def __init__(self):
                self.port = com_port

        ser = FakeSerial()

    else:

        # Create serial device
        ser = serial.Serial()

        try:
            # Configure port
            ser.port = com_port
            ser.baudrate = baudrate
            ser.bytesize = 8
            ser.parity = 'N'
            ser.stopbits = 1

            ser.timeout = timeout

            # Open serial device
            ser.open()

        # Capture serial communication error
        except serial.serialutil.SerialException:
            ser.close()
            ser = 'ERROR: could not open serial device'

    return ser


def close_serial_device(ser_device):
    # Closes the serial device
    # Input: the serial device

    ser_device.close()
