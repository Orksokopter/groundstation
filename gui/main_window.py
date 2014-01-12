# coding=utf-8
import logging
from queue import Queue
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QVBoxLayout
import serial
from serial.serialutil import SerialException
from gui.serial_port_dialog import SerialPortDialog
from gui.widgets import PingPongWidget, MessageListWidget, ParametersWidget
from messages import BaseMessage, PingMessage, NopMessage, ConfirmationMessage
from serial_port_handler import SerialRead, SerialWrite

import gui.resources_rc


class MainWindow(QtGui.QWidget):
    parameters_widget = None

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        QtGui.QApplication.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        self.setWindowTitle('Mikrokopter Bodenpython')

        self.selected_serial_port = None

        self.serial_reader = None
        self.serial_writer = None
        self.serial_writer_queue = None

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

        if dlg.exec() == QtGui.QDialog.Rejected:
            QtCore.QTimer.singleShot(0, self.close)
            return

        selected_port = dlg.get_selected_serial_port()
        logging.debug('Selected port {}'.format(selected_port))

        try:
            self.selected_serial_port = serial.Serial(selected_port, 57600)
        except SerialException as e:
            QtGui.QMessageBox.critical(
                self,
                'Error!',
                'Could not connect to serial port {}<br><br>The error was: {}'.format(selected_port, e.strerror)
            )
            QtCore.QTimer.singleShot(0, self.close)
            return

        # This needs to be set so the threads may have a chance to abort
        self.selected_serial_port.timeout = 1

        self.serial_writer_queue = Queue()
        self.serial_reader = SerialRead(self.selected_serial_port)
        self.serial_writer = SerialWrite(self.selected_serial_port, self.serial_writer_queue)
        self.serial_reader.connect_to_writer(self.serial_writer)

        self.serial_reader.received_message.connect(self.reader_received_message)
        self.serial_writer.sent_message.connect(self.writer_sent_message)

        self.serial_reader.start()
        self.serial_writer.start()

        self.serial_writer_queue.put(PingMessage())

        self.init_gui()

    def init_gui(self):
        self.list_widget = MessageListWidget(self)
        self.pingpong_widget = PingPongWidget(self.serial_writer_queue, self)
        self.parameters_widget = ParametersWidget(self)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.pingpong_widget)
        layout.addWidget(self.parameters_widget)

        self.setLayout(layout)

    def closeEvent(self, event):
        if self.selected_serial_port and self.selected_serial_port.isOpen():
            logger = logging.getLogger()

            logger.debug("Aborting threads")
            self.serial_reader.abort()
            self.serial_writer.abort()

            logger.debug("Waiting for threads to stop")
            self.serial_reader.wait()
            self.serial_writer.wait()

            logger.debug("Closing serial port")
            self.selected_serial_port.close()

            logger.debug("Serial port closed")

        event.accept()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
