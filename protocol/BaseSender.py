from abc import abstractmethod
import logging
from queue import Empty, Queue
from threading import Condition, Lock

from PyQt5.QtCore import QThread, pyqtSignal

from messages import BaseMessage, RequestConfirmationMessage


class BaseSender(QThread):
    sent_message = pyqtSignal(BaseMessage)

    def __init__(self, QObject_parent=None):
        """
        @type serial_port: serial.Serial
        @type queue: queue.Queue
        """
        QThread.__init__(self, QObject_parent)
        self.queue = Queue()
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

    def enqueue_message(self, message):
        self.queue.put(message)

    def put_message_in_free_slot(self, message):
        for index, slot in enumerate(self.message_buffer_slots):
            if slot is None:
                self.message_buffer_slots[index] = message
                break

    def remove_message_from_slots(self, message_number):
        with self.reset_send_buffer_lock:
            for index, slot in enumerate(self.message_buffer_slots):
                if slot is not None and slot.message_number() == message_number:
                    self.message_buffer_slots[index] = None
                    self.full_buffer_wait_condition.notify_all()
                    return

    def abort(self):
        self.__abort = True

    @abstractmethod
    def send_message(self, message):
        pass

    def run(self):
        logger = logging.getLogger()
        while not self.__abort:
            try:
                msg = self.queue.get(timeout=1)
            except Empty:
                continue

            with self.reset_send_buffer_lock:
                while not self.__abort and not self.has_empty_message_slot():
                    logger.debug('Send buffer full... waiting for message '
                                 'confirmations')

                    if not self.full_buffer_wait_condition.wait(1):
                        for msg_in_buffer in self.message_buffer_slots:
                            if msg_in_buffer is None:
                                continue

                            request_confirmation = RequestConfirmationMessage(
                                msg_in_buffer
                            )
                            self.send_message(request_confirmation)
                            self.sent_message.emit(request_confirmation)
                            logger.debug('> {}'.format(request_confirmation))

                # This thread may have been told to abort while waiting on the
                # send buffer
                if self.__abort:
                    continue

                self.current_message_number += 1
                msg.set_message_number(self.current_message_number)

                logger.debug("> {}...".format(msg))

                self.send_message(msg)

                self.put_message_in_free_slot(msg)

                self.sent_message.emit(msg)
