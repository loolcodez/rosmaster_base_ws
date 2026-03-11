import time
from typing import List

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from std_msgs.msg import Int16MultiArray
from std_msgs.msg import Int32MultiArray
from std_srvs.srv import Trigger

class RosmasterDriverNode(Node):
    def __init__(self) -> None:
        super().__init__('rosmaster_driver')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('command_timeout_sec', 1.0)
        self.declare_parameter('invert_motor_1', False)
        self.declare_parameter('invert_motor_2', False)
        self.declare_parameter('invert_motor_3', False)
        self.declare_parameter('invert_motor_4', False)

        self.port = self.get_parameter('port').value
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.command_timeout_sec = float(self.get_parameter('command_timeout_sec').value)

        self.invert = [
            bool(self.get_parameter('invert_motor_1').value),
            bool(self.get_parameter('invert_motor_2').value),
            bool(self.get_parameter('invert_motor_3').value),
            bool(self.get_parameter('invert_motor_4').value),
        ]

        self.last_command_time = time.monotonic()
        self.last_command = [0, 0, 0, 0]

        self.driver = None

        self.battery_pub = self.create_publisher(Float32, '/battery_voltage', 10)
        self.encoder_pub = self.create_publisher(Int32MultiArray, '/wheel_encoders', 10)

        self.cmd_sub = self.create_subscription(
            Int16MultiArray,
            '/cmd_raw_motors',
            self.cmd_raw_motors_callback,
            10
        )

        self.stop_srv = self.create_service(
            Trigger,
            '/stop_motors',
            self.stop_motors_callback
        )

        if not self.initialize_driver():
            self.get_logger().error('Failed to initialize Rosmaster driver')
            raise RuntimeError('Rosmaster init failed')

        period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(period, self.timer_callback)

        self.get_logger().info('Rosmaster driver node started')

    def initialize_driver(self) -> bool:
        """
        Adjust the import below if your Rosmaster library uses a different module path.
        """

        try:
            # Example import style. Change this if your local library differs.
            from Rosmaster_Lib import Rosmaster  # type: ignore
        except Exception as exc:
            self.get_logger().error(f'Failed to import Rosmaster library: {exc}')
            self.get_logger().error(
                'Install or copy the vendor Rosmaster library so Python can import it.'
            )
            return False

        try:
            # Some vendor libraries accept com/port, some do not.
            # Start with the simplest constructor first.
            try:
                self.driver = Rosmaster(com=self.port, debug=False)
            except TypeError:
                self.driver = Rosmaster()

            self.driver.create_receive_threading()
            self.driver.clear_auto_report_data()

            self.get_logger().info(
                f'Rosmaster initialized on port {self.port}'
            )
            return True

        except Exception as exc:
            self.get_logger().error(f'Rosmaster initialization error: {exc}')
            return False

    def cmd_raw_motors_callback(self, msg: Int16MultiArray) -> None:
        if len(msg.data) != 4:
            self.get_logger().warning(
                f'/cmd_raw_motors expects 4 values, got {len(msg.data)}'
            )
            return

        speeds = [int(v) for v in msg.data]
        speeds = [self.clamp_motor_value(v) for v in speeds]

        for i in range(4):
            if self.invert[i]:
                speeds[i] = -speeds[i]

        self.send_motor_command(speeds)
        self.last_command = speeds
        self.last_command_time = time.monotonic()

    def stop_motors_callback(self, request, response):
        del request
        ok = self.send_motor_command([0, 0, 0, 0])
        response.success = ok
        response.message = 'Motors stopped' if ok else 'Failed to stop motors'
        return response

    def timer_callback(self) -> None:
        self.publish_battery()
        self.publish_encoders()
        self.apply_command_timeout()

    def publish_battery(self) -> None:
        if self.driver is None:
            return

        try:
            voltage = float(self.driver.get_battery_voltage())
            msg = Float32()
            msg.data = voltage
            self.battery_pub.publish(msg)
        except Exception as exc:
            self.get_logger().warning(f'Failed to read battery voltage: {exc}')

    def publish_encoders(self) -> None:
        if self.driver is None:
            return

        try:
            encoders = self.driver.get_motor_encoder()
            msg = Int32MultiArray()
            msg.data = [int(v) for v in encoders]
            self.encoder_pub.publish(msg)
        except Exception as exc:
            self.get_logger().warning(f'Failed to read motor encoders: {exc}')

    def apply_command_timeout(self) -> None:
        elapsed = time.monotonic() - self.last_command_time
        if elapsed > self.command_timeout_sec and self.last_command != [0, 0, 0, 0]:
            self.get_logger().warning('Motor command timeout, stopping motors')
            self.send_motor_command([0, 0, 0, 0])
            self.last_command = [0, 0, 0, 0]

    def send_motor_command(self, speeds: List[int]) -> bool:
        if self.driver is None:
            return False

        try:
            self.driver.set_motor(
                int(speeds[0]),
                int(speeds[1]),
                int(speeds[2]),
                int(speeds[3]),
            )
            return True
        except Exception as exc:
            self.get_logger().error(f'Failed to send motor command: {exc}')
            return False

    @staticmethod
    def clamp_motor_value(value: int) -> int:
        return max(-100, min(100, value))

    def destroy_node(self) -> bool:
        try:
            self.get_logger().info('Stopping motors before shutdown')
            self.send_motor_command([0, 0, 0, 0])
        except Exception:
            pass
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None

    try:
        node = RosmasterDriverNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
