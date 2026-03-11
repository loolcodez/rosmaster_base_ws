# Rosmaster Base Workspace

ROS 2 Jazzy workspace for a Python driver that connects a Yahboom Rosmaster motor control board to ROS 2 topics and services.

## What this package provides

- Launch file: `ros2 launch rosmaster_base driver.launch.py`
- Battery voltage publisher: `/battery_voltage`
- Wheel encoder publisher: `/wheel_encoders`
- Raw motor command topic: `/cmd_raw_motors`
- Stop-motors service: `/stop_motors`

## Workspace layout

```text
rosmaster_base_ws/
├── src/rosmaster_base/
├── build/
├── install/
└── log/
```

## Prerequisites

- Ubuntu with ROS 2 Jazzy installed
- Python 3
- `colcon`
- Yahboom Rosmaster vendor Python library
- USB connection to the Rosmaster board

## 1. Install the vendor Rosmaster library

Download the Rosmaster Python library from Yahboom:

```text
https://www.yahboom.net/study/ROS-Driver-Board
```

On the Yahboom page, open the code/software download for the Rosmaster board, then install the library and `pyserial`:

```bash
python3 setup.py install --user
sudo apt install python3-serial
```

## 2. Check the USB connection

Confirm that the board is visible over USB:

```bash
lsusb
```

Example output:

```text
Bus 004 Device 002: ID 1a86:7523 QinHeng Electronics CH340 serial converter
```

Check the serial device:

```bash
ls -l /dev/ttyUSB0
```

If you use a custom symlink such as `/dev/myserial`, verify it with:

```bash
ls -l /dev/myserial
```

## 3. Optional: create a persistent udev rule

If the device path changes between reboots, create a udev rule:

```bash
sudo nano /etc/udev/rules.d/myserial.rules
```

Use this content:

```text
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE:="0777", SYMLINK+="myserial"
```

Reload udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## 4. Configure the serial port

The default driver configuration currently uses:

```yaml
port: "/dev/ttyUSB0"
```

That value is defined in [`driver.yaml`](/home/orangepi/Documents/first_ros2_robot/rosmaster_base_ws/src/rosmaster_base/config/driver.yaml).

If you want to use `/dev/myserial`, update the `port` value there before launching the node.

## 5. Build the workspace

```bash
cd ~/Documents/first_ros2_robot/rosmaster_base_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

## 6. Run the driver

```bash
cd ~/Documents/first_ros2_robot/rosmaster_base_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch rosmaster_base driver.launch.py
```

If the workspace has already been built, only the `source` and `ros2 launch` commands are needed.

## Interfaces

### Published topics

```text
/battery_voltage    std_msgs/msg/Float32
/wheel_encoders     std_msgs/msg/Int32MultiArray
```

### Subscribed topics

```text
/cmd_raw_motors     std_msgs/msg/Int16MultiArray
```

Expected motor command format:

```text
data: [M1, M2, M3, M4]
```

Each value is clamped to the range `-100` to `100`.

### Services

```text
/stop_motors        std_srvs/srv/Trigger
```

## Test commands

Open a second terminal and source the workspace first:

```bash
cd ~/Documents/first_ros2_robot/rosmaster_base_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Check battery voltage:

```bash
ros2 topic echo /battery_voltage
```

Check wheel encoders:

```bash
ros2 topic echo /wheel_encoders
```

Drive all motors forward:

```bash
ros2 topic pub --once /cmd_raw_motors std_msgs/msg/Int16MultiArray "{data: [20, 20, 20, 20]}"
```

Drive all motors in reverse:

```bash
ros2 topic pub --once /cmd_raw_motors std_msgs/msg/Int16MultiArray "{data: [-20, -20, -20, -20]}"
```

Turn in place:

```bash
ros2 topic pub --once /cmd_raw_motors std_msgs/msg/Int16MultiArray "{data: [20, -20, 20, -20]}"
```

Stop the motors:

```bash
ros2 service call /stop_motors std_srvs/srv/Trigger "{}"
```

## Notes

- The node name is `rosmaster_driver`.
- The launch file loads parameters from `src/rosmaster_base/config/driver.yaml`.
- If the vendor Python package uses a different import path, update the import in [`driver_node.py`](/home/orangepi/Documents/first_ros2_robot/rosmaster_base_ws/src/rosmaster_base/rosmaster_base/driver_node.py).
