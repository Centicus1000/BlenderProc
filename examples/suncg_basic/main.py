from src.utility.CameraUtility import CameraUtility
from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.Utility import Utility
from src.utility.MathUtility import MathUtility

from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.utility.SegMapRendererUtility import SegMapRendererUtility
from src.utility.loader.SuncgLoader import SuncgLoader
from src.utility.SuncgLightingUtility import SuncgLightingUtility

from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer

from src.utility.RendererUtility import RendererUtility
import numpy as np
from mathutils import Matrix, Vector, Euler

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file which describes one camera pose per line, here the output of scn2cam from the SUNCGToolbox can be used")
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/suncg_with_cam_sampling/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
objs = SuncgLoader.load(args.house)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, pixel_aspect_x=1.333333333, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position = MathUtility.transform_point_to_blender_coord_frame(Vector(line[:3]), ["X", "-Z", "Y"])
        rotation = MathUtility.transform_point_to_blender_coord_frame(Vector(line[3:6]), ["X", "-Z", "Y"])
        matrix_world = Matrix.Translation(position) @ CameraUtility.rotation_from_forward_vec(rotation).to_4x4()
        CameraUtility.add_camera_pose(matrix_world)

# makes Suncg objects emit light
SuncgLightingUtility.light()

# activate normal and distance rendering
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

# render the whole pipeline
data = RendererUtility.render()

data.update(SegMapRendererUtility.render(Utility.get_temporary_directory(), Utility.get_temporary_directory(), "class"))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
