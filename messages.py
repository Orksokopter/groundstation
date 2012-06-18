import abc
import sys
from tools import crc8

class MessageCRCError(Exception):
    def __init__(self, transmitted_crc, computed_crc):
        self.transmitted_crc = transmitted_crc
        self.computed_crc = computed_crc
class UnknownMessageType(Exception):
    pass

ESC = b"\x1B"
STX = b"\x01"
ETB = b"\x17"

class MESSAGE_TYPES:
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


class BaseMessage(object):
    def __init__(self, message_type):
        self.__message_type = message_type

    def message_type(self):
        return self.__message_type

    def encode_for_writing(self):
        val = b''

        type = self.message_type().to_bytes(3, byteorder='big')
        data = self.prepare_data()
        crc = crc8.calc(type+data).to_bytes(1, byteorder='big')

        val+= STX+STX+self.escape_bytes(type)+self.escape_bytes(data)+self.escape_bytes(crc)+ETB
        return val

    @classmethod
    def from_raw_data(cls, data):
        """
        @param data: Bla
        @type data: bytes
        """
        transmitted_crc = data[-1]
        computed_crc = crc8.calc(data[0:-1])

        if transmitted_crc != computed_crc:
            raise MessageCRCError(transmitted_crc=transmitted_crc, computed_crc=computed_crc)

        type = int.from_bytes(data[0:3], byteorder='big')

        if type == MESSAGE_TYPES.MSG_PONG:
            msg = PongMessage.from_raw_data(data[3:-1])
        elif type == MESSAGE_TYPES.MSG_CLEAR_TO_SEND:
            msg = ClearToSendMessage()
        else:
            raise UnknownMessageType()

        return msg

    @abc.abstractmethod
    def prepare_data(self):
        """
        @rtype: bytes
        """
        pass

    def escape_bytes(self, bytes):
        return bytes.replace(ESC, ESC+ESC).replace(STX, ESC+STX).replace(ETB, ESC+ETB)

    def __str__(self):
        return self.__class__.__name__

class PingMessage(BaseMessage):
    sequence_number = 0

    def __init__(self):
        super().__init__(MESSAGE_TYPES.MSG_PING)
        PingMessage.sequence_number+= 1
        self.sequence_number = PingMessage.sequence_number

    def __str__(self):
        return 'PingMessage (Sequence number: {})'.format(self.sequence_number)

    def prepare_data(self):
        return self.sequence_number.to_bytes(2, byteorder="big")

    @classmethod
    def from_raw_data(cls, data):
        msg = PingMessage()
        msg.sequence_number = int.from_bytes(data, byteorder='big')

        return msg

class PongMessage(BaseMessage):
    def __init__(self):
        super().__init__(MESSAGE_TYPES.MSG_PONG)
        self.sequence_number = None

    def __str__(self):
        return 'PongMessage (Sequence number: {})'.format(self.sequence_number)

    def prepare_data(self):
        return self.sequence_number.to_bytes(2, byteorder="big")

    @classmethod
    def from_raw_data(cls, data):
        msg = PongMessage()
        msg.sequence_number = int.from_bytes(data, byteorder='big')

        return msg

class ClearToSendMessage(BaseMessage):
    def __init__(self):
        super().__init__(MESSAGE_TYPES.MSG_CLEAR_TO_SEND)