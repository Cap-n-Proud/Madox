# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time
import sys
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


from utils import get_ip_address
import ads1115 as ads1115
import ina219 as ina219
import os
import subprocess


# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node

# import board

from std_msgs.msg import String
from std_msgs.msg import Int32MultiArray, Int16
from sensor_msgs.msg import Joy

import time
import argparse

Charge = False


def ip_address(interface):
    try:
        if network_interface_state(interface) == "down":
            return None
        cmd = (
            "ifconfig %s | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'"
            % interface
        )
        return subprocess.check_output(cmd, shell=True).decode("ascii")[:-1]
    except:
        return None


def network_interface_state(interface):
    try:
        with open("/sys/class/net/%s/operstate" % interface, "r") as f:
            return f.read()
    except:
        return "down"  # default to down


class Display(Node):
    def __init__(self):
        super().__init__("Display")

        adress = os.popen(
            "i2cdetect -y -r 1 0x48 0x48 | egrep '48' | awk '{print $2}'"
        ).read()
        if adress == "48\n":
            ads = ads1115.ADS1115()
        else:
            ads = None

        adress = os.popen(
            "i2cdetect -y -r 1 0x41 0x41 | egrep '41' | awk '{print $2}'"
        ).read()
        if adress == "41\n":
            ina = ina219.INA219(addr=0x41)
        else:
            ina = None

        # 128x32 display with hardware I2C:
        disp = Adafruit_SSD1306.SSD1306_128_32(
            rst=None, i2c_bus=1, gpio=1
        )  # setting gpio to 1 is hack to avoid platform detection

        # Initialize library.
        disp.begin()

        # Clear display.
        disp.clear()
        disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = disp.width
        height = disp.height
        image = Image.new("1", (width, height))

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        top = padding
        bottom = height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0

        # Load default font.
        font = ImageFont.load_default()
        draw.text((x, top), "SETTING UP...", font=font, fill=255)

        self.joy_topic = self.create_subscription(Joy, "joy", self.joy_topic, 10)

    def joy_topic(self, msg):
        print(msg)

    def clear(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, width, height), outline=0, fill=0)

    def print_info(self):
        self.clear()
        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell=True)
        cmd = "free -m | awk 'NR==2{printf \"Mem:%s/%sMB %.1f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell=True)
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk:%d/%dGB %s", $3,$2,$5}\''
        Disk = subprocess.check_output(cmd, shell=True)

        # Write two lines of text.
        if ina != None:
            if ip_address("eth0") is not None:
                draw.text(
                    (x, top), "IP: " + str(ip_address("eth0")), font=font, fill=255
                )
            elif ip_address("wlan0") is not None:
                draw.text(
                    (x, top), "IP: " + str(ip_address("wlan0")), font=font, fill=255
                )
            else:
                draw.text((x, top), "IP: not available", font=font, fill=255)

            bus_voltage = ina.getBusVoltage_V()  # voltage on V- (load side)
            current = ina.getCurrent_mA()  # current in mA
            p = bus_voltage / 12.6 * 100
            if p > 100:
                p = 100
            if current > 30:
                Charge = not Charge
            else:
                Charge = False

            if Charge == False:
                draw.text((120, top), " ", font=font, fill=255)
            else:
                draw.text((120, top), "*", font=font, fill=255)
            draw.text(
                (x, top + 8),
                ("%.1fV") % bus_voltage
                + ("  %.2fA") % (current / 1000)
                + ("  %2.0f%%") % p,
                font=font,
                fill=255,
            )
            draw.text((x, top + 16), str(MemUsage.decode("utf-8")), font=font, fill=255)
            draw.text((x, top + 25), str(Disk.decode("utf-8")), font=font, fill=255)
        elif ads != None:
            value = ads.readVoltage(4) / 1000.0
            draw.text(
                (x, top), "eth0: " + str(get_ip_address("eth0")), font=font, fill=255
            )
            draw.text(
                (x, top + 8),
                "wlan0: " + str(get_ip_address("wlan0")),
                font=font,
                fill=255,
            )
            draw.text((x, top + 16), str(MemUsage.decode("utf-8")), font=font, fill=255)
            draw.text(
                (x, top + 25),
                str(Disk.decode("utf-8")) + (" %.1f") % value,
                font=font,
                fill=255,
            )
        else:
            draw.text(
                (x, top), "eth0: " + str(get_ip_address("eth0")), font=font, fill=255
            )
            draw.text(
                (x, top + 8),
                "wlan0: " + str(get_ip_address("wlan0")),
                font=font,
                fill=255,
            )
            draw.text((x, top + 16), str(MemUsage.decode("utf-8")), font=font, fill=255)
            draw.text((x, top + 25), str(Disk.decode("utf-8")), font=font, fill=255)
        # Display image.
        disp.image(image)
        disp.display()


def main(args=None):
    rclpy.init(args=args)

    oled = display()
    print("Node ready")
    oled.clear()
    rclpy.spin(oled)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    oled.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
