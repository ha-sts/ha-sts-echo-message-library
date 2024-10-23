#!/usr/bin/env python3

### IMPORTS ###
import logging

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
class Payload:
    pass

class PayloadInboundComplete(Payload):
    message_class_byte = 0x00

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._message_class_byte = 0x00
        self._pti = 0x00
        self._data = []

    @property
    def bytes(self):
        tmp_result = []
        tmp_result.append(self._message_class_byte)
        tmp_result.append(self._pti)
        for tmp_item in self._data:
            tmp_result.append(tmp_item)
        return tmp_result

    @bytes.setter
    def bytes(self, value):
        if not isinstance(value, list):
            raise TypeError("Not a list of bytes")
        if not len(value) > 1:
            raise ValueError("Too few bytes")
        self._message_class_byte = value[0]
        self._pti = value[1]
        if len(value) > 2:
            for tmp_item in value[2:]:
                self._data.append(tmp_item)

class PayloadEnvironmentApplication(PayloadInboundComplete):
    message_class_byte = 0x3c

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
