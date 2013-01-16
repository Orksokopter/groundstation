# coding=utf-8
import logging
from queue import Queue
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QVBoxLayout
import serial
from gui.serial_port_dialog import SerialPortDialog
from gui.widgets.MessageListWidget import MessageListWidget
from messages import BaseMessage, PingMessage
from serial_port_handler import SerialRead, SerialWrite

import gui.resources_rc

class MainWindow(QtGui.QWidget):
    selected_serial_port = None

    serial_reader = None
    serial_writer = None
    serial_writer_queue = None

    list_widget = None

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setWindowIcon(QtGui.QIcon(':/icons/app-icon'))
        self.setWindowTitle('Mikrokopter Bodenpython')

        QtCore.QTimer.singleShot(0, self.initialize)

    @pyqtSlot(BaseMessage)
    def reader_received_message(self, message):
        self.list_widget.addMessage('in', message)

    @pyqtSlot(BaseMessage)
    def writer_sent_message(self, message):
        self.list_widget.addMessage('out', message)

    def initialize(self):
        dlg = SerialPortDialog()

        if dlg.exec() == QtGui.QDialog.Rejected:
            QtCore.QTimer.singleShot(0, self.close)
            return

        selected_port = dlg.get_selected_serial_port()
        logging.debug('Selected port {}'.format(selected_port))

        self.selected_serial_port = serial.Serial(selected_port, 57600)
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

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())