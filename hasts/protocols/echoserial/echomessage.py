#!/usr/bin/env python3

### IMPORTS ###
import enum
import logging

from .exceptions import EchoMessageInvalidException
from .metadata import MetadataInboundComplete

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
@enum.unique
class HeaderByte(enum.Enum):
    Generic = 0x00
    InboundComplete = 0x72

class EchoMessage:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        self._header = HeaderByte.Generic
        # Calc Length when needed
        self._metadata = None
        self._payload = None
        self._signal_level = None
        self._signal_margin = None
        self._signal_channel = None
        # Calc Checksum when needed

    @property
    def bytes(self):
        raise NotImplementedError

    @bytes.setter
    def bytes(self, packet):
        # packet should be a list of integers less than 256 (8 bits)
        # Verify length and bytes
        tmp_length = len(packet)
        if tmp_length < 2 or tmp_length > 255:
            self.logger.warning("Invalid packet: incorrect number of bytes.")
            raise EchoMessageInvalidException("incorrect number of bytes")
        if packet[1] != tmp_length - 1:
            self.logger.warning("Invalid packet: invalid length.")
            raise EchoMessageInvalidException("invalid length")
        for tmp_byte in packet:
            if tmp_byte < 0 or tmp_byte > 255:
                self.logger.warning("Invalid packet: packet contains non-byte value.")
                raise EchoMessageInvalidException("packet contains non-byte value")
        # Check for a valid header
        try:
            self._header = HeaderByte(packet[0])
        except ValueError:
            self.logger.warning("Invalid packet: unknown header value.")
            raise EchoMessageInvalidException("unknown header value")
        # verify checksum
        tmp_checksum = 0
        for i in range(packet[1]):
            tmp_checksum = (tmp_checksum + packet[i]) % 256
        if tmp_checksum != packet[-1]:
            self.logger.warning("Invalid packet: invalid checksum.")
            raise EchoMessageInvalidException("invalid checksum")

        # Create values from packet
        if self._header == HeaderByte.InboundComplete:
            # Create metadata, payload, and set signal
            self._metadata = MetadataInboundComplete()
            tmp_len_meta = (packet[10] * 4) + 10
            self._metadata.bytes = packet[2 : tmp_len_meta + 2]

    # FIXME: Make a summary / pretty print method
