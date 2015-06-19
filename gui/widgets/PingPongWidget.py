from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot

from messages import PingMessage, ProxyMessage


class PingPongWidget(QtWidgets.QWidget):
    communicator = None

    def __init__(self, communicator, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.communicator = communicator

        ping_button = QtWidgets.QPushButton()
        ping_button.setText('Ping')
        ping_button.setIcon(QtGui.QIcon(':/icons/pong'))
        ping_button.clicked.connect(self.ping_button_pushed)

        proxy_ping_button = QtWidgets.QPushButton()
        proxy_ping_button.setText('Proxy ping')
        proxy_ping_button.setIcon(QtGui.QIcon(':/icons/pong'))
        proxy_ping_button.clicked.connect(self.proxy_ping_button_pushed)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ping_button)
        layout.addWidget(proxy_ping_button)
        layout.addStretch()

        self.setLayout(layout)

    @pyqtSlot()
    def proxy_ping_button_pushed(self):
        self.communicator.send_message(ProxyMessage(PingMessage()))

    @pyqtSlot()
    def ping_button_pushed(self):
        self.communicator.send_message(PingMessage())
