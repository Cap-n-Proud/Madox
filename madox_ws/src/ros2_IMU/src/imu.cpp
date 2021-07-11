/*
   The MIT License (MIT)
   Copyright (c) 2019 Techno Road Inc.
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
   The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   THE SOFTWARE.
 */
#include <chrono>
#include <iostream>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_msgs/msg/tf_message.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h> // for use tf2::Quaternion
// #include <diagnostic_updater/diagnostic_updater.hpp>

#include <RTIMULib.h>


using namespace std::chrono_literals;

class ImuNode : public rclcpp::Node {
public:

  explicit ImuNode(const rclcpp::NodeOptions& op)
    : Node("imu", op) {
    InitParam();

    // std::cout << "Inizializing" << "\n";
    RCLCPP_INFO(this->get_logger(), "Inizializing");
    PubImuData();
    std::chrono::milliseconds ms((int)(1.0 / rate_ * 1000));

    // updater_ = std::make_unique<diagnostic_updater::Updater>(this);
    // updater_->add("imu", this, &ImuNode::Diagnostic);

    // publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
    timer_ = this->create_wall_timer(
      500ms, std::bind(&ImuNode::Spin, this));
  }

  ~ImuNode() {
    RCLCPP_INFO(this->get_logger(), "called destructor!");

    // imu_.Close();
  }

  void Prepare() {}

private:

  RTIMU *imu_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_data_pub_;
  rclcpp::Publisher<tf2_msgs::msg::TFMessage>::SharedPtr tf_br_;

  // rclcpp::Service<SimpleCmd>::SharedPtr cmd_server_;

  // std::unique_ptr<diagnostic_updater::Updater>updater_;

  std::string device_;
  std::string frame_id_;
  std::string parent_id_;
  double rate_;
  int cant_rcv_cnt_;
  void test() {
    RCLCPP_INFO(this->get_logger(), "called test!");
  }

  void InitParam() {
    // Set default value to variables
    device_    = "/dev/ttyACM0";
    frame_id_  = "imu";
    parent_id_ = "odom";
    rate_      = 100.0;

    // Read parameters
    std::string key = "device";

    std::chrono::seconds sec(1);
    rclcpp::Rate r(sec);

    // int sampleCount = 0;

    // int sampleRate  = 0;
    uint64_t rateTimer;
    uint64_t displayTimer;

    // uint64_t now;

    //  using RTIMULib here allows it to use the .ini file generated by
    // RTIMULibDemo.

    RTIMUSettings *settings = new RTIMUSettings("RTIMULib");

    RTIMU *imu           = RTIMU::createIMU(settings);
    RTPressure *pressure = RTPressure::createPressure(settings);

    if ((imu == NULL) || (imu->IMUType() == RTIMU_TYPE_NULL)) {
      printf("No IMU found\n");
      exit(1);
    }

    //  This is an opportunity to manually override any settings before the call
    // IMUInit

    //  set up IMU

    imu->IMUInit();

    //  this is a convenient place to change fusion parameters

    imu->setSlerpPower(0.02);
    imu->setGyroEnable(true);
    imu->setAccelEnable(true);
    imu->setCompassEnable(true);

    //  set up pressure sensor

    if (pressure != NULL) pressure->pressureInit();

    //  set up for rate timer

    rateTimer = displayTimer = RTMath::currentUSecsSinceEpoch();
  }

  void PubImuData() {
    auto data = std::make_shared<sensor_msgs::msg::Imu>();

    data->header.frame_id = frame_id_;
    data->header.stamp    = this->now();

    RTIMU_DATA imu_data = imu_->getIMUData();
    printf("%f", imu_data.fusionQPose.x());
    RCLCPP_INFO(this->get_logger(), "Publishing");

    // printf("%s\n", imuData.fusionPose);

    //
    // // Linear acceleration
    // data->linear_acceleration.x = acc[0];
    // data->linear_acceleration.y = acc[1];
    // data->linear_acceleration.z = acc[2];
    //
    // // Angular velocity
    // data->angular_velocity.x = gyro[0];
    // data->angular_velocity.y = gyro[1];
    // data->angular_velocity.z = gyro[2];
    //
    // // Orientation (not provided)
    // data->orientation.x = 0;
    // data->orientation.y = 0;
    // data->orientation.z = 0;
    // data->orientation.w = 1;
    //
    // imu_data_pub_->publish(*data);
  }

  void BroadcastImuPose() {
    tf2_msgs::msg::TFMessage tf_msg;
    geometry_msgs::msg::TransformStamped tff;

    //
    // double ypr[3];
    //
    // imu_.GetYPR(ypr);
    //
    // tff.transform.translation.x = 0;
    // tff.transform.translation.y = 0;
    // tff.transform.translation.z = 0;
    //
    // tf2::Quaternion q;
    // q.setRPY(ypr[2] * DEG2RAD, ypr[1] * DEG2RAD, ypr[0] * DEG2RAD);
    // tff.transform.rotation.x = q.getX();
    // tff.transform.rotation.y = q.getY();
    // tff.transform.rotation.z = q.getZ();
    // tff.transform.rotation.w = q.getW();
    //
    // tff.child_frame_id  = frame_id_;
    // tff.header.frame_id = parent_id_;
    // tff.header.stamp    = this->now();
    //
    // tf_msg.transforms.push_back(tff);
    // tf_br_->publish(tf_msg);
  }

  void UpdateAndPubRegMode() {
    // if (imu_.GetState() != AdisRcvCsv::State::RUNNING) return;
    //
    // int res = imu_.UpdateRegMode();
    //
    // if (res == IMU_OK) {
    //   PubImuData();
    //   cant_rcv_cnt_ = 0;
    // } else {
    //   if (res == IMU_ERR_CANT_RCV_DATA) cant_rcv_cnt_++;
    //
    //   PrintErrorCode(res);
    //   RCLCPP_ERROR(this->get_logger(), "Cannot update on register mode");
    // }
  }

  void UpdateAndPubYprMode() {
    // if (imu_.GetState() != AdisRcvCsv::State::RUNNING) return;
    //
    // int res = imu_.UpdateYprMode();
    //
    // if (res == IMU_OK) {
    //   BroadcastImuPose();
    //   cant_rcv_cnt_ = 0;
    // } else {
    //   if (res == IMU_ERR_CANT_RCV_DATA) cant_rcv_cnt_++;
    //
    //   PrintErrorCode(res);
    //   RCLCPP_ERROR(this->get_logger(), "Cannot update on attiude mode");
    // }
  }

  void PrintErrorCode(const int& code) {
    // switch (code) {
    // case IMU_ERR_CANT_RCV_DATA:
    //   RCLCPP_ERROR(this->get_logger(), "Can not read data from port");
    //   break;
    //
    // case IMU_ERR_COULDNOT_FIND_PACKET:
    //   RCLCPP_ERROR(this->get_logger(), "Can not find packet");
    //   break;
    //
    // case IMU_ERR_INVALID_DATA:
    //   RCLCPP_ERROR(this->get_logger(), "Can not invalid data");
    //   break;
    //
    // case IMU_ERR_CHECKSUM:
    //   RCLCPP_ERROR(this->get_logger(), "Checksum error");
    //   break;
    //
    // default:
    //   break;
    // }
  }

  void Spin() {
    RCLCPP_INFO(this->get_logger(), "Publishing data");

    PubImuData();
  }
}; // end of class


int main(int argc, char **argv) {
  rclcpp::init(argc, argv);

  rclcpp::NodeOptions options;
  options.allow_undeclared_parameters(true);
  options.automatically_declare_parameters_from_overrides(true);

  auto imu_node = std::make_shared<ImuNode>(options);

  rclcpp::spin(imu_node);
  rclcpp::shutdown();
  return 0;
}
