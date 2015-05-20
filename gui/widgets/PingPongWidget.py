from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from messages import PingMessage, ProxyMessage

import gui.resources_rc


class PingPongWidget(QtWidgets.QWidget):
    writer_queue = None

    def __init__(self, writer_queue, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.writer_queue = writer_queue

        ping_button = QtWidgets.QPushButton()
        ping_button.setText('Ping')
        ping_button.setIcon(QtGui.QIcon(':/icons/pong'))
        ping_button.clicked.connect(self.ping_button_pushed)

        proxy_ping_button = QtWidgets.QPushButton()
        proxy_ping_button.setText('Proxy ping')
        proxy_ping_button.setIcon(QtGui.QIcon(':/icons/pong'))
        proxy_ping_button.clicked.connect(self.proxy_ping_button_pushed)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(ping_button)
        layout.addWidget(proxy_ping_button)
        layout.addStretch()

        self.setLayout(layout)


    @pyqtSlot()
    def proxy_ping_button_pushed(self):
        self.writer_queue.put(ProxyMessage(PingMessage()))

    @pyqtSlot()
    def ping_button_pushed(self):
        self.writer_queue.put(PingMessage())
