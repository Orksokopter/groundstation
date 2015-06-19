from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QScrollArea


class HorizontalScrollArea(QScrollArea):
    def __init__(self, QWidget_parent=None):
        super().__init__(QWidget_parent)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def eventFilter(self, o, e):
        if (o == self.widget() and e.type() == QEvent.Resize):
            self.setMinimumHeight(self.widget().minimumSizeHint().height() +
                                  self.horizontalScrollBar().height())

        return super().eventFilter(o, e)
