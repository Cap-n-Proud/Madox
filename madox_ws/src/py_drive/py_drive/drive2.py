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
import board

from std_msgs.msg import String
from std_msgs.msg import Int32MultiArray, Int16
from sensor_msgs.msg import Joy

import time
import argparse

import traitlets
from traitlets.config.configurable import SingletonConfigurable


class Robot(Node, SingletonConfigurable):
    def __init__(
        self,
        simulation=False,
        debug=False,
        steer_gain=0.4,
        speed_limit=0.3,
        left_trim=-0,
        right_trim=0,
        *args,
        **kwargs
    ):
        super().__init__("robot")

        self.steer_gain = steer_gain
        self.speed_limit = speed_limit
        self.left_trim = left_trim
        self.right_trim = right_trim
        self.simulation = simulation
        self.debug = debug
        self.joy_topic = self.create_subscription(Joy, "joy", self.joy_topic, 10)
        self.joy_web = self.create_subscription(String, "joy_web", self.joy_web, 10)
        if not self.simulation:
            from Adafruit_MotorHAT import Adafruit_MotorHAT
            from .motor import Motor

            self.left_motor = traitlets.Instance(Motor)
            self.right_motor = traitlets.Instance(Motor)
            self.i2c_bus = traitlets.Integer(default_value=1).tag(config=True)
            self.left_motor_channel = traitlets.Integer(default_value=1).tag(
                config=True
            )
            self.left_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)
            self.right_motor_channel = traitlets.Integer(default_value=2).tag(
                config=True
            )
            self.right_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)

            self.motor_driver = Adafruit_MotorHAT(i2c_bus=self.i2c_bus)
            self.left_motor = Motor(
                self.motor_driver,
                channel=self.left_motor_channel,
                alpha=self.left_motor_alpha,
            )
            self.right_motor = Motor(
                self.motor_driver,
                channel=self.right_motor_channel,
                alpha=self.right_motor_alpha,
            )

    def set_steer_gain(self, steer_gain):
        self.steer_gain = steer_gain

    def set_speed_limit(self, speed_limit):
        self.speed_limit = speed_limit

    def set_left_trim(self, left_trim):
        self.left_trim = left_trim

    def set_right_trim(self, right_trim):
        self.right_trim = right_trim

    def move(self, speed, steer):
        if abs(float(speed)) > 0 or abs(float(steer)) > 0:
            speed_l = float(speed) + self.steer_gain * float(steer) - self.left_trim
            speed_r = float(speed) - self.steer_gain * float(steer) - self.right_trim
            if abs(speed_l) > self.speed_limit:
                speed_l = (speed_l / abs(speed_l)) * self.speed_limit
            if abs(speed_r) > self.speed_limit:
                speed_r = (speed_r / abs(speed_r)) * self.speed_limit
            self.left_motor.value = speed_l
            self.right_motor.value = speed_r

            # print(speed, steer, speed_l, speed_r)

    def joy_topic(self, msg):
        if self.debug:
            self.get_logger().info(
                "joy X: " + str(msg.axes[0]) + " Y: " + str(msg.axes[1])
            )
        if abs(msg.axes[0]) >= 0.1 or abs(msg.axes[1]) >= 0.1:
            self.move(msg.axes[1], msg.axes[0])
        else:
            if self.debug:
                self.get_logger().info("Motors stopped")

            self.move(0, 0)

        if msg.axes[7] != 0:
            self.move(msg.axes[7] * self.speed_limit - self.left_trim)
            self.move(-msg.axes[7] * self.speed_limit - self.left_trim)
        if msg.axes[6] != 0:
            self.move(msg.axes[6] * self.speed_limit - self.left_trim)
            self.move(-msg.axes[6] * self.speed_limit - self.left_trim)
        if msg.buttons[2] == 1:
            self.kit.motor1.throttle = 0
            self.kit.motor2.throttle = 0

    def joy_web(self, msg):
        speed = msg.data.split(",")
        self.move(speed[0], speed[1])
        # print(msg.data)


def main(args=None):
    rclpy.init(args=args)
    # Construct an argument parser
    parser = argparse.ArgumentParser()

    # Add arguments to the parser
    parser.add_argument(
        "-s",
        "--simulation",
        required=False,
        action="store_true",
        default=False,
        help="Simulation mode: motors are not imported, a message is displayed to simuate the signal",
    )
    parser.add_argument(
        "-d",
        "--debug",
        required=False,
        action="store_true",
        default=False,
        help="Debug mode: robot will print extra log info in teh console",
    )

    args = parser.parse_args()
    robot = Robot(simulation=args.simulation, debug=args.debug)
    print("Robot ready")
    if args.simulation:
        print("Running simulation")

    if args.debug:
        print("Debug mode")

    rclpy.spin(robot)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    robot.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()