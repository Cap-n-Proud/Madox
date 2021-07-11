#include <chrono>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

#include <sensor_msgs/msg/imu.hpp>
#include "RTIMULib.h"
using namespace std::chrono_literals;

/* This example creates a subclass of Node and uses std::bind() to register a
 * member function as a callback from the timer. */

class MinimalPublisher : public rclcpp::Node {
public:

  MinimalPublisher()
    : Node("minimal_publisher"), count_(0)
  {
    int sampleCount = 0;
    int sampleRate  = 0;
    uint64_t rateTimer;
    uint64_t displayTimer;
    uint64_t now;

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

    /* message */
    auto message_ = std::make_shared<sensor_msgs::msg::Imu>();

    /* publisher */
    auto topic_name = "imu";
    auto qos        = rclcpp::QoS(rclcpp::KeepLast(1));
    publisher_ = create_publisher<sensor_msgs::msg::Imu>(
      topic_name,
      qos);

    /* timer */
    int period_ms = 50;
    timer_ = create_wall_timer(
      std::chrono::milliseconds(period_ms),
      std::bind(&MinimalPublisher::timer_callback, this)
      );
  }

private:

  void timer_callback()
  {
    RTIMU_DATA imuData = imu->getIMUData();

    //  add the pressure data to the structure

    if (pressure != NULL) pressure->pressureRead(imuData);

    sampleCount++;

    now = RTMath::currentUSecsSinceEpoch();

    // // message.data = "Hello, world! " + std::to_string(count_++);
    // RCLCPP_INFO(this->get_logger(), "Publishing: '%s'",
    //             RTMath::displayDegrees("", imuData.fusionPose));
    // RCLCPP_INFO(this->get_logger(), "Hello from ROS2");

    // publisher_->publish(message);
  }

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  size_t count_;
};

int main(int argc, char *argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalPublisher>());
  rclcpp::shutdown();
  return 0;
}
