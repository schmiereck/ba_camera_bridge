"""Launch both overview and gripper cameras with explicit parameter file scoping."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_share = get_package_share_directory('ba_camera_bridge')
    
    # Explicitly define paths to prevent argument clashing in the shared launch context
    overview_params = os.path.join(pkg_share, 'config', 'overview_camera.yaml')
    gripper_params = os.path.join(pkg_share, 'config', 'gripper_camera.yaml')
    
    overview_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'overview_camera.launch.py')
        ),
        launch_arguments={'params_file': overview_params}.items()
    )
    
    gripper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gripper_camera.launch.py')
        ),
        launch_arguments={'params_file': gripper_params}.items()
    )
    
    return LaunchDescription([
        overview_launch,
        gripper_launch,
    ])
