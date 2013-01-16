from datetime import datetime
from PyQt4 import QtGui
from PyQt4.QtSvg import *

import gui.resources_rc

class MessageListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

    def addMessage(self, direction, msg):
        scroll_down = False

        # Since this list will pollute the applications memory sooner or later
        # the list will stop getting larger after a specific amount of items
        # As long as this amount is not reached the list will also automatically
        # scroll down if the slider is at the bottom anyways.
        if self.count() > 300:
            self.takeItem(0)
        else:
            if self.verticalScrollBar().sliderPosition() == self.verticalScrollBar().maximum():
                scroll_down = True

        if direction == 'in':
            icon = QtGui.QIcon(QtGui.QPixmap(':/icons/arrow-left'))
        else:
            icon = QtGui.QIcon(QtGui.QPixmap(':/icons/arrow-right'))

        self.addItem(QtGui.QListWidgetItem(icon, "{}: {}".format(datetime.now().isoformat(), msg)))

        if scroll_down:
            self.scrollToBottom()
