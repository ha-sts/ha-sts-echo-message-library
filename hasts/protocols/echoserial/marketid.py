#!/usr/bin/env python3

### IMPORTS ###
import logging

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
class MarketID:
    _valid_values = {
        0x00: "Network Coordinator",
        0x01: "Repeater",
        0xA0: "Submetering",
        0xB2: "Security",
        0xC0: "Environmental",
        0xFD: "Universal"
    }

    _valid_names = {
        "Network Coordinator": 0x00,
        "Repeater": 0x01,
        "Submetering": 0xA0,
        "Security": 0xB2,
        "Environmental": 0xC0,
        "Universal": 0xFD
    }

    def __init__(self, input = None):
        self.logger = logging.getLogger(type(self).__name__)
        # Decode the input into a value
        self._value = 0xFD # Default universal value
        # - Check if MarketID and process/copy
        if isinstance(input, MarketID):
            self._value = input.value
        # - Check if bitslice/bitarray and process
        # FIXME: Should this even handle the bit slice / bit array directly?
        # - Check if integer and process
        elif isinstance(input, int) and input in self._valid_values.keys():
            self._value = input
        # - Check if string and process
        elif isinstance(input, str) and input in self._valid_names.keys():
            self._value = self._valid_names[input]
        # FIXME: Raise exception or use default?

    # Create a property for the value and for the name
    @property
    def name(self):
        return self._valid_values[self._value]

    # FIXME: Be able to set by name?

    @property
    def value(self):
        return self._value

    # FIXME: Be able to change value?

    # FIXME: Bitslice / bitarray?
