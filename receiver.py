# http://www.varesano.net/blog/fabio/serial%20rs232%20connections%20python
# install pySerial

import serial
from serial.tools import list_ports
import time

def choose_comport():
    coms = list_ports.comports(True)
    if not len(coms):
        print("No COM-devices available.\n")
        return

    val = 0
    while not val:
        print("Available COM-devices:")
        for _, com in zip(range(1,len(coms)+1), coms):
            print("{}: {}".format(_, com))
        val = int(input("Select COM-device: "))
        if val-1 not in range(len(coms)):
            print("Wrong value. Please try again.")
            val = 0
        print()

    return coms[val-1]
    

print(choose_comport())