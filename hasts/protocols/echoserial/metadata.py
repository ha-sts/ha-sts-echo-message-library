#!/usr/bin/env python3

### IMPORTS ###
import logging

from .txid import TransmitterIdentifier

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
class Metadata:
    pass

class MetadataInboundComplete(Metadata):
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._originator = TransmitterIdentifier()
        self._first_hop = TransmitterIdentifier()
        self._trace_list = []
        self._hop_count = 0

    @property
    def bytes(self):
        tmp_buffer = []
        for i in range(len(self._originator.bytes)):
            tmp_buffer.append(self._originator.bytes[i])
        for i in range(len(self._first_hop.bytes)):
            tmp_buffer.append(self._first_hop.bytes[i])
        tmp_buffer.append(len(self._trace_list))
        for j in range(len(self._trace_list)):
            for i in range(len(self._trace_list[j].bytes)):
                tmp_buffer.append(self._trace_list[j].bytes[i])
        tmp_buffer.append(self._hop_count)
        return tmp_buffer

    @bytes.setter
    def bytes(self, value):
        if not isinstance(value, list):
            raise TypeError("Not a list of bytes")
        if not len(value) > 9:
            raise ValueError("Too few bytes")
        tmp_trace_count = value[8]
        if len(value) != ((4 * tmp_trace_count) + 10):
            raise ValueError("Incorrect number of bytes")
        self._originator.bytes = value[0:4]
        self._first_hop.bytes = value[4:8]
        self._trace_list = []
        for i in range(tmp_trace_count):
            tmp_txid = TransmitterIdentifier()
            tmp_index = (i * 4) + 9
            tmp_txid.bytes = value[tmp_index : tmp_index + 4]
            self._trace_list.append(tmp_txid)
        self._hop_count = value[-1]