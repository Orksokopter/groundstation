import abc
import sys
import binascii
from tools import crc8


ESC = b"\x1B"
STX = b"\x01"
ETB = b"\x17"


class MessageCRCError(Exception):
    def __init__(self, transmitted_crc, computed_crc):
        self.transmitted_crc = transmitted_crc
        self.computed_crc = computed_crc


class UnknownMessageType(Exception):
    pass


class EmptyMessageError(Exception):
    pass


class MessageTypes:
    MSG_NOP = 0x000000
    MSG_ACK = 0x000001
    MSG_PROXY_MESSAGE = 0x000002
    MSG_SET_PARAMETER = 0x000003
    MSG_CUR_PARAMETER = 0x000004
    MSG_GET_PARAMETER = 0x000005
    MSG_PING = 0x000006
    MSG_PONG = 0x000007
    MSG_SET_LEDS = 0x000008
    MSG_CLEAR_TO_SEND = 0x000009
    MSG_BUFFER_REPORT = 0x00000a
    MSG_OUT_BUFFER_FULL = 0x00000b
    MSG_DO_ACCEL_CALIBRATION = 0x00000c
    MSG_ACCEL_CALIBRATION_DONE = 0x00000d
    MSG_DO_GYRO_CALIBRATION = 0x00000e
    MSG_GYRO_CALIBRATION_DONE = 0x00000f
    MSG_DECIMAL_DEBUG_DUMP = 0x000010
    MSG_REQUEST_CONFIRMATION = 0x000011
    MSG_CONFIRMATION = 0x000012


class BaseMessage(object):
    def __init__(self, message_type):
        self.__message_type = message_type
        self.__message_number = None

    def message_type(self):
        return self.__message_type

    def message_number(self):
        return self.__message_number

    def set_message_number(self, msg_num):
        self.__message_number = msg_num

    def encode_for_writing(self):
        val = b''

        msg_num = (self.message_number() if self.message_number() is not None else 0).to_bytes(3, byteorder='big')
        msg_type = self.message_type().to_bytes(3, byteorder='big')
        data = self.prepare_data()
        crc = crc8.calc(msg_num+msg_type+data).to_bytes(1, byteorder='big')

        val += STX+STX+self.escape_bytes(msg_num)+self.escape_bytes(msg_type)+self.escape_bytes(data)+self.escape_bytes(crc)+ETB
        return val

    # TODO Find a better name for this
    def encode_for_writing_without_msg_num(self):
        val = b''

        msg_type = self.message_type().to_bytes(3, byteorder='big')
        data = self.prepare_data()
        crc = crc8.calc(msg_type+data).to_bytes(1, byteorder='big')

        val += STX+STX+self.escape_bytes(msg_type)+self.escape_bytes(data)+self.escape_bytes(crc)+ETB
        return val

    def encoded_message_length(self):
        return len(self.encode_for_writing())

    @classmethod
    def from_raw_data(cls, data):
        """
        @param data: Bla
        @type data: bytes
        """
        if not data:
            raise EmptyMessageError()

        transmitted_crc = data[-1]
        computed_crc = crc8.calc(data[0:-1])

        if transmitted_crc != computed_crc:
            raise MessageCRCError(transmitted_crc=transmitted_crc, computed_crc=computed_crc)

        msg_type = int.from_bytes(data[0:3], byteorder='big')

        if msg_type == MessageTypes.MSG_PONG:
            msg = PongMessage.from_raw_data(data[3:-1])
        elif msg_type == MessageTypes.MSG_CONFIRMATION:
            msg = ConfirmationMessage.from_raw_data(data[3:-1])
        else:
            raise UnknownMessageType()

        return msg

    @abc.abstractmethod
    def prepare_data(self):
        """
        @rtype: bytes
        """
        pass

    @staticmethod
    def escape_bytes(val):
        return val.replace(ESC, ESC+ESC).replace(STX, ESC+STX).replace(ETB, ESC+ETB)

    def __str__(self):
        return self._pretty_print()

    def _pretty_print(self, stuff=None):
        format_str = "{type}" if self.message_number() is None else "[{msg_num:0>8}] {type}"
        base = format_str.format(msg_num=self.message_number(), type=self.__class__.__name__)

        if stuff is not None:
            return '{} ({})'.format(base, stuff)

        return base


class PingMessage(BaseMessage):
    sequence_number = 0

    def __init__(self):
        super().__init__(MessageTypes.MSG_PING)
        PingMessage.sequence_number += 1
        self.sequence_number = PingMessage.sequence_number

    def __str__(self):
        return self._pretty_print('Sequence number: {}'.format(self.sequence_number))

    def prepare_data(self):
        return self.sequence_number.to_bytes(2, byteorder="big")

    @classmethod
    def from_raw_data(cls, data):
        msg = PingMessage()
        msg.sequence_number = int.from_bytes(data, byteorder='big')

        return msg


class PongMessage(BaseMessage):
    def __init__(self):
        super().__init__(MessageTypes.MSG_PONG)
        self.sequence_number = None

    def __str__(self):
        return self._pretty_print('Sequence number: {}'.format(self.sequence_number))

    def prepare_data(self):
        return self.sequence_number.to_bytes(2, byteorder="big")

    @classmethod
    def from_raw_data(cls, data):
        msg = PongMessage()
        msg.sequence_number = int.from_bytes(data, byteorder='big')

        return msg


class ConfirmationMessage(BaseMessage):
    def __init__(self):
        super().__init__(MessageTypes.MSG_CONFIRMATION)
        self.__confirmed_message_number = None

    def confirmed_message_number(self):
        return self.__confirmed_message_number

    def set_confirmed_message_number(self, msg_num):
        self.__confirmed_message_number = msg_num

    def __str__(self):
        return self._pretty_print("Message Number: {}".format(self.__confirmed_message_number))

    def prepare_data(self):
        return self.__confirmed_message_number.to_bytes(3, byteorder='big')

    @classmethod
    def from_raw_data(cls, data):
        msg = ConfirmationMessage()
        msg.__confirmed_message_number = int.from_bytes(data[0:3], byteorder='big')

        return msg


class ProxyMessage(BaseMessage):
    def __init__(self, inner_message=None):
        """
        @type inner_message: BaseMessage
        """
        super().__init__(MessageTypes.MSG_PROXY_MESSAGE)
        self.inner_message = inner_message

    def set_inner_message(self, msg):
        """
        @type msg: BaseMessage
        """
        self.inner_message = msg

    def prepare_data(self):
        tmp = self.inner_message.message_type().to_bytes(3, byteorder='big')
        tmp += self.inner_message.prepare_data()

        return len(tmp).to_bytes(2, byteorder='big')+tmp

    def __str__(self):
        return self._pretty_print(self.inner_message)


class NopMessage(BaseMessage):
    def __init__(self):
        super().__init__(MessageTypes.MSG_NOP)

    def prepare_data(self):
        return b''


class RequestConfirmationMessage(BaseMessage):
    def __init__(self, message):
        super().__init__(MessageTypes.MSG_REQUEST_CONFIRMATION)
        self.message = message
        self.set_message_number(0)

    def __str__(self):
        return self._pretty_print(self.message)

    def prepare_data(self):
        return self.message.message_type().to_bytes(3, byteorder='big')
