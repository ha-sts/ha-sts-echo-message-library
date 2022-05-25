#!/usr/bin/env python3

### IMPORTS ###
import logging
import queue
import random
import serial
import signal
import threading
import time

### GLOBALS ###
COM_PORT = "COM5"
COM_BAUD = 9600
COM_TOUT = 2

SHUTDOWN = False

### FUNCTIONS ###
def sigint_handler(signal, frame):
    global SHUTDOWN
    SHUTDOWN = True

### CLASSES ###
class SerialReader(threading.Thread):
    def __init__(self, comport, baudrate, timeout, output):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._shutdown = False
        self._comport = comport
        self._baudrate = baudrate
        self._timeout = timeout
        #self.queue = queue.SimpleQueue()
        self._queue = output

    def run(self):
        self.logger.debug("Starting the SerialReader thread.")
        with serial.Serial(self._comport, self._baudrate, timeout = self._timeout) as ser:
            while not self._shutdown:
                tmp_bytes = ser.read(32)
                self.logger.debug("Serial Bytes (up to 32): %s", tmp_bytes.hex())
                # Append bytes to a fifo
                for tmp_byte in tmp_bytes:
                    self._queue.put(tmp_byte)
        self.logger.debug("Ending the SerialReader thread.")

    def stop(self):
        self.logger.debug("Shutting down SerialReader thread.")
        self._shutdown = True


class SerialFaker(threading.Thread):
    fake_packets = [
        [114, 24, 192, 152, 34, 225, 0, 118, 173, 117, 0, 0, 60, 42, 66, 145, 172, 204, 68, 11, 0, 8, 77, 77, 31],
        [114, 24, 192, 152, 34, 225, 0, 118, 173, 117, 0, 0, 60, 42, 66, 145, 57, 154, 68, 11, 0, 8, 78, 78, 124],
        [114, 24, 192, 152, 34, 225, 0, 118, 173, 117, 0, 0, 60, 42, 66, 145, 115, 51, 68, 11, 0, 8, 79, 79, 81],
        [114, 24, 192, 152, 34, 225, 0, 118, 173, 117, 0, 0, 60, 42, 66, 145, 172, 204, 68, 11, 0, 8, 78, 72, 27]
    ]
    def __init__(self, bytes_output):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._shutdown = False
        self._queue = bytes_output

    def run(self):
        self.logger.debug("Starting the SerialFaker thread.")
        while not self._shutdown:
            tmp_bytes = self.fake_packets[random.randrange(len(self.fake_packets))]
            self.logger.debug("Serial Faker Bytes: %s", tmp_bytes)
            # Append bytes to a fifo
            for tmp_byte in tmp_bytes:
                self._queue.put(tmp_byte)
            time.sleep(3)
        self.logger.debug("Ending the SerialFaker thread.")

    def stop(self):
        self.logger.debug("Shutting down SerialFaker thread.")
        self._shutdown = True

class MessagePacketizer(threading.Thread):
    start_bytes = [0x72]

    def __init__(self, bytes_input, packet_output):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._shutdown = False
        self._input = bytes_input
        self._output = packet_output

    def run(self):
        self.logger.debug("Starting the MessagePacketizer thread.")
        tmp_buffer = []
        while not self._shutdown:
            # Get a byte from the queue
            try:
                tmp_buffer.append(int(self._input.get(timeout = 1))) # Should get a bytes object with one byte
            except queue.Empty:
                pass # NOTE: This is a poor way to do this, but this is quick.

            # Check for a valid start value
            if len(tmp_buffer) > 0 and tmp_buffer[0] not in self.start_bytes:
                tmp_buffer.pop(0)

            # Check the length byte
            if len(tmp_buffer) > 1 and tmp_buffer[0] in self.start_bytes:
                #self.logger.debug("Have a second byte, so checking length.")
                # Get the number of bytes for length
                tmp_length = tmp_buffer[1]

                # Check the checksum
                if len(tmp_buffer) > tmp_length:
                    self.logger.debug("Have enough bytes to check the packet.")
                    self.logger.debug("tmp_length: %d", tmp_length)
                    self.logger.debug("tmp_buffer: %s", tmp_buffer)

                    tmp_checksum = 0
                    for i in range(tmp_length):
                        tmp_checksum = (tmp_checksum + tmp_buffer[i]) % 256
                    self.logger.debug("Checksum byte: 0x%x, calc: 0x%x", tmp_buffer[tmp_length], tmp_checksum)
                    if tmp_checksum == tmp_buffer[tmp_length]:
                        self.logger.debug("Checksum valid.  Passing packet.")
                        # If valid packet
                        self._output.put(tmp_buffer[:tmp_length + 1])
                        # pass to output
                        for i in range(tmp_length + 1):
                            tmp_buffer.pop(0) # NOTE: This could be made a slice to be more efficient
                    else:
                        self.logger.debug("Checksum INVALID.  Rejecting first byte.")
                        # If not, check bad packet for another starter
                        tmp_buffer.pop(0)
        self.logger.debug("Ending the MessagePacketizer thread.")

    def stop(self):
        self.logger.debug("Shutting down MessagePacketizer thread.")
        self._shutdown = True

class MessageDecoder(threading.Thread):
    def __init__(self, packet_input, msg_output):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._shutdown = False
        self._input = packet_input
        self._output = msg_output

    def run(self):
        self.logger.debug("Starting the MessageDecoder thread.")
        while not self._shutdown:
            time.sleep(1)
        self.logger.debug("Ending the MessageDecoder thread.")

    def stop(self):
        self.logger.debug("Shutting down MessageDecoder thread.")
        self._shutdown = True

class MessagePrinter(threading.Thread):
    def __init__(self, msg_input):
        self.logger = logging.getLogger(type(self).__name__)
        super().__init__()
        self._shutdown = False
        self._input = msg_input

    def run(self):
        self.logger.debug("Starting the MessagePrinter thread.")
        while not self._shutdown:
            try:
                tmp_msg = self._input.get(timeout = 1)
                self.logger.info("Message: %s", tmp_msg)
            except queue.Empty:
                pass # NOTE: This is a poor way to do this, but this is quick.
        self.logger.debug("Ending the MessagePrinter thread.")

    def stop(self):
        self.logger.debug("Shutting down MessagePrinter thread.")
        self._shutdown = True

def main():
    # Gather settings
    # FIXME: Should this use ENVs, argparse, or a config file?

    # Setup logging
    debug_logging = True
    log_format = "%(asctime)s:%(levelname)s:%(name)s.%(funcName)s: %(message)s"
    logging.basicConfig(
        format = log_format,
        level = (logging.DEBUG if debug_logging else logging.INFO)
    )

    # Create the needed threads
    q_bytes = queue.SimpleQueue()
    q_packets = queue.SimpleQueue()
    q_messages = queue.SimpleQueue()

    tmp_threads = []
    tmp_threads.append(SerialReader(COM_PORT, COM_BAUD, COM_TOUT, q_bytes))
    tmp_threads.append(SerialFaker(q_bytes))
    tmp_threads.append(MessagePacketizer(q_bytes, q_packets))
    tmp_threads.append(MessageDecoder(q_packets, q_messages))
    tmp_threads.append(MessagePrinter(q_messages))

    # Start the threads and grab hold of the keyboard interrupt signal
    signal.signal(signal.SIGINT, sigint_handler)
    for tmp_th in tmp_threads:
        tmp_th.start()

    # Wait for the shutdown signal
    while not SHUTDOWN:
        time.sleep(1)

    # Stop all of the threads and wait for them to finish.
    logging.debug("Shutting down.")
    for tmp_th in tmp_threads:
        tmp_th.stop()
    logging.debug("Threads stopped.")
    for tmp_th in tmp_threads:
        tmp_th.join()
    logging.debug("Threads ended.")

if __name__ == "__main__":
    main()
