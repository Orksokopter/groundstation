from datetime import datetime

from PyQt5 import QtGui, QtWidgets


class MessageListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

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
            icon = QtGui.QIcon(':/icons/arrow-left')
        else:
            icon = QtGui.QIcon(':/icons/arrow-right')

        self.addItem(QtWidgets.QListWidgetItem(icon, "{}: {}".format(datetime.now().isoformat(), msg)))

        if scroll_down:
            self.scrollToBottom()
