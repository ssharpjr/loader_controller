#!/usr/bin/env python3

import sys
from time import sleep
import RPi.GPIO as io

io.setmode(io.BCM)

io.setup(23, io.IN, pull_up_down=io.PUD_UP)


print("Checking IR Sensor")
while True:
    try:
        if io.input(23) == 1:
            print("IR Detected")
            sleep(0.1)
        elif io.input(23) == 0:
            print("IR Not Detected")
            sleep(0.1)
    except KeyboardInterrupt:
        io.cleanup()
        sys.exit()
