"""serial_port_handler

Usage:
  serial_port_handler <device>
  serial_port_handler -h | --help

Options:
  -h --help     Show this screen.

"""
from docopt import docopt
import binascii
import logging
from threading import Lock, Condition
from PyQt4.QtCore import pyqtSignal
import serial
import sys
from messages import STX, ETB, ESC, BaseMessage, UnknownMessageType, MessageCRCError, ConfirmationMessage, NopMessage, \
    RequestConfirmationMessage
from queue import Queue, Empty
import settings
from PyQt4 import QtCore
from tools.getch import getch

settings.init_logging()


class SerialRead(QtCore.QThread):
    received_message = pyqtSignal(BaseMessage)

    def __init__(self, serial_port):
        """
        @type serial_port: serial.Serial
        """
        QtCore.QThread.__init__(self)
        self.serial_port = serial_port
        self.writer = None
        self.__abort = False

    def connect_to_writer(self, writer):
        """
        @type writer: SerialWrite
        """
        self.writer = writer

    def abort(self):
        self.__abort = True

    def run(self):
        logger = logging.getLogger()
        buffer = b""
        state = "inactive"
        while not self.__abort:
            curr_char = self.serial_port.read()

            if not curr_char:
                continue

            if state != "after_escape" and curr_char == STX:
                buffer = b""
                state = "in_message"
            elif state == "in_message" and curr_char == ESC:
                state = "after_escape"
            elif state == "in_message" and curr_char == ETB:
                state = "after_message"
            elif state in ["after_escape", "in_message"]:
                buffer += curr_char

                if state == "after_escape":
                    state = "in_message"

            if state == "after_message":
                if not buffer:
                    logger.warning('Received empty message, skipping!')
                    continue

                try:
                    msg = BaseMessage.from_raw_data(buffer)
                    logger.debug("< {}".format(msg))

                    self.received_message.emit(msg)

                    if isinstance(msg, ConfirmationMessage):
                        self.writer.remove_message_from_slots(msg.confirmed_message_number())

                except MessageCRCError as e:
                    logger.error('Message CRC mismatch... transmitted CRC: {}, computed CRC: {}'.format(
                        e.transmitted_crc,
                        e.computed_crc)
                    )
                except UnknownMessageType:
                    logger.warn('Unknown message {}'.format(binascii.hexlify(buffer)))
                buffer = b""


class SerialWrite(QtCore.QThread):
    MAX_SERIAL_SEND_BUFFER = 128

    sent_message = pyqtSignal(BaseMessage)

    def __init__(self, serial_port, queue):
        """
        @type serial_port: serial.Serial
        @type queue: queue.Queue
        """
        QtCore.QThread.__init__(self)
        self.serial_port = serial_port
        self.queue = queue
        self.current_message_number = 0
        self.last_cleared_message_number = None
        self.__abort = False

        self.message_buffer_slots = [None] * 3

        self.reset_send_buffer_lock = Lock()
        self.full_buffer_wait_condition = Condition(self.reset_send_buffer_lock)

    def has_empty_message_slot(self):
        for index, slot in enumerate(self.message_buffer_slots):
            if slot is None:
                return True

        return False

    def put_message_in_free_slot(self, message):
        for index, slot in enumerate(self.message_buffer_slots):
            if slot is None:
                self.message_buffer_slots[index] = message

    def remove_message_from_slots(self, message_number):
        with self.reset_send_buffer_lock:
            for index, slot in enumerate(self.message_buffer_slots):
                if slot is not None and slot.message_number == message_number:
                    self.message_buffer_slots[index] = None

    def abort(self):
        self.__abort = True

    def run(self):
        logger = logging.getLogger()
        while not self.__abort:
            try:
                msg = self.queue.get(timeout=1)
            except Empty:
                continue

            with self.reset_send_buffer_lock:
                while not self.__abort and not self.has_empty_message_slot():
                    logger.debug('Send buffer full... waiting for message confirmations')

                    if not self.full_buffer_wait_condition.wait(1):
                        for msg in self.message_buffer_slots:
                            if msg is None:
                                continue

                            request_confirmation = RequestConfirmationMessage(msg)
                            self.serial_port.write(request_confirmation.encode_for_writing())
                            self.sent_message.emit(request_confirmation)
                            logger.debug('> {}'.format(request_confirmation))

                # This thread may have been told to abort while waiting on the send buffer
                if self.__abort:
                    continue

                self.current_message_number += 1
                msg.set_message_number(self.current_message_number)

                logger.debug("> {}...".format(msg))

                encoded_message = msg.encode_for_writing()

                self.serial_port.write(encoded_message)
                self.serial_port.flush()

                self.put_message_in_free_slot(msg)

                self.sent_message.emit(msg)

if __name__ == "__main__":
    arguments = docopt(__doc__, version='serial_port_handler')

    from messages import PingMessage, ProxyMessage
    app = QtCore.QCoreApplication(sys.argv)

    ser = serial.Serial(arguments['<device>'], 57600)
    ser.timeout = 1  # This needs to be set so the threads may have a chance to abort

    writer_queue = Queue()
    sr = SerialRead(ser)
    sw = SerialWrite(ser, writer_queue)
    sr.connect_to_writer(sw)

    sr.start()
    sw.start()

    #logging.info("Press Enter to send a ping")

    #while input() is not None:
    #    writer_queue.put(PingMessage())
    #    #writer_queue.put(ProxyMessage(PingMessage()))

    for i in range(100):
        writer_queue.put(PingMessage())
        writer_queue.put(ProxyMessage(PingMessage()))

    print("")
    print("")
    print("(STRG+c) or (q) to quit")
    print("")

    char = None
    while char is not b"\x03" and char is not b"q":
        char = getch()

    sr.abort()
    sw.abort()

    sr.wait()
    sw.wait()
