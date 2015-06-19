from PyQt5.QtWidgets import QRadioButton


class QDataRadioButton(QRadioButton):
    __data = None

    def setData(self, data):
        self.__data = data

    def data(self):
        return self.__data
