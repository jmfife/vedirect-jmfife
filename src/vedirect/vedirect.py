#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Forked from karioja at https://github.com/karioja/vedirect
#
# 2019-01-16 JMF Modified for Python 3 and updated protocol from
# https://www.sv-zanshin.com/r/manuals/victron-ve-direct-protocol.pdf


import sys
import logging

log = logging.getLogger("vedirect")
log.setLevel(logging.WARNING)


MICROPYTHON = False
# Protect for micropython version
if "micropython" in str(sys.implementation):
    MICROPYTHON = True

if not MICROPYTHON:
    import argparse
    import serial
else:
    from machine import UART

    try:
        from machine import Timer
    except ImportError as _:
        Timer = None


def int_base_guess(string_val):
    return int(string_val, 0)


class VEDirect:
    encoding = "utf-8"

    error_codes = {
        0: "No error",
        2: "Battery voltage too high",
        17: "Charger temperature too high",
        18: "Charger over current",
        19: "Charger current reversed",
        20: "Bulk time limit exceeded",
        21: "Current sensor issue (sensor bias/sensor broken)",
        26: "Terminals overheated",
        33: "Input voltage too high (solar panel)",
        34: "Input current too high (solar panel)",
        38: "Input shutdown (due to excessive battery voltage)",
        116: "Factory calibration data lost",
        117: "Invalid/incompatible firmware",
        119: "User settings invalid",
    }

    @staticmethod
    def conv_error(code):
        return VEDirect.error_codes[int(code)]

    device_state_map = {
        0: "Off",
        1: "Low power",
        2: "Fault",
        3: "Bulk",
        4: "Absorption",
        5: "Float",
        6: "Storage",
        7: "Equalize (manual)",
        9: "Inverting",
        11: "Power supply",
        245: "Starting-up",
        246: "Repeated absorption",
        247: "Auto equalize / Recondition",
        248: "BatterySafe",
        252: "External Control",
    }

    @staticmethod
    def conv_mode(code):
        return VEDirect.device_state_map[int(code)]

    cs = {"0": "Off", "2": "Fault", "3": "Bulk", "4": "Abs", "5": "Float"}

    offReasonDecode = {
        0x000: "",
        0x001: "No input power",
        0x002: "Switched off (power switch)",
        0x004: "Switched off (device mode register)",
        0x008: "Remote input",
        0x010: "Protection active",
        0x020: "Paygo",
        0x040: "BMS",
        0x080: "Engine shutdown detection",
        0x100: "Analyzing input voltage",
    }

    capBleDecode = {
        0x001: "BLE supports switching off",
        0x002: "BLE switching off is permanent",
    }

    trackerModeDecode = {
        0x000: "Off",
        0x001: "Voltage or current limited",
        0x002: "MPPT Tracker active",
    }

    alarmReasonDecode = {
        "Low Voltage": 1 << 0,  # 1  0b00000000000001
        "High Voltage": 1 << 1,  # 2  0b00000000000010
        "Low SOC": 1 << 2,  # 4  0b00000000000100
        "Low Starter Voltage": 1 << 3,  # 8  0b00000000001000
        "High Starter Voltage": 1 << 4,  # 16  0b00000000010000
        "Low Temperature": 1 << 5,  # 32  0b00000000100000
        "High Temperature": 1 << 6,  # 64  0b00000001000000
        "Mid Voltage": 1 << 7,  # 128  0b00000010000000
        "Overload": 1 << 8,  # 256  0b00000100000000
        "DC-ripple": 1 << 9,  # 512  0b00001000000000
        "Low V AC out": 1 << 10,  # 1024  0b00010000000000
        "High C AC out": 1 << 11,  # 2048  0b00100000000000
        "Short Circuit": 1 << 12,  # 4096  0b01000000000000
        "BMS Lockout": 1 << 13,  # 8192  0b10000000000000
    }

    @staticmethod
    def lookup(key_int, lookup_list):
        if key_int in lookup_list:
            return lookup_list[key_int]
        else:
            return ""

    values = {
        "LOAD": {"key": "load"},
        "H19": {"key": "yieldTotal", "mx": 0.01},
        "VPV": {"key": "panelVoltage", "mx": 0.001},
        "ERR": {"key": "error", "f": conv_error},
        "FW": {"key": "firmwareVersion", "mx": 0.01},
        "I": {"key": "current", "mx": 0.001},
        "H21": {"key": "maximumPowerToday", "f": int},  # W
        "IL": {"key": "loadCurrent", "mx": 0.001},
        "PID": {"key": "productId"},
        "H20": {"key": "yieldToday", "mx": 0.01},  # kWh
        "H23": {"key": "maximumPowerYesterday", "f": int},  # W
        "H22": {"key": "yieldYesterday", "mx": 0.01},  # kWh
        "HSDS": {"key": "daySequenceNumber", "f": int},
        "SER#": {"key": "serialNumber"},
        "V": {"key": "batteryVoltage", "mx": 0.001},
        "CS": {"key": "mode", "f": conv_mode},
        "PPV": {"key": "panelPower", "f": int},
    }

    divs = {
        "batteries_hdg": ["bmv", "SOC"],
        "batteries_bdy": ["bmv", "V", "I"],
        "solar_hdg": ["mppt", "I"],
        "solar_bdy": ["mppt", "V", "CS", "H20"],
        "vehicle_hdg": ["bmv", "VS"],
        "vehicle_bdy": ["bmv", "Relay"],
        "conv_hdg": ["conv", "I"],
        "conv_bdy": ["conv", "V", "T"],
    }

    units = {
        "V": "mV",
        "V2": "mV",
        "V3": "mV",
        "VS": "mV",
        "VM": "mV",
        "DM": "%",
        "VPV": "mV",
        "PPV": "W",
        "I": "mA",
        "I2": "mA",
        "I3": "mA",
        "IL": "mA",
        "LOAD": "",
        "T": "°C",
        "P": "W",
        "CE": "mAh",
        "SOC": "%",
        "TTG": "Minutes",
        "Alarm": "",
        "Relay": "",
        "AR": "",
        "OR": "",
        "H1": "mAh",
        "H2": "mAh",
        "H3": "mAh",
        "H4": "",
        "H5": "",
        "H6": "mAh",
        "H7": "mV",
        "H8": "mV",
        "H9": "Seconds",
        "H10": "",
        "H11": "",
        "H12": "",
        "H15": "mV",
        "H16": "mV",
        "H17": "0.01 kWh",
        "H18": "0.01 kWh",
        "H19": "0.01 kWh",
        "H20": "0.01 kWh",
        "H21": "W",
        "H22": "0.01 kWh",
        "H23": "W",
        "ERR": "",
        "CS": "*",
        "BMV": "",
        "FW": "",
        "FWE": "",
        "PID": "",
        "SER#": "",
        "HSDS": "",
        "MODE": "",
        "AC_OUT_V": "0.01 V",
        "AC_OUT_I": "0.1 A",
        "AC_OUT_S": "VA",
        "WARN": "",
        "MPPT": "",
    }

    types = {
        "V": int,
        "VS": int,
        "VM": int,
        "DM": int,
        "VPV": int,
        "PPV": int,
        "I": int,
        "IL": int,
        "LOAD": str,
        "T": int,
        "P": int,
        "CE": int,
        "SOC": int,
        "TTG": int,
        "Alarm": str,
        "Relay": str,
        "AR": int_base_guess,
        "OR": int_base_guess,
        "H1": int,
        "H2": int,
        "H3": int,
        "H4": int,
        "H5": int,
        "H6": int,
        "H7": int,
        "H8": int,
        "H9": int,
        "H10": int_base_guess,
        "H11": int_base_guess,
        "H12": int_base_guess,
        "H13": int_base_guess,
        "H14": int_base_guess,
        "H15": int,
        "H16": int,
        "H17": int,
        "H18": int,
        "H19": int,
        "H20": int,
        "H21": int,
        "H22": int,
        "H23": int,
        "ERR": int_base_guess,
        "CS": int_base_guess,
        "BMV": str,
        "FW": str,
        "PID": str,
        "SER#": str,
        "HSDS": int_base_guess,
        "MODE": int_base_guess,
        "AC_OUT_V": int,
        "AC_OUT_I": int,
        "AC_OUT_S": int,
        "WARN": int_base_guess,
        "MPPT": int_base_guess,
    }

    @staticmethod
    def typecast(payload_dict):
        new_dict = {}
        for key, val in payload_dict.items():
            try:
                new_dict[key] = VEDirect.types[key](val)
            except KeyError as exc:
                log.warning("Got unknown VE key: {}, skipping...".format(key))
        return new_dict

    fmt = {
        "%": ["%", 10, 1],
        "°C": ["°C", 1, 0],
        "0.01 kWh": ["Wh", 0.1, 2],
        "mA": ["A", 1000, 2],
        "mAh": ["Ah", 1000, 2],
        "Minutes": ["Mins", 1, 0],
        "mV": ["V", 1000, 2],
        "Seconds": ["Secs", 1, 0],
        "W": ["W", 1, 0],
    }

    # A list of received but not consumed records
    _buff_records = list()

    def __init__(self, serialport, timeout=60):
        """Constructor for a Victron VEDirect serial communication session.

        Params:
            serialport (str or "io.IOBase"): The name or number of the serial port to open OR
                an already opened interface that adheres the serial interface
            timeout (float): Read timeout value (seconds)
        """
        if isinstance(serialport, str):
            log.debug("VEDirect init opening serial port: {}".format(serialport))
            self.serialport = serialport
            if MICROPYTHON:
                if "xbee" in sys.platform:
                    self.ser = UART(
                        int(serialport), baudrate=19200, timeout=timeout * 1000
                    )
                    # Docs are unclear if you need to call init.
                    self.ser.init(baudrate=19200, timeout=timeout * 1000)
                else:
                    self.ser = UART(int(serialport))  # E.g. for fipy 0,1, or 2
                    self.ser.init(baudrate=19200, timeout_chars=10)
            else:
                self.ser = serial.Serial(
                    port=serialport, baudrate=19200, timeout=timeout
                )
        else:
            log.debug(
                "VEDirect init using passed in serial port: {}".format(str(serialport))
            )
            self.serialport = str(serialport)
            self.ser = serialport

        self.header1 = b"\n"
        self.header2 = b"\r"
        self.hexmarker = b":"
        self.delimiter = b"\t"
        self.key = b""
        self.value = b""
        self.bytes_sum = 0
        self.state = self.WAIT_HEADER1
        self.dict = {}
        if not MICROPYTHON:
            if hasattr(self.ser, "flushInput"):
                self.ser.flushInput()
            else:
                # Changed in pyserial>=3.0
                self.ser.reset_input_buffer()

    (HEX, WAIT_HEADER1, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(5)

    def _input(self, byte):
        """Accepts a new byte and tries to finish constructing a record.
        When a record is complete, it will be returned as a dictionary
        """
        log.debug("State: {}, Input: {}".format(self.state, byte))
        if byte == self.hexmarker and self.state != self.IN_CHECKSUM:
            log.debug("Changing to HEX state")
            self.state = self.HEX

        if self.state is not self.HEX:
            self.bytes_sum += ord(byte)
            if byte == b"\r":
                # Ignore these, they are optional. Do count towards CRC!
                log.debug("Skipping carriage return")
                return None

        if self.state == self.WAIT_HEADER1:
            if byte == self.header1:
                log.debug("Found header1")
                self.state = self.IN_KEY
            return None
        elif self.state == self.IN_KEY:
            if byte == self.delimiter:
                log.debug("Found delimiter")
                if self.key == b"Checksum":
                    log.debug("Found Checksum")
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += byte
            return None
        elif self.state == self.IN_VALUE:
            if byte == self.header1:
                log.debug("Found header1, ending value read")
                try:
                    self.dict[str(self.key.decode(self.encoding))] = str(
                        self.value.decode(self.encoding)
                    )
                except UnicodeError:
                    log.warning(
                        "Could not decode key {} and value {}".format(
                            self.key, self.value
                        )
                    )
                self.key = b""
                self.value = b""
                self.state = self.IN_KEY
            else:
                self.value += byte
            return None
        elif self.state == self.IN_CHECKSUM:
            log.debug(
                "Checking checksum... Current {}, CRC {}".format(
                    self.bytes_sum % 256, ord(byte)
                )
            )
            self.key = b""
            self.value = b""
            self.state = self.WAIT_HEADER1
            if self.bytes_sum % 256 == 0:
                self.bytes_sum = 0
                dict_copy = self.dict.copy()
                self.dict = {}  # clear the holder - ready for a new record
                return dict_copy
            else:
                # print('Malformed record')
                log.debug(
                    "Malformed record, Remainder: {}".format(self.bytes_sum % 256)
                )
                self.bytes_sum = 0
        elif self.state == self.HEX:
            log.warning("_input is in HEX state. Current byte: {}, current value: {}".format(byte, self.value))
            self.bytes_sum = 0
            if byte == self.header2:
                self.state = self.WAIT_HEADER1
        else:
            raise AssertionError()

    def read(self):
        """
        Check for input buffer, process if present, return record if complete. Non-blocking
        """
        if not MICROPYTHON:
            raise NotImplementedError()
        input_buf_len = self.ser.any()
        if input_buf_len:
            input_buf = self.ser.read(input_buf_len)
            for byte in input_buf:
                record = self._input(byte.to_bytes(1, sys.byteorder))
                if record is not None:
                    record = self.typecast(record)
                    self._buff_records.append(record)
        try:
            return self._buff_records.pop()
        except IndexError:
            return None

    def read_data_single(self, flush=True, timeout=None):
        """Wait until we get a single complete record, then return it. Optional timeout in ms"""
        timer = None
        if flush and not MICROPYTHON:
            self.ser.flushInput()
        if timeout and MICROPYTHON and Timer:
            timer = Timer.Chrono()
            timer.start()
        while True:
            if timer and timer.read_ms() > timeout:
                log.debug("Timed out")
                return None
            byte = self.ser.read(1)
            if byte:
                # log.debug("Read: {}".format(byte))
                # got a byte (didn't time out)
                record = self._input(byte)
                if record is not None:
                    return self.typecast(record)


def main():
    # provide a simple entry point that streams data from a VEDirect device to stdout
    parser = argparse.ArgumentParser(
        description="Read VE.Direct device and stream data to stdout"
    )
    parser.add_argument("--port", help="Serial port to read from", type=str, default="")
    parser.add_argument(
        "--n",
        help="number of records to read (or default=-1 for infinite)",
        default=-1,
        type=int,
    )
    parser.add_argument(
        "--timeout", help="Serial port read timeout, seconds", type=int, default="60"
    )
    parser.add_argument(
        "--loglevel",
        help="logging level - one of [DEBUG, INFO, WARNING, ERROR, CRITICAL]",
        default="ERROR",
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel.upper())
    if not args.port:
        print("Must specify a port to listen.")
        raise ValueError("Must give a port")
    ve = VEDirect(args.port, args.timeout)
    ve.read_data_callback(print_data_callback, args.n)


if __name__ == "__main__" and not MICROPYTHON:
    main()
