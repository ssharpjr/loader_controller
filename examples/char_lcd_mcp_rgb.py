#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Example using an RGB character LCD connected to an MCP23017 GPIO extender.

import sys
import time

import Adafruit_CharLCD as LCD
import Adafruit_GPIO.MCP230xx as MCP
import RPi.GPIO as io  # For standard GPIO methods.

# Define MCP pins connected to the LCD.
lcd_rs        = 0
lcd_en        = 1
lcd_d4        = 2
lcd_d5        = 3
lcd_d6        = 4
lcd_d7        = 5
lcd_red       = 6
lcd_green     = 7
lcd_blue      = 8

# Define LCD column and row size for 16x2 LCD.
# lcd_columns = 16
# lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
lcd_columns = 20
lcd_rows    = 4

# Initialize MCP23017 device using its default 0x20 I2C address.
gpio = MCP.MCP23017()

# Alternatively you can initialize the MCP device on another I2C address or bus.
# gpio = MCP.MCP23017(0x24, busnum=1)

# Initialize the LCD using the pins
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue,
                              gpio=gpio)

# Print a full 20x4 message
lcd.set_cursor(0, 0)
lcd.message('####################')
lcd.set_cursor(0, 1)
lcd.message('#   Hello          #')
lcd.set_cursor(0, 2)
lcd.message('#          World!  #')
lcd.set_cursor(0, 3)
lcd.message('####################')

# Wait 5 seconds
time.sleep(5.0)

# End demo here
# lcd.set_color(0, 0, 0)
# lcd.enable_display(False)
# io.cleanup()
# sys.exit()

# Demo showing the cursor.
lcd.clear()
lcd.show_cursor(True)
lcd.message('Show cursor')

time.sleep(5.0)

# Demo showing the blinking cursor.
lcd.clear()
lcd.blink(True)
lcd.message('Blink cursor')

time.sleep(5.0)

# Stop blinking and showing cursor.
lcd.show_cursor(False)
lcd.blink(False)

# Demo scrolling message right/left.
lcd.clear()
message = 'Scroll'
lcd.message(message)
for i in range(lcd_columns-len(message)):
    time.sleep(0.2)
    lcd.move_right()
for i in range(lcd_columns-len(message)):
    time.sleep(0.2)
    lcd.move_left()

# Show some colors
lcd.clear()
lcd.message('And now for some \n     RGB \n        colors!')
time.sleep(3.0)
lcd.set_color(1.0, 0.0, 0.0)  # Red
lcd.clear()
lcd.message('R E D')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 0.0)  # Green
lcd.clear()
lcd.message('G R E E N')
time.sleep(3.0)

lcd.set_color(0.0, 0.0, 1.0)  # Blue
lcd.clear()
lcd.message('B L U E')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 0.0)  # Yellow
lcd.clear()
lcd.message('Y E L L O W')
time.sleep(3.0)

lcd.set_color(0.0, 1.0, 1.0)  # Cyan
lcd.clear()
lcd.message('C Y A N')
time.sleep(3.0)

lcd.set_color(1.0, 0.0, 1.0)  # Magenta
lcd.clear()
lcd.message('M A G E N T A')
time.sleep(3.0)

lcd.set_color(1.0, 1.0, 1.0)  # White
lcd.clear()
lcd.message('W H I T E')
time.sleep(3.0)

# Demo turning backlight off and on.
lcd.clear()
lcd.message('Flash backlight\nin 5 seconds...')
time.sleep(5.0)
# Turn backlight off.
lcd.set_backlight(0)
time.sleep(2.0)
# Change message.
lcd.clear()
lcd.message('Goodbye!')
# Turn backlight on.
lcd.set_backlight(1)
time.sleep(2.0)
# Power down LCD
lcd.clear()
lcd.set_color(0.0, 0.0, 0.0)
lcd.set_backlight(0)
lcd.enable_display(False)
io.cleanup()

