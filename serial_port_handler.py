import binascii
import logging
from threading import Thread, Lock, Condition
import serial
import sys
from messages import PingMessage, STX, ETB, ESC, BaseMessage, UnknownMessageType, MessageCRCError, ProxyMessage, ClearToSendMessage
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
        self.writer = None

    def connect_to_writer(self, writer):
        """
        @type writer: SerialWrite
        """
        self.writer = writer

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

                    if isinstance(msg, ClearToSendMessage):
                        self.writer.reset_remaining_send_buffer()

                except MessageCRCError as e:
                    logger.error('Message CRC mismatch... transmitted CRC: {}, computed CRC: {}'.format(e.transmitted_crc, e.computed_crc))
                except UnknownMessageType:
                    logger.warn('Unknown message {}'.format(binascii.hexlify(buffer)))
                buffer = b""

class SerialWrite(Thread):
    MAX_SERIAL_SEND_BUFFER = 128

    def __init__(self, serial_port, queue):
        """
        @type serial_port: serial.Serial
        @type queue: queue.Queue
        """
        Thread.__init__(self)
        self.serial_port = serial_port
        self.queue = queue
        self.current_message_number = 0
        self.last_cleared_message_number = None
        self.remaining_send_buffer = 0

        self.reset_send_buffer_lock = Lock()
        self.full_buffer_wait_condition = Condition(self.reset_send_buffer_lock)

        self.reset_remaining_send_buffer()

    def reset_remaining_send_buffer(self):
        logging.debug('Clearing remaining send buffer...')
        self.reset_send_buffer_lock.acquire()
        self.remaining_send_buffer = self.MAX_SERIAL_SEND_BUFFER
        try:
            self.full_buffer_wait_condition.notify()
        except RuntimeError:
            pass
        self.reset_send_buffer_lock.release()

    def run(self):
        logger = logging.getLogger()
        while True:
            msg = self.queue.get()

            self.current_message_number+= 1
            msg.set_message_number(self.current_message_number)

            logger.debug("> {}...".format(msg))

            encoded_message = msg.encode_for_writing()

            with self.reset_send_buffer_lock:
                if len(encoded_message) > self.remaining_send_buffer:
                    logger.info('Send buffer full... waiting for ClearToSend')
                    self.full_buffer_wait_condition.wait()

                self.remaining_send_buffer-= len(encoded_message)
                self.serial_port.write(encoded_message)
                self.serial_port.flush()

ser = serial.Serial(3, 57600)

writer_queue = Queue()
sr = SerialRead(ser)
sw = SerialWrite(ser, writer_queue)
sr.connect_to_writer(sw)

sr.start()
sw.start()

for i in range(1000):
    writer_queue.put(PingMessage())
    writer_queue.put(ProxyMessage(PingMessage()))
