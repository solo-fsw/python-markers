
def send_command(ser_device, command):
    if type(command) == str:
        ser_device.write(b'P')
    elif type(command) == int:
        usb_par_marker.write(bytearray([0]))

    data = ser_device.readline()
    decoded_data = data.decode('utf-8')
    return decoded_data
