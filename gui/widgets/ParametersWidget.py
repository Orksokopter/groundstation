from collections import OrderedDict
import os
import uuid

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QLabel, QSpinBox, QHBoxLayout, QGroupBox, \
    QVBoxLayout, qApp, QWidget, QToolButton, QMenu, QPushButton, QMessageBox, \
    QAction, QInputDialog

from .HorizontalScrollArea import HorizontalScrollArea


class Parameters:
    YAW_KP = 0x000000
    YAW_KI = 0x000001
    YAW_KD = 0x000002
    YAW_ILIMIT = 0x000003
    YAW_RESOLUTIONFILTER = 0x000004
    YAW_AVERAGINGFILTER = 0x000005
    ROLL_KP = 0x000006
    ROLL_KI = 0x000007
    ROLL_KD = 0x000008
    ROLL_ILIMIT = 0x000009
    ROLL_RESOLUTIONFILTER = 0x00000a
    ROLL_AVERAGINGFILTER = 0x00000b
    PITCH_KP = 0x00000c
    PITCH_KI = 0x00000d
    PITCH_KD = 0x00000e
    PITCH_ILIMIT = 0x00000f
    PITCH_RESOLUTIONFILTER = 0x000010
    PITCH_AVERAGINGFILTER = 0x000011
    MISC_ACC_HORIZ_KI = 0x000012
    MISC_ACC_VERT_KI = 0x000013
    MISC_COMPASS_KI = 0x000014
    MISC_IDLE_SPEED = 0x000015
    MISC_START_THRESHOLD = 0x000016
    MISC_STOP_THRESHOLD = 0x000017
    MISC_SKIP_CONTROL_CYCLES = 0x000018
    MISC_ACC_RANGE = 0x000019
    SPECIAL_BATT_VOLTAGE = 0x00001a

    @classmethod
    def get_sorted_parameters(cls):
        parameters_dict = {}
        for param in dir(cls):
            if not isinstance(getattr(cls, param), int):
                continue
            parameters_dict.update({
                param: getattr(cls, param)
            })
        return OrderedDict(sorted(parameters_dict.items(), key=lambda t: t[1]))


class ParametersWidget(QWidget):
    writer_queue = None
    parameter_control_widgets = []
    dirty = False

    def __init__(self, writer_queue, parent=None):
        super(ParametersWidget, self).__init__(parent)
        self.writer_queue = writer_queue

        self.settings = QtCore.QSettings(
            os.path.join(qApp.applicationDirPath(), 'parameter_profiles.ini'),
            QtCore.QSettings.IniFormat
        )

        ###
        # Parameter groups
        ###

        scroll_widget = QWidget()

        group_widgets_layout = QHBoxLayout(scroll_widget)
        last_group = None
        curr_group_widget = None
        for param in Parameters.get_sorted_parameters():
            if param.startswith('_'):
                continue

            group, param_name = param.split('_', 1)

            if group != last_group:
                if last_group is not None:
                    curr_group_widget.layout().addStretch()
                last_group = group

                curr_group_widget = QGroupBox(group)
                curr_group_widget.setLayout(QVBoxLayout())

                group_widgets_layout.addWidget(curr_group_widget)

            param_widget = ParameterControlWidget(param_name, getattr(Parameters, param))
            param_widget.setParameterTypeName(param)
            param_widget.editingFinished.connect(self.parameter_changed)
            curr_group_widget.layout().addWidget(param_widget)
            self.parameter_control_widgets.append(param_widget)
        curr_group_widget.layout().addStretch()
        del last_group, curr_group_widget

        ###
        # Buttons
        ###

        self.profile_button = QToolButton()
        self.profile_button.setArrowType(Qt.DownArrow)
        self.profile_button.setMenu(QMenu())
        self.profile_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.profile_button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.profile_button.clicked.connect(self.save_profile)
        self.profile_button.triggered.connect(self.change_profile)

        get_parameters_button = QPushButton('Fetch parameters')
        get_parameters_button.clicked.connect(self.fetch_parameters)
        self.send_parameters_button = QPushButton('Send parameters')
        self.send_parameters_button.clicked.connect(self.send_parameters)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.profile_button)
        button_layout.addWidget(get_parameters_button)
        button_layout.addWidget(self.send_parameters_button)

        ###
        # Main layout
        ###

        scroll_area = HorizontalScrollArea()
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.rebuild_profile_menu()
        self.change_profile(self.profile_button.menu().defaultAction())

    @pyqtSlot()
    def fetch_parameters(self):
        # TODO
        return

    @pyqtSlot()
    def send_parameters(self):
        # TODO
        return

    @pyqtSlot(QAction)
    def change_profile(self, action):
        """
        @type action: QtGui.QAction
        """

        profile_uuid = action.data()
        if profile_uuid is None:
            return

        if self.dirty:
            msg_box = QMessageBox()
            msg_box.setText('The current profile has unsaved changes')
            msg_box.setInformativeText('Should the changes be saved in the current profile?')
            msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Save)

            r = msg_box.exec()

            if r == QMessageBox.Cancel:
                return
            elif r == QMessageBox.Save:
                self.save_profile()

        self.active_profile = action

        self.set_dirty(False)

        if profile_uuid == 'new_profile':
            text = QInputDialog.getText(self, 'New profile', 'Name:')

            if not text:
                return

            profile_uuid = "{" + str(uuid.uuid4()) + "}"

            self.settings.beginGroup(profile_uuid)
            self.settings.setValue('profileName', text)

            self.settings.beginGroup('parameters')
            for le in self.parameter_control_widgets:
                self.settings.setValue(le.parameterTypeName(), le.value())
            self.settings.endGroup()

            self.settings.endGroup()

            self.rebuild_profile_menu()

            for action in self.profile_button.menu().actions():
                if action.data() == profile_uuid:
                    self.change_profile(action)
                    return
        else:
            self.profile_button.setText('Profile: ' + action.text())

            readonly = profile_uuid == 'read_only'

            self.send_parameters_button.setDisabled(readonly)

            for le in self.parameter_control_widgets:
                le.setReadOnly(readonly)
                le.setValue(0)

            if profile_uuid.startswith('{'):
                profile_uuid = "{" + str(uuid.UUID(profile_uuid)) + "}"

                self.settings.beginGroup(profile_uuid)
                self.settings.beginGroup('parameters')
                for le in self.parameter_control_widgets:
                    le.setValue(int(self.settings.value(le.parameterTypeName(), 0)))
                self.settings.endGroup()
                self.settings.endGroup()


    def rebuild_profile_menu(self):
        menu = self.profile_button.menu()
        menu.clear()

        read_only_action = QAction('Read-only', menu)
        read_only_action.setData('read_only')
        menu.addAction(read_only_action)
        menu.addSeparator()

        for le in self.settings.childGroups():
            action = QAction(self.settings.value(le + '/profileName')[0], menu)
            action.setData(le)
            menu.addAction(action)

        menu.addSeparator()

        new_profile_action = QAction("New profile", menu)
        new_profile_action.setData('new_profile')
        menu.addAction(new_profile_action)

        menu.setDefaultAction(read_only_action)

    def save_profile(self):
        if self.dirty and self.active_profile.data().startswith('{'):
            self.settings.beginGroup(self.active_profile.data())
            self.settings.beginGroup('parameters')
            for le in self.parameter_control_widgets:
                self.settings.setValue(le.parameterTypeName(), le.value())
            self.settings.endGroup()
            self.settings.endGroup()
            self.set_dirty(False)

    def set_dirty(self, dirty):
        self.dirty = dirty

        if self.dirty:
            self.profile_button.setText('Profile: ' + self.active_profile.text() + '*')
        else:
            self.profile_button.setText('Profile: ' + self.active_profile.text())

    @pyqtSlot(QWidget)
    def parameter_changed(self, widget):
        if self.active_profile.data() == 'read_only':
            return

        print("Test")

        # TODO msg

        self.set_dirty(True)


class ParameterControlWidget(QWidget):
    parameter_type_id = None
    parameter_type_name = None
    spinbox = None

    editingFinished = pyqtSignal(QWidget)

    def __init__(self, parameter_name, parameter_type, parent=None):
        super(ParameterControlWidget, self).__init__(parent)

        self.parameter_type_id = parameter_type

        self.spinbox = QSpinBox(self)
        # Hier steht im Gegensatz zu C++ -2147483648 weil nicht: http://bit.ly/uflXkq
        self.spinbox.setMinimum(-2147483648)
        self.spinbox.setMaximum(2147483647)
        self.spinbox.editingFinished.connect(self.someEditingFinished)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(parameter_name + ":"))
        layout.addWidget(self.spinbox)

        self.current_value = self.spinbox.value()

        self.setLayout(layout)

    def parameterTypeId(self):
        return self.parameter_type_id

    def parameterTypeName(self):
        return self.parameter_type_name

    def setParameterTypeName(self, parameter_type_name):
        self.parameter_type_name = parameter_type_name

    def value(self):
        return self.spinbox.value()

    def setValue(self, value):
        self.current_value = value
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)

    def setReadOnly(self, readonly):
        return self.spinbox.setReadOnly(readonly)

    @pyqtSlot()
    def someEditingFinished(self):
        if self.spinbox.value() != self.current_value:
            self.current_value = self.spinbox.value()

            if not self.spinbox.isReadOnly() and self.isEnabled():
                self.editingFinished.emit(self)

    def contextMenuEvent(self, event):
        # TODO big numbers widget
        pass
