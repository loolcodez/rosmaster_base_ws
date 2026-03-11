import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('rosmaster_base'),
        'config',
        'driver.yaml'
    )

    return LaunchDescription([
        Node(
            package='rosmaster_base',
            executable='driver_node',
            name='rosmaster_driver',
            output='screen',
            parameters=[config]
        )
    ])
