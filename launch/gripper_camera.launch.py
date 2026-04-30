"""Launch the gripper USB camera as a ROS2 publisher.

Starts a single ``v4l2_camera_node`` inside the ``/ba_gripper_camera``
namespace so the following topics become available:

    /ba_gripper_camera/image_raw            (sensor_msgs/Image, local use)
    /ba_gripper_camera/image_raw/compressed (sensor_msgs/CompressedImage)
    /ba_gripper_camera/camera_info          (sensor_msgs/CameraInfo)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution([
        FindPackageShare('ba_camera_bridge'),
        'config',
        'gripper_camera.yaml',
    ])

    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='Path to the parameter YAML for the gripper camera node.',
    )

    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera_node',
        namespace='ba_gripper_camera',
        output='screen',
        emulate_tty=True,
        parameters=[LaunchConfiguration('params_file')],
    )

    return LaunchDescription([
        params_file_arg,
        camera_node,
    ])
