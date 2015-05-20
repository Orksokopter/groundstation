from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from messages import BaseMessage
from protocol.BaseReceiver import BaseReceiver
from protocol.BaseSender import BaseSender


class BaseCommunicator(QObject):
    receiver = None
    sender = None

    received_message = pyqtSignal(BaseMessage)
    sent_message = pyqtSignal(BaseMessage)

    def __init__(self, QObject_parent=None):
        super().__init__(QObject_parent)

        assert isinstance(self.sender, BaseSender)
        assert isinstance(self.receiver, BaseReceiver)

        self.receiver.received_message.connect(self.receiver_received_message)
        self.sender.sent_message.connect(self.sender_sent_message)

        self.receiver.connect_to_writer(self.sender)

        self.receiver.start()
        self.sender.start()

    def send_message(self, message):
        self.sender.enqueue_message(message)

    def stop(self):
        self.receiver.abort()
        self.sender.abort()

        self.receiver.wait()
        self.sender.wait()

    @pyqtSlot(BaseMessage)
    def receiver_received_message(self, message):
        self.received_message.emit(message)

    @pyqtSlot(BaseMessage)
    def sender_sent_message(self, message):
        self.sent_message.emit(message)
