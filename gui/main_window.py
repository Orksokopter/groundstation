import logging
import sys

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout

from serial.serialutil import SerialException

from gui.widgets import PingPongWidget, MessageListWidget, ParametersWidget, \
    SerialPortSelector
from messages import BaseMessage, PingMessage, NopMessage, ConfirmationMessage
from protocol.EmulatedCommunicator import EmulatedCommunicator
from protocol.SerialPortCommunicator import SerialPortCommunicator


class MainWindow(QtWidgets.QMainWindow):
    parameters_widget = None

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Mikrokopter Bodenpython')
        self.communicator = None
        self.list_widget = None
        self.pingpong_widget = None

        self.serialport_selector = SerialPortSelector()
        self.setCentralWidget(self.serialport_selector)
        self.serialport_selector.accepted.connect(self.serialport_selected)
        self.serialport_selector.rejected.connect(self.close)

        QtCore.QTimer.singleShot(0, self.initialize)

    @pyqtSlot(BaseMessage)
    def reader_received_message(self, message):
        if isinstance(message, NopMessage) or isinstance(message, ConfirmationMessage):
            return

        self.list_widget.addMessage('in', message)

    @pyqtSlot(BaseMessage)
    def writer_sent_message(self, message):
        if isinstance(message, NopMessage) or isinstance(message, ConfirmationMessage):
            return

        self.list_widget.addMessage('out', message)

    @pyqtSlot('QString')
    def serialport_selected(self, selected_port):
        logging.debug('Selected port {}'.format(selected_port))

        if selected_port == SerialPortSelector.EMULATOR:
            self.communicator = EmulatedCommunicator()
        else:
            try:
                self.communicator = SerialPortCommunicator(selected_port)
            except SerialException as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    'Error!',
                    'Could not connect to serial port {}<br><br>The error was: {}'.format(selected_port, e.strerror)
                )
                QtCore.QTimer.singleShot(0, self.close)
                return

        self.communicator.received_message.connect(self.reader_received_message)
        self.communicator.sent_message.connect(self.writer_sent_message)

        self.communicator.send_message(PingMessage())

        self.init_gui()

        del self.serialport_selector

    def initialize(self):
        self.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        QtWidgets.qApp.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))

    def init_gui(self):
        self.list_widget = MessageListWidget(self)
        self.pingpong_widget = PingPongWidget(self.communicator, self)
        self.parameters_widget = ParametersWidget(self)

        list_and_ping_layout = QHBoxLayout()
        list_and_ping_layout.addWidget(self.list_widget)
        list_and_ping_layout.addWidget(self.pingpong_widget)

        layout = QVBoxLayout()
        layout.addLayout(list_and_ping_layout)
        layout.addWidget(self.parameters_widget)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def closeEvent(self, event):
        if self.communicator is not None:
            logger = logging.getLogger()

            logger.debug("Stopping communicator")
            self.communicator.stop()

        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
