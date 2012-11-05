import binascii
from threading import Thread
import serial
import sys
from messages import PingMessage, STX, ETB, ESC, BaseMessage, UnknownMessageType, MessageCRCError

class SerialRead(Thread):
    def __init__(self, serial_port):
        Thread.__init__(self)
        self.serial_port = serial_port

    def run(self):
        buffer = b""
        state = "inactive"
        while True:
            curr_char = ser.read()

            if state != "after_escape" and curr_char == STX:
                buffer = b""
                state = "in_message"
            elif state == "in_message" and curr_char == ESC:
                state = "after_escape"
            elif state == "in_message" and curr_char == ETB:
                state = "after_message"
            elif state in ["after_escape", "in_message"]:
                buffer+= curr_char

                if state == "after_escape":
                    state = "in_message"

            if state == "after_message":
                try:
                    msg = BaseMessage.from_raw_data(buffer)
                    sys.stdout.write("Received message: {}\n".format(msg))
                    sys.stdout.flush()
                except MessageCRCError as e:
                    sys.stderr.write('Message CRC mismatch... transmitted CRC: {}, computed CRC: {}\n'.format(e.transmitted_crc, e.computed_crc))
                    sys.stderr.flush()
                except UnknownMessageType:
                    sys.stderr.write('Unknown message {}\n'.format(binascii.hexlify(buffer)))
                    sys.stderr.flush()
                buffer = b""

class SerialWrite(Thread):
    def __init__(self, serial_port):
        Thread.__init__(self)
        self.serial_port = serial_port
        pass

    def run(self):
        pass

ser = serial.Serial(3, 57600)

msg = PingMessage()
full_msg = msg.encode_for_writing()

sys.stdout.write("Sending {}...".format(msg))
ser.write(full_msg)
ser.flush()
sys.stdout.write(" done!\n")
sys.stdout.flush()

sr = SerialRead(ser)
sr.start()
sr.join()