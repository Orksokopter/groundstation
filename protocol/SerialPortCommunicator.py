from time import sleep

import serial

from protocol.BaseReceiver import BaseReceiver
from protocol.BaseCommunicator import BaseCommunicator
from protocol.BaseSender import BaseSender


class SerialPortReceiver(BaseReceiver):
    serial_port = None

    def __init__(self, serial_port, QObject_parent=None):
        super().__init__(QObject_parent)

        self.serial_port = serial_port

    def read(self):
        return self.serial_port.read()


class SerialPortSender(BaseSender):
    serial_port = None

    def __init__(self, serial_port, QObject_parent=None):
        super().__init__(QObject_parent)

        self.serial_port = serial_port

    def send_message(self, message):
        self.serial_port.write(message.encode_for_writing())
        self.serial_port.flush()

    def run(self):
        # Wait some time for the serial device because it can ignore data until
        # it is fully booted up
        sleep(1)

        super().run()


class SerialPortCommunicator(BaseCommunicator):
    serial_port = None

    def __init__(self, serial_port, QObject_parent=None):
        self.serial_port = serial.Serial(serial_port, 57600)

        # This needs to be set so the threads may have a chance to abort
        self.serial_port.timeout = 1

        self.sender = SerialPortSender(self.serial_port, QObject_parent)
        self.receiver = SerialPortReceiver(self.serial_port, QObject_parent)

        super().__init__(QObject_parent)

    def stop(self):
        super().stop()

        self.serial_port.close()
