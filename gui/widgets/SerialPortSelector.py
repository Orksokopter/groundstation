import os
import sys

from PyQt5.QtCore import QSettings, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox, QDialogButtonBox, QWidget, QVBoxLayout
from serial.tools import list_ports


class SerialPortSelector(QWidget):
    serialport_combobox = None
    settings = None

    DARWIN_SERIAL_PORT_PATH = "/dev/tty.Orksokopter-DevB"

    EMULATOR = "__EMULATOR__"

    accepted = pyqtSignal(['QString'])
    rejected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Seriellen Port wählen')
        self.setWindowIcon(QIcon(':/icons/glyph-router'))

        self.serialport_combobox = QComboBox()
        self.serialport_combobox.setEditable(True)

        buttonbox = QDialogButtonBox(self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok |
                                     QDialogButtonBox.Close)

        layout = QVBoxLayout()
        layout.addWidget(self.serialport_combobox)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        self.settings = QSettings('olle-orks.org', 'Bodenpython')

        comports = list_ports.comports()

        if sys.platform.lower() == "darwin":
            if os.path.exists(self.DARWIN_SERIAL_PORT_PATH):
                comports.append((self.DARWIN_SERIAL_PORT_PATH,
                                 "Orksokopter-DevB"))

        comports.append((self.EMULATOR, "Emulator"))

        if comports:
            for port in comports:
                self.serialport_combobox.addItem(port[1], port[0])

        if self.settings.value('last_selected_com_port'):
            index = self.serialport_combobox.findData(
                self.settings.value('last_selected_com_port')
            )

            if index != -1:
                self.serialport_combobox.setCurrentIndex(index)

    def accept(self):
        self.settings.setValue('last_selected_com_port',
                               self.get_selected_serial_port())
        self.accepted.emit(self.get_selected_serial_port())

    def reject(self):
        self.rejected.emit()

    def get_selected_serial_port(self):
        selected_item_data = self.serialport_combobox.itemData(
            self.serialport_combobox.currentIndex()
        )

        if selected_item_data:
            return selected_item_data
        else:
            return self.serialport_combobox.currentText()
