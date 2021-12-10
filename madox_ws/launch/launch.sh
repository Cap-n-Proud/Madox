#!/bin/bash
sudo mount 192.168.1.121:/mnt/VDev/Software Software
sudo chmod 777 /dev/i2c-1
sudo usermod -aG i2c $USER

cd /home/robot/Software/ROS2/Madox/madox_ws
source /opt/ros/foxy/setup.bash
. install/local_setup.bash

ros2 run jetbot_oled_display ros2_jetbot_oled_display &
ros2 run jetbot_drive ros2_jetbot_drive &
ros2 run oled_display display &
ros2 run ros2_rtimulib ros2_imu_node &
ros2 run jetbot_sys_info ros2_jetbot_sys_info &
ros2 run camera ros2_camera --width 640 --height 480 &
