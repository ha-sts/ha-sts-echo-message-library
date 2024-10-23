#!/usr/bin/env python3

### IMPORTS ###
import enum
import logging

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
@enum.unique
class MarketIDByte(enum.Enum):
    NetworkCoordinator = 0x00
    Repeater = 0x01
    Submetering = 0xA0
    Security = 0xB2
    Environmental = 0xC0
    Universal = 0xFD

class TransmitterIdentifier:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        self._market_id = MarketIDByte.Universal
        self._serial_number = [0x00, 0x00, 0x00]

    def __str__(self):
        return "TXID: {:02X} {}".format(
            self._market_id.value,
            " ".join("{:02X}".format(a) for a in self._serial_number)
        )

    @property
    def bytes(self):
        return [self._market_id.value, self._serial_number[0], self._serial_number[1], self._serial_number[2]]

    @bytes.setter
    def bytes(self, value):
        if not isinstance(value, list):
            raise TypeError("Not a list of bytes")
        if len(value) != 4:
            raise ValueError("Incorrect number of bytes")
        try:
            self._market_id = MarketIDByte(value[0])
        except ValueError:
            raise ValueError("Invalid Market ID")
        for i in range(3):
            if value[i + 1] > 255:
                raise ValueError("Not bytes in list")
            self._serial_number[i] = value[i + 1]