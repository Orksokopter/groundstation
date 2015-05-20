from abc import abstractmethod
import logging
import binascii

from PyQt5.QtCore import QThread, pyqtSignal

from messages import BaseMessage, STX, ESC, ETB, ConfirmationMessage, \
    MessageCRCError, UnknownMessageType


class BaseReceiver(QThread):
    received_message = pyqtSignal(BaseMessage)
    __abort = None
    writer = None

    def __init__(self, QObject_parent=None):
        QThread.__init__(self, QObject_parent)

        self.__abort = False

    def connect_to_writer(self, writer):
        """
        @type writer: SerialWrite
        """
        self.writer = writer

    def abort(self):
        self.__abort = True

    @abstractmethod
    def read(self):
        pass

    def run(self):
        logger = logging.getLogger()
        buffer = b""
        state = "inactive"
        while not self.__abort:
            curr_char = self.read()

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
                        self.writer.remove_message_from_slots(
                            msg.confirmed_message_number()
                        )

                except MessageCRCError as e:
                    logger.error('Message CRC mismatch... transmitted CRC: {}, '
                                 'computed CRC: {}'.format(
                        e.transmitted_crc,
                        e.computed_crc)
                    )
                except UnknownMessageType:
                    logger.warn('Unknown message {}'.format(
                        binascii.hexlify(buffer))
                    )
                buffer = b""
