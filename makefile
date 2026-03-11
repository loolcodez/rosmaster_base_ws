
.PHONY: build run clean

build:
	bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash && colcon build --symlink-install"

run:
	bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash && source install/setup.bash && ros2 launch rosmaster_base driver.launch.py"

clean:
	rm -rf build install log
