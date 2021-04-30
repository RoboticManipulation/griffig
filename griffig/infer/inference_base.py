from pathlib import Path
import os

import cv2
from loguru import logger
import numpy as np
import tensorflow.keras as tk

from pyaffx import Affine
from _griffig import BoxData, RobotPose, OrthographicImage
from ..utility.image import draw_around_box, get_inference_image, get_box_projection


class InferenceBase:
    def __init__(self, model_data, gaussian_sigma=None, gpu: int = None, seed: int = None, verbose=0):
        self.model_data = model_data
        self.model = self._load_model(model_data.path, 'grasp', gpu=gpu)
        self.gaussian_sigma = gaussian_sigma
        self.rs = np.random.default_rng(seed=seed)
        self.verbose = verbose

        self.size_area_cropped = model_data.size_area_cropped
        self.size_result = model_data.size_result
        self.scale_factors = (self.size_area_cropped[0] / self.size_result[0], self.size_area_cropped[1] / self.size_result[1])
        self.a_space = np.linspace(-np.pi/2 + 0.1, np.pi/2 - 0.1, 20)  # [rad] # Don't use a=0.0 -> even number
        self.keep_indixes = None

    def _load_model(self, path: Path, submodel=None, gpu=None):
        if os.getenv('GRIFFIG_HARDWARE') == 'jetson-nano':
            import tensorflow as tf
            
            logger.info('Detected NVIDIA Jetson Nano Platform')
            device = tf.config.list_physical_devices('GPU')
            tf.config.experimental.set_memory_growth(device[0], True)
            tf.config.experimental.set_virtual_device_configuration(device[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=512)])

        elif gpu is not None:
            import tensorflow as tf
            
            devices = tf.config.list_physical_devices('GPU')
            tf.config.experimental.set_visible_devices(devices[gpu], 'GPU')
            for device in devices:
                tf.config.experimental.set_memory_growth(device, True)

        model = tk.models.load_model(path, compile=False)

        if submodel:
            model = model.get_layer(submodel)

        # TensorRT
        if os.getenv('GRIFFIG_HARDWARE') == 'jetson-nano':
            from tensorflow.python.compiler.tensorrt import trt_convert as trt

            submodel_path = str(path / 'submodel')
            model.save(submodel_path)

            logger.info('Convert to TensorRT')
            conversion_params = trt.TrtConversionParams(
                precision_mode=trt.TrtPrecisionMode.FP16,
                max_batch_size=32,
            )

            converter = trt.TrtGraphConverterV2(
                input_saved_model_dir=submodel_path,
                conversion_params=conversion_params
            )
            converter.convert()
            converted_path = str(path / 'converted')
            converter.save(converted_path)

            root = tf.saved_model.load(converted_path)
            func = root.signatures['serving_default']
            
            def predict(x):
                x = tf.convert_to_tensor(x)
                output = [y.numpy() for y in func(x).values()]

                if len(output) == 1:
                    return output[0]
                return output
            return predict

        def predict(x):
            return model.predict_on_batch(x)
        return predict

    def _get_size_cropped(self, image, box_data: BoxData):
        box_projection = get_box_projection(image, box_data)
        center = np.array([image.mat.shape[1], image.mat.shape[0]]) / 2
        farthest_corner = np.max(np.linalg.norm(box_projection - center, axis=1))
        side_length = int(np.ceil(2 * farthest_corner * self.size_result[0] / self.size_area_cropped[0]))
        return (side_length, side_length)

    def pose_from_index(self, index, index_shape, image: OrthographicImage) -> RobotPose:
        return RobotPose(Affine(
            x=self.scale_factors[0] * image.position_from_index(index[1], index_shape[1]),
            y=self.scale_factors[1] * image.position_from_index(index[2], index_shape[2]),
            a=self.a_space[index[0]],
        ).inverse(), d=0.0)

    def transform_for_prediction(
            self,
            image: OrthographicImage,
            box_data: BoxData = None,
    ):
        size_cropped = self._get_size_cropped(image, box_data)

        if box_data:
            draw_around_box(image, box_data)

        # Rotate images
        rotated = []
        for a in self.a_space:
            dst_depth = get_inference_image(image, Affine(a=a), size_cropped, self.size_area_cropped, self.size_result)
            rotated.append(dst_depth.mat)

        result = np.array(rotated) / np.iinfo(image.mat.dtype).max

        if len(result.shape) == 3:
            result = np.expand_dims(result, axis=-1)

        if self.verbose:
            cv2.imwrite('/tmp/test-input-c.png', result[0][0, :, :, :3] * 255)
            cv2.imwrite('/tmp/test-input-d.png', result[0][0, :, :, 3:] * 255)

        return result

    @classmethod
    def keep_array_at_last_indixes(cls, array, indixes) -> None:
        mask = np.zeros(array.shape)
        mask[:, :, :, indixes] = 1
        array *= mask

    @classmethod
    def set_last_dim_to_zero(cls, array, indixes):
        array[:, :, :, indixes] = 0
