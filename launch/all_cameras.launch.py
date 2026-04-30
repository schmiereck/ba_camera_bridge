"""Launch both overview and gripper cameras."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_share = get_package_share_directory('ba_camera_bridge')
    
    overview_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'overview_camera.launch.py')
        )
    )
    
    gripper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gripper_camera.launch.py')
        )
    )
    
    return LaunchDescription([
        overview_launch,
        gripper_launch,
    ])
