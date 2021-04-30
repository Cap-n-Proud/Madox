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

from std_msgs.msg import String
from std_msgs.msg import Int32MultiArray, Int16
from sensor_msgs.msg import Joy

import time
import argparse


# https://github.com/adafruit/Adafruit_CircuitPython_MotorKit.git


class Robot(Node):
    def __init__(
        self,
        simulation=False,
        debug=False,
        steer_gain=0.5,
        speed_limit=0.3,
        left_trim=0,
        right_trim=0,
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
            from adafruit_motorkit import MotorKit

            self.kit = MotorKit()

    def set_steer_gain(self, steer_gain):
        self.steer_gain = steer_gain

    def set_speed_limit(self, speed_limit):
        self.speed_limit = speed_limit

    def set_left_trim(self, left_trim):
        self.left_trim = left_trim

    def set_right_trim(self, right_trim):
        self.right_trim = right_trim

    def move(self, x, y):
        speedL = (
            max(
                -self.speed_limit,
                min(self.speed_limit, float(y) + self.steer_gain * float(x)),
            )
            + self.left_trim
        )
        speedR = (
            max(
                -self.speed_limit,
                min(self.speed_limit, float(y) - self.steer_gain * float(x)),
            )
            + self.right_trim
        )
        if self.simulation:
            self.get_logger().info('Left speed se to: "%s"' % speedL)
            self.get_logger().info('Right speed se to: "%s"' % speedR)
        else:
            kit.motor1.throttle = max(-1, min(1, speedL))
            kit.motor2.throttle = max(-1, min(1, speedR))

    def joy_topic(self, msg):
        if self.debug:
            self.get_logger().info(
                "joy X: " + str(msg.axes[0]) + " Y: " + str(msg.axes[1])
            )
        if msg.axes[0] != 0 or msg.axes[1] != 0:
            self.move(msg.axes[0], msg.axes[1])

    def joy_web(self, msg):
        speed = msg.data.split(",")
        self.move(speed[0], speed[1])


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
