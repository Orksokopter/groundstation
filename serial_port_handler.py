import binascii
import logging
from threading import Thread
import serial
import sys
from messages import PingMessage, STX, ETB, ESC, BaseMessage, UnknownMessageType, MessageCRCError, ProxyMessage
from queue import Queue
import settings

settings.init_logging()

class SerialRead(Thread):
    def __init__(self, serial_port):
        """
        @type serial_port: serial.Serial
        """
        Thread.__init__(self)
        self.serial_port = serial_port

    def run(self):
        logger = logging.getLogger()
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
                    logger.debug("< {}".format(msg))
                except MessageCRCError as e:
                    logger.error('Message CRC mismatch... transmitted CRC: {}, computed CRC: {}'.format(e.transmitted_crc, e.computed_crc))
                except UnknownMessageType:
                    logger.warn('Unknown message {}'.format(binascii.hexlify(buffer)))
                buffer = b""

class SerialWrite(Thread):
    def __init__(self, serial_port, queue):
        """
        @type serial_port: serial.Serial
        @type queue: queue.Queue
        """
        Thread.__init__(self)
        self.serial_port = serial_port
        self.queue = queue

    def run(self):
        logger = logging.getLogger()
        while True:
            msg = self.queue.get()

            logger.debug("> {}...".format(msg))
            self.serial_port.write(msg.encode_for_writing())
            self.serial_port.flush()

ser = serial.Serial(3, 57600)

sr = SerialRead(ser)
sr.start()

writer_queue = Queue()

sw = SerialWrite(ser, writer_queue)
sw.start()

writer_queue.put(PingMessage())
writer_queue.put(ProxyMessage(PingMessage()))