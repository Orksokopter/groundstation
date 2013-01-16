# coding=utf-8
from PyQt4 import QtGui
from serial.tools import list_ports

class SerialPortDialog(QtGui.QDialog):
    serialport_combobox = None

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle('Seriellen Port wählen')
        self.setWindowIcon(QtGui.QIcon(':/icons/glyph-router'))

        label = QtGui.QLabel("Port wählen:")

        self.serialport_combobox = QtGui.QComboBox()

        combolayout = QtGui.QHBoxLayout()
        combolayout.addWidget(label)
        combolayout.addStretch()
        combolayout.addWidget(self.serialport_combobox)

        buttonbox = QtGui.QDialogButtonBox(self)
        buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(combolayout)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        comports = list_ports.comports()
        self.serialport_combobox.clear()
        for port in comports:
            self.serialport_combobox.addItem(port[1], port[0])
        self.serialport_combobox.setFixedWidth(300)

    def get_selected_serial_port(self):
        return self.serialport_combobox.itemData(self.serialport_combobox.currentIndex())
