# !/usr/bin/python
# -*- coding: utf-8 -*-

# An emulator for a Victron MPPT solar charge controller.
# sends output to a port.
#
# To re-route the port to another one for testing, Use `socat` to create linked virtual serial ports with:
# socat -d -d PTY,raw,echo=0,link=/tmp/vmodem0 PTY,raw,echo=0,link=/tmp/vmodem1
# https://github.com/karioja/vedirect
#
# Or, use `pty` as in:
# http://allican.be/blog/2017/01/15/python-dummy-serial-port.html
#
# The code below originated from https://github.com/karioja/vedirect
#
# 2020 JMF

import os, serial, time, argparse
import logging

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

model_default = "MPPT"


class VEDirectDeviceEmulator:
    models = ["ALL", "BMV_600", "BMV_700", "MPPT", "PHX_INVERTER"]
    data = {
        "ALL": {
            "V": "12800",
            "V2": "12802",
            "V3": "12803",
            "VS": "12200",
            "VM": "1280",
            "DM": "120",
            "VPV": "3350",
            "PPV": "130",
            "I": "15000",
            "IL": "1500",
            "LOAD": "ON",
            "T": "25",
            "P": "130",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1000001",
            "OR": "0x00000000",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H13": "0",
            "H14": "0",
            "H15": "11500",
            "H16": "14800",
            "H17": "34",
            "H18": "45",
            "H19": "456",
            "H20": "45",
            "H21": "300",
            "H22": "45",
            "H23": "350",
            "ERR": "0",
            "CS": "5",
            "BMV": "702",
            "FW": "1.19",
            "PID": "0x204",
            "SER#": "HQ141112345",
            "HSDS": "0",
            "MODE": "2",
            "AC_OUT_V": "23000",
            "AC_OUT_I": "50",
            "WARN": "1",
            "MPPT": "2",
        },
        "BMV_600": {
            "V": "12800",
            "VS": "12800",
            "I": "15000",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H13": "0",
            "H14": "0",
            "H15": "11500",
            "H16": "14800",
            "BMV": "702",
            "FW": "1.19",
        },
        "BMV_700": {
            "V": "12800",
            "VS": "12800",
            "VM": "1280",
            "DM": "120",
            "I": "15000",
            "T": "25",
            "P": "130",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H15": "11500",
            "H16": "14800",
            "H17": "34",
            "H18": "45",
            "BMV": "702",
            "FW": "1.19",
            "PID": "0x204",
        },
        "MPPT": {
            "V": "12800",
            "VPV": "3350",
            "PPV": "130",
            "I": "15000",
            "IL": "1500",
            "LOAD": "ON",
            "Relay": "OFF",
            "H19": "456",
            "H20": "45",
            "H21": "300",
            "H22": "45",
            "H23": "350",
            "ERR": "0",
            "CS": "5",
            "FW": "1.19",
            "PID": "0xA042",
            "SER#": "HQ141112345",
            "HSDS": "0",
            "MPPT": "2",
        },
        "PHX_INVERTER": {
            "AR": "1",
            "CS": "5",
            "FW": "1.19",
            "PID": "0xA201",
            "SER#": "HQ141112345",
            "MODE": "2",
            "AC_OUT_V": "23000",
            "AC_OUT_I": "50",
            "WARN": "1",
        },
    }

    def __init__(self, serialport, model="ALL"):
        """
        Constructor for Victron VEDirect device emulator.

        Args:
            serialport (str, int): Port to write to (or an integer file descriptor for testing)
            model (str): one of ['ALL', 'BMV_600', 'BMV_700', 'MPPT', 'PHX_INVERTER']
        """
        self.serialport = serialport
        self.model = model
        if isinstance(serialport, str):
            if not serialport:
                self.writer = print
            else:
                self.ser = serial.Serial(serialport, 19200, timeout=0)
                self.writer = self.ser.write
        else:
            # serialport must be file descriptor
            self.writer = self.writetofd

    def writetofd(self, s):
        """Write a file (for testing)"""
        os.write(self.serialport, s)

    def record_to_bytes(self, datadict):
        result = list()
        for key in self.data[self.model]:
            result.append(ord("\r"))
            result.append(ord("\n"))
            result.extend([ord(i) for i in key])
            result.append(ord("\t"))
            result.extend([ord(i) for i in datadict[key]])
        # checksum
        result.append(ord("\r"))
        result.append(ord("\n"))
        result.extend([ord(i) for i in "Checksum"])
        result.append(ord("\t"))
        result.append((256 - (sum(result) % 256)) % 256)
        return result

    def send_record(self):
        record = self.get_bytes()
        log.info(f"Sending: {record[:10]}...")
        self.writer(self.get_bytes())

    def get_record(self):
        return self.data[self.model]

    def get_bytes(self):
        return bytes(self.record_to_bytes(self.get_record()))

    def send_records(self, n=-1, samples_per_hour=720.0):
        """Send n records"""
        sleep_seconds = 3600.0 / float(samples_per_hour)
        while n != 0:
            self.send_record()
            time.sleep(sleep_seconds)
            if n != 0:
                n = n - 1


def main():
    parser = argparse.ArgumentParser(description="A simple VE.Direct emulator")
    parser.add_argument("--port", help="Serial port to write", type=str, default="")
    parser.add_argument(
        "--n",
        help="number of records to send (or default=-1 for infinite)",
        default=-1,
        type=int,
    )
    parser.add_argument(
        "--sph", default=60, help="samples per hour (default=False)", type=float
    )
    parser.add_argument(
        "--model",
        help="one of ['ALL', 'BMV_600', 'BMV_700', 'MPPT', 'PHX_INVERTER']",
        default=model_default,
        type=str,
    )
    args = parser.parse_args()
    if args.port:
        destination = f"serial port {args.port}"
    else:
        destination = f"<stdout>"
    print(f"VEDirect emulator running. Writing to {destination}")
    VEDirectDeviceEmulator(args.port, model=args.model).send_records(
        n=args.n, samples_per_hour=args.sph
    )
    print("Done")


if __name__ == "__main__":
    main()
