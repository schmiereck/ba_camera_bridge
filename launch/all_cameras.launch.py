"""Launch both overview and gripper cameras."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    pkg_share = FindPackageShare('ba_camera_bridge')
    
    overview_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share.find('ba_camera_bridge'), 'launch', 'overview_camera.launch.py')
        )
    )
    
    gripper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share.find('ba_camera_bridge'), 'launch', 'gripper_camera.launch.py')
        )
    )
    
    return LaunchDescription([
        overview_launch,
        gripper_launch,
    ])
