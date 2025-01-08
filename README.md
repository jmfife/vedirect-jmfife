# VEDirect

This is a Python library for decoding the Victron Energy VE.Direct text protocol used in their range of MPPT solar 
charge controllers, battery monitors, and inverters.  
This is a forked version of a package originally created by Janne Kario (https://github.com/karioja/vedirect).

## Installation

To install directly from GitHub:

```
$ python3 -m pip install "git+https://github.com/Jordan-seebyte/vedirect-JL"
```

[NOT SURE IF THIS STILL WORKS] If you have cloned or forked the repo already to your local directory and want to use it in live (editable mode):
```
$ python3 -m pip install -e "."
```

If you want to build the repo into a whl file, run the following:

```
python setup.py bdist_wheel

```

If you want to build the repo into a tar.gz file, run the following:

```
python setup.py sdist

```
If you want to install the built library you can by doing the following:

```
python -m pip install [LOCATION OF THE TAR>.GZ or the WHL FILE]
```

## Check

Test both command line entry points:
```
$ vedirect_device_emulator --sph 3600 --n 2
VEDirect emulator running. Writing to <stdout>
b'\r\nV\t12800\r\nVPV\t3350\r\nPPV\t130\r\nI\t15000\r\nIL\t1500\r\nLOAD\tON\r\nRelay\tOFF\r\nH19\t456\r\nH20\t45\r\nH21\t300\r\nH22\t45\r\nH23\t350\r\nERR\t0\r\nCS\t5\r\nFW\t1.19\r\nPID\t0xA042\r\nSER#\tHQ141112345\r\nHSDS\t0\r\nMPPT\t2\r\nChecksum\t\x99'
b'\r\nV\t12800\r\nVPV\t3350\r\nPPV\t130\r\nI\t15000\r\nIL\t1500\r\nLOAD\tON\r\nRelay\tOFF\r\nH19\t456\r\nH20\t45\r\nH21\t300\r\nH22\t45\r\nH23\t350\r\nERR\t0\r\nCS\t5\r\nFW\t1.19\r\nPID\t0xA042\r\nSER#\tHQ141112345\r\nHSDS\t0\r\nMPPT\t2\r\nChecksum\t\x99'
Done

$ vedirect --emulate=mppt --n=2
{'V': 12800, 'VPV': 3350, 'PPV': 130, 'I': 15000, 'IL': 1500, 'LOAD': 'ON', 'Relay': 'OFF', 'H19': 456, 'H20': 45, 'H21': 300, 'H22': 45, 'H23': 350, 'ERR': 0, 'CS': 5, 'FW': '1.19', 'PID': '0xA042', 'SER#': 'HQ141112345', 'HSDS': 0, 'MPPT': 2}
{'V': 12800, 'VPV': 3350, 'PPV': 130, 'I': 15000, 'IL': 1500, 'LOAD': 'ON', 'Relay': 'OFF', 'H19': 456, 'H20': 45, 'H21': 300, 'H22': 45, 'H23': 350, 'ERR': 0, 'CS': 5, 'FW': '1.19', 'PID': '0xA042', 'SER#': 'HQ141112345', 'HSDS': 0, 'MPPT': 2}
```

## Quick Simulation

A simple command line test with a built-in emulator can be performend on any platform without
an actual VEDirect device using three commands launching three processes (e.g.
in three terminal windows on the same machine):

First, create a pair of virtual serial ports.
```
$ socat -d -d PTY,raw,echo=0,link=/tmp/vmodem0 PTY,raw,echo=0,link=/tmp/vmodem1
2020/04/13 16:20:43 socat[84720] N PTY is /dev/ttys005
2020/04/13 16:20:43 socat[84720] N PTY is /dev/ttys006
2020/04/13 16:20:43 socat[84720] N starting data transfer loop with FDs [5,5] and [7,7]
```

Run the VEDirect monitor with the default entry point to display packets to `stdio`.  In this case 
we note from the above output that we need to listen on `/dev/ttys006`:

```
% vedirect --port=/dev/ttys006
```

Next, run the emulator and set it to write to the first port (in this case `/dev/tty005`:

```
% vedirect_device_emulator --port=/dev/ttys005 --model="MPPT" --n=10 --sph=3600
VEDirect emulator eunning. Writing to serial port /dev/ttys005
```

In the first terminal window, we should begin to see the emulated data printed to `stdio`:

```
% vedirect --port=/dev/ttys006
{'V': 12800, 'VPV': 3350, 'PPV': 130, 'I': 15000, 'IL': 1500, 'LOAD': 'ON', 'Relay': 'OFF', 'H19': 456, 'H20': 45, 'H21': 300, 'H22': 45, 'H23': 350, 'ERR': 0, 'CS': 5, 'FW': '1.19', 'PID': '0xA042', 'SER#': 'HQ141112345', 'HSDS': 0, 'MPPT': 2}
{'V': 12800, 'VPV': 3350, 'PPV': 130, 'I': 15000, 'IL': 1500, 'LOAD': 'ON', 'Relay': 'OFF', 'H19': 456, 'H20': 45, 'H21': 300, 'H22': 45, 'H23': 350, 'ERR': 0, 'CS': 5, 'FW': '1.19', 'PID': '0xA042', 'SER#': 'HQ141112345', 'HSDS': 0, 'MPPT': 2}
{'V': 12800, 'VPV': 3350, 'PPV': 130, 'I': 15000, 'IL': 1500, 'LOAD': 'ON', 'Relay': 'OFF', 'H19': 456, 'H20': 45, 'H21': 300, 'H22': 45, 'H23': 350, 'ERR': 0, 'CS': 5, 'FW': '1.19', 'PID': '0xA042', 'SER#': 'HQ141112345', 'HSDS': 0, 'MPPT': 2}
...
```

You can also emulate vedirect output without using `vedirect_device_emulator`:
```
vedirect --emulate=mppt --n=2
{"V": 12800, "VPV": 3350, "PPV": 130, "I": 15000, "IL": 1500, "LOAD": "ON", "Relay": "OFF", "H19": 456, "H20": 45, "H21": 300, "H22": 45, "H23": 350, "ERR": 0, "CS": 5, "FW": "1.19", "PID": "0xA042", "SER#": "HQ141112345", "HSDS": 0, "MPPT": 2}
{"V": 12800, "VPV": 3350, "PPV": 130, "I": 15000, "IL": 1500, "LOAD": "ON", "Relay": "OFF", "H19": 456, "H20": 45, "H21": 300, "H22": 45, "H23": 350, "ERR": 0, "CS": 5, "FW": "1.19", "PID": "0xA042", "SER#": "HQ141112345", "HSDS": 0, "MPPT": 2}
```

## Original README.md

This package was forked from karioja at https://github.com/karioja/vedirect.
Below is the original README.md with describes use of some examples in the repo.


The test directory contains a set of live recordings of the serial port data sent by the 3 devices that I own.

* SmartSolar MPPT 100/20 running firmware version 1.39
* BlueSolar MPPT 75/15 running firmware version 1.23
* BVM 702 battery monitor running firmware version 3.08

These recordings can be fed to the Vedirect decoder using a pair of virtual serial ports. To create a pair of virtual serial ports issue the following command:
```
$ socat -d -d PTY,raw,echo=0,link=/tmp/vmodem0 PTY,raw,echo=0,link=/tmp/vmodem1
```
This will create 2 virtual serials ports connected to each other. Anything sent to /tmp/vmodem0 will be echoed to /tmp/vmodem1 and vice versa.

Attach the decoder to /tmp/vmodem1
```
python3 examples/vedirect_print.py --port /tmp/vmodem1
```

Feed the recording over to /tmp/vmodem0
```
$ cat test/bvm702.dump > /dev/vmodem0
```
There is no 1 second delay between the packets as there is with the real hardware. The above commands will flood the terminal with all of the data at once.