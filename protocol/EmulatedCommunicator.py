from queue import Queue, Empty

from messages import ConfirmationMessage, PingMessage, PongMessage
from protocol.BaseCommunicator import BaseCommunicator
from protocol.BaseReceiver import BaseReceiver
from protocol.BaseSender import BaseSender


class EmulatedReceiver(BaseReceiver):
    emulator_queue = None

    def __init__(self, emulator_queue, QObject_parent=None):
        super().__init__(QObject_parent)

        self.emulator_queue = emulator_queue

    def read(self):
        try:
            return self.emulator_queue.get(timeout=1)
        except Empty:
            return None


class EmulatedSender(BaseSender):
    emulator_queue = None

    def __init__(self, emulator_queue, QObject_parent=None):
        super().__init__(QObject_parent)

        self.emulator_queue = emulator_queue
        self.next_message_number = 0

    def send_message(self, message):
        confirmation_msg = ConfirmationMessage()
        confirmation_msg.set_confirmed_message_number(message.message_number())
        self.put_message_in_receiver_queue(confirmation_msg)

        if isinstance(message, PingMessage):
            pong = PongMessage()
            pong.sequence_number = message.sequence_number
            self.put_message_in_receiver_queue(pong)

    def put_message_in_receiver_queue(self, message):
        encoded_msg = message.encode_for_writing_without_msg_num()

        for byte in [encoded_msg[i:i+1] for i in range(len(encoded_msg))]:
            self.emulator_queue.put(byte)



class EmulatedCommunicator(BaseCommunicator):
    emulator_queue = None

    def __init__(self, QObject_parent=None):
        self.emulator_queue = Queue()

        self.receiver = EmulatedReceiver(self.emulator_queue)
        self.sender = EmulatedSender(self.emulator_queue)

        super().__init__(QObject_parent)

