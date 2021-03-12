from pathlib import Path
from frankx import Affine
from _griffig import BoxData, Renderer
import inference.selection as Selection


class Griffig:
    def __init__(
        self,
        model='two-finger',
        gripper=None,
        box_data: BoxData = None,
        width_interval=None,
    ):
        self.model_name = model
        self.gripper = gripper
        self.box_data = box_data
        self.width_interval = width_interval

        self.renderer = Renderer()
        self.last_grasp_successful = True

    def calculate_grasp(self, camera_pose, pointcloud, box_data=None, method=None):
        image = self.renderer.render(pointcloud, camera_pose, pixel_size, delta_depth)

        selection_method = Selection.Max() if self.last_grasp_successful else Selection.Top(5)

        self.last_grasp_successful = True

    def report_grasp_failure(self):
        self.last_grasp_successful = False
