import logging
import sys

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout
from serial.serialutil import SerialException

from gui.serial_port_dialog import SerialPortDialog
from gui.widgets import PingPongWidget, MessageListWidget
from messages import BaseMessage, PingMessage, NopMessage, ConfirmationMessage
from protocol.EmulatedCommunicator import EmulatedCommunicator
from protocol.SerialPortCommunicator import SerialPortCommunicator


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        QtWidgets.QApplication.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        self.setWindowTitle('Mikrokopter Bodenpython')

        self.communicator = None

        self.list_widget = None
        self.pingpong_widget = None

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

    def initialize(self):
        dlg = SerialPortDialog()

        if dlg.exec() == QtWidgets.QDialog.Rejected:
            QtCore.QTimer.singleShot(0, self.close)
            return

        selected_port = dlg.get_selected_serial_port()
        logging.debug('Selected port {}'.format(selected_port))

        if selected_port == dlg.EMULATOR:
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

    def init_gui(self):
        self.list_widget = MessageListWidget(self)
        self.pingpong_widget = PingPongWidget(self.communicator, self)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.pingpong_widget)

        self.setLayout(layout)

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

    sys.exit(app.exec_())
