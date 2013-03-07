from PyQt4 import QtGui


import gui.resources_rc
from messages import PingMessage


class PingPongWidget(QtGui.QPushButton):
    writer_queue = None

    def __init__(self, writer_queue, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.writer_queue = writer_queue
        self.setText('Ping senden')
        self.setIcon(QtGui.QIcon(':/icons/pong'))

        self.clicked.connect(self.button_pushed)

    def button_pushed(self):
        self.writer_queue.put(PingMessage())
