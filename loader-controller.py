#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2016 Stacey Sharp (github.com/ssharpjr)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# TODO: wo_monitor()
#       Periodically check if the captured work order is still current in RT.
# TODO: Setup the Gaylord switch.
# TODO: Pull PRESS_ID from /boot/pressid.txt


import os
import sys
import requests
from time import sleep
import json

import Adafruit_CharLCD as LCD
import Adafruit_GPIO.MCP230xx as MCP
import RPi.GPIO as IO  # For standard GPIO methods.


# CONSTANTS
DEBUG = True
PRESS_ID = '136'  # This does not change!


# Variables
api_url = 'http://10.130.0.42'  # Web API URL

# GPIO Setup
rst_btn = 18  # INPUT - Manually restart the program.
ir_pin = 23  # INPUT - Reads the outlet IR beam state.
ssr_pin = 24  # OUTPUT - Turns on the Solid State Relay.

IO.setmode(IO.BCM)
IO.setup(ssr_pin, IO.OUT, initial=0)

# Wire IR beam sensor from PIN to GND. Default state = False.
# The edge will RISE when a signal is present.
IO.setup(ir_pin, IO.IN, pull_up_down=IO.PUD_UP)

# Wire the restart button from PIN to 3V3.  Default state = True.
# The edge will FALL when pressed.
IO.setup(rst_btn, IO.IN, pull_up_down=IO.PUD_DOWN)


###############################################################################
# Setup the LCD and MCP.
###############################################################################
# Define the MCP pins connected to the LCD.
# Note: These are MCP pins, not RPI pins.
lcd_rs = 0
lcd_en = 1
lcd_d4 = 2
lcd_d5 = 3
lcd_d6 = 4
lcd_d7 = 5
lcd_red = 6
lcd_green = 7
lcd_blue = 8
lcd_columns = 20
lcd_rows = 4

# Initialize MCP23017 device using its default 0x20 I2C address.
gpio = MCP.MCP23017()

# Initialize the LCD using the pins.
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green,
                              lcd_blue, gpio=gpio)
###############################################################################


def lcd_ctrl(msg, color, clear=True):
    # Send instructions to the LCD.
    # Colors are Red, Green, Blue values.
    # all zeros equals off, all ones equals white
    color = color
    if clear:
        lcd.clear()
    if color == 'red':
        lcd.set_color(1.0, 0.0, 0.0)  # Red
    elif color == 'green':
        lcd.set_color(0.0, 1.0, 0.0)  # Green
    elif color == 'blue':
        lcd.set_color(0.0, 0.0, 1.0)  # Blue
    elif color == 'white':
        lcd.set_color(1.0, 1.0, 1.0)  # White
    elif color == 'off':
        lcd.set_color(0.0, 0.0, 0.0)  # Off
    else:
        lcd.set_color(0.0, 0.0, 0.0)  # Off
    lcd.message(msg)


def network_fail():
    if DEBUG:
        print("Failed to get data from API")
        print("System will restart in 10 seconds.")
    lcd_ctrl("NETWORK FAILURE\nIf this persists\ncontact TPI IT Dept.\nRestarting...", 'red')
    sleep(5)
    run_or_exit_program('run')


def get_wo_scan():
    lcd_ctrl("SCAN\n\nWORKORDER NUMBER", 'white')
    # wo_scan = '9934386'  # Should be 9934386 for test.
    wo_scan = input("Scan Workorder: ")
    # wo_scan = sys.stdin.readline().rstrip()
    return wo_scan


def wo_api_request(wo_id):
    # Notify user of potential pause
    lcd_ctrl("GETTING\nWORKORDER\nINFORMATION...", 'blue')

    url = api_url + '/wo/' + wo_id
    resp = requests.get(url=url, timeout=10)
    data = json.loads(resp.text)

    try:
        if data['error']:
            lcd_ctrl("INVALID WORKORDER!", 'red')
            if DEBUG:
                print("Invalid Workorder!  (data = error)")
            sleep(2)  # Pause so the user can read the error.
            run_or_exit_program('run')
    except:
        pass
    try:
        press_from_api_wo = data['press']
        rmat_from_api_wo = data['rmat']
        return press_from_api_wo, rmat_from_api_wo
    except:
        pass


def serial_api_request(sn):
    # Notify user of the potential pause
    lcd_ctrl("GETTING\nRAW MATERIAL\nSERIAL NUMBER\nINFORMATION...", 'blue')

    url = api_url + '/serial/' + sn
    resp = requests.get(url=url, timeout=10)
    data = json.loads(resp.text)

    try:
        if data['error']:
            lcd_ctrl("INVALID SERIAL\nNUMBER!", 'red')
            if DEBUG:
                print("Invalid Serial Number! (data = error)")
            sleep(2)  # Pause so the user can read the error.
            run_or_exit_program('run')
    except:
        pass
    try:
        rmat_from_api = data['itemno']
    except:
        pass
    return rmat_from_api


def get_rmat_scan():
    # Get the Raw Material Serial Number.
    # Check for the "S" qualifier.
    # Strip the qualifier is present and return the serial number.
    lcd_ctrl("SCAN\nRAW MATERIAL\nSERIAL NUMBER", 'white')
    # rmat_scan = 'S07234585' for test.
    rmat_scan = ''
    if DEBUG:
        rmat_scan = str(input("Scan Raw Material Serial Number: "))
    else:
        rmat_scan = str(input())
    if not rmat_scan.startswith('S'):
        lcd_ctrl("NOT A VALID\nSERIAL NUMBER!", 'red')
        if DEBUG:
            print("Not a Serial Number! (missing \"S\" qualifier)")
        sleep(2)  # Pause so the user can read the error.
        run_or_exit_program('run')
    rmat_scan = rmat_scan[1:]  # Strip off the "S" Qualifier.
    return rmat_scan


def wo_monitor(wo_id_from_wo):
    # Check if the workorder number changes (RT workorder unloaded).
    if DEBUG:
        print("Checking loaded workorder")
    wo_id = wo_id_from_wo
    url = api_url + '/wo_monitor/' + wo_id
    resp = requests.get(url=url, timeout=10)
    data = json.loads(resp.text)

    try:
        if data['error']:
            lcd_ctrl("WORKORDER CHANGED!\n\nRESTARTING", 'red')
            if DEBUG:
                print("Workorder changed! (data = error)")
            sleep(2)  # Pause so the user can read the error.
            run_or_exit_program('run')
    except:
        pass
    try:
        wo_id_from_api = data['wo_id']
    except:
        pass

    if wo_id_from_wo != wo_id_from_api:
        if DEBUG:
            print("Workorders do not match.  Restarting")
        run_or_exit_program('run')


def sensor_monitor():
    if IO.input(rst_btn) == 1:
        if DEBUG:
            print("Sensor detected.  Pallet moved")
        run_or_exit_program('run')


def start_loader():
    if DEBUG:
        print("\nEnergizing Loader")
    sleep(0.5)
    IO.output(ssr_pin, 1)  # Turn on the Solid State Relay.


def stop_loader():
    if DEBUG:
        print("\nDe-energizing Loader")
    sleep(0.5)
    IO.output(ssr_pin, 0)  # Turn off the Solid State Relay.


def restart_program():
    print("\nRestarting program")
    # sleep(1)
    IO.cleanup()
    os.execv(__file__, sys.argv)


def reboot_system():
    lcd.clear()
    lcd_ctrl("REBOOTING SYSTEM\n\nSTANDBY...", 'blue')
    IO.cleanup()
    os.system('sudo reboot')


def run_or_exit_program(status):
    if status == 'run':
       restart_program()
    elif status == 'exit':
        print("\nExiting")
        lcd.set_color(0, 0, 0)  # Turn off backlight
        lcd.clear()
        IO.cleanup()
        sys.exit()


def check_outlet_beam():
    beam = IO.input(ir_pin)
    if beam == 1:  # Beam connected.  Nothing is in the outlet.
        if DEBUG:
            print("\nOutlet IR beam is connected. (Nothing is plugged in)")
        lcd_ctrl("LOADER NOT FOUND!\n\nPlease check the\nLoader outlet", 'red')
        wait_for_beam()


def wait_for_beam():
    # Wait for beam to be broken again (beam == 0).
    beam = IO.input(ir_pin)
    while beam:
        beam = IO.input(ir_pin)
        sleep(1)

    beam = IO.input(ir_pin)
    print("\nLoader Outlet IR Beam state: " + str(beam) + " (Beam is broken)")
    print("Something is plugged into the loader outlet.  Let's proceed")
    restart_program()  # Restart the program (Break out of the input loop).


# Interrupt Callback function
def beam_cb(channel):
    if DEBUG:
        print("beam_cb() callback called")
    sleep(0.1)
    stop_loader()
    check_outlet_beam()


def rst_btn_cb(channel):
    if DEBUG:
        print("rst_btn_cb() callback called")
    sleep(0.1)
    stop_loader()
    lcd_ctrl("RESETTING\nLOADER\nCONTROLLER", 'white')
    sleep(1)
    restart_program()


###############################################################################
# Interrupts
# If the outlet beam is connected, stop everything until it disconnects.
# IO.add_event_detect(ir_pin, IO.RISING, callback=beam_cb)
# IO.add_event_detect(rst_btn, IO.FALLING, callback=rst_btn_cb, bouncetime=300)
# NOTE: Disabled because the IR sensor is picking up EMI and triggering.
###############################################################################


def run_mode():
    # Run a timed loop, checking the IR sensor and API
    c = 0  # Reset counter
    while True:
        if c == 10:  # Check the sensor every 10 seconds
            sensor_monitor()
        if c == 300:  # Check the API every 5 minutes
            wo_monitor(wo_id_from_wo)

        c = c + 1
        sleep(1)


###############################################################################
# Main
###############################################################################

def main():
    print()
    print("Starting Loader Controller Program")
    print("For Press " + PRESS_ID)
    lcd_msg ="LOADER CONTROLLER\n\n\nPRESS " + PRESS_ID
    lcd_ctrl(lcd_msg, 'white')
    sleep(1)


    # Request the Workorder Number (ID) Barcode.
    wo_id_from_wo = get_wo_scan()
    if DEBUG:
        print("Scanned Work Order: " + wo_id_from_wo)


    # Request Press Number and Raw Material Item Number from the API.
    if DEBUG:
        print("Requesting data from API")

    try:
        press_from_api_wo, rmat_from_api_wo = wo_api_request(wo_id_from_wo)
    except:
        network_fail()


    if DEBUG:
        print("Press Number from API: " + press_from_api_wo)
        print("RM Item Number from API: " + rmat_from_api_wo)


    # Verify the Press Number.
    if DEBUG:
        print("Checking if workorder is currently running on this press...")
    if press_from_api_wo == PRESS_ID:
        if DEBUG:
            print("Match.  Workorder: " + wo_id_from_wo +
                  " is running on Press #" + PRESS_ID)
            print("Good Workorder.  Continuing...")
    else:
        lcd_ctrl("INCORRECT\nWORKORDER!", 'red')
        if DEBUG:
            print("Incorrect Workorder!")
            print("This Workorder is for press: " + press_from_api_wo)
        sleep(2)  # Pause so the user can see the error.
        run_or_exit_program('run')


    # Scan the Raw Material Serial Number Barcode.
    serial_from_label = get_rmat_scan()
    if DEBUG:
        print("Serial Number from Label: " + serial_from_label)


    # Request Raw Material Item Number from the API.
    rmat_from_api_inv = serial_api_request(serial_from_label)
    if DEBUG:
      print("RM Item Number from API: " + rmat_from_api_inv)


    # Verify the Raw Material Item Number.
    if DEBUG:
        print("Checking if raw material matches this workorder...")
    if rmat_from_api_wo == rmat_from_api_inv:
        if DEBUG:
            print("Material matches workorder.  Continuing...")
            print("Starting the Loader!")

        start_loader()  # Looks good, turn on the loader.
        lcd_msg = "PRESS: " + PRESS_ID + "\nWORKORDER: " + wo_id_from_wo + "\n\nLOADER RUNNING"
        lcd_ctrl(lcd_msg, 'green')
        run_mode()   # Start the monitors
    else:
        if DEBUG:
            print("Invalid Material!")
        lcd_ctrl("INCORRECT\nMATERIAL!", 'red')
        sleep(2)  # Pause so the user can see the error.
        run_or_exit_program('run')


def run():
    while True:
        try:
            # check_outlet_beam()
            main()
        except KeyboardInterrupt:
            run_or_exit_program('exit')
        except:
            # stop_loader()
            print("GPIO Cleanup")
            IO.cleanup()


if __name__ == '__main__':
    run()
