#region IMPORTS
import numpy as np
import math as m
import random
import re
import os
import subprocess
import ast
from datetime import datetime
#endregion

#region CONSTANTS

#TODO: change all file names to constants
#enter path to local blender installation
BLENDER_PATH = ''
INSPECTION_PATH_FILE = 'Inspektionspfad_links_blenderready.txt'

DEFECT_MODELS_AMOUNT = 15
RAND_POSES_PER_POSE = 2
IMGS_PER_POSE = 2

LIGHT_ENERGY = 140000

#distance between camera and LED in mm
LED_OFFSET = np.matrix([0,3,0]).transpose()

#regex search terms
RE_LOC = r"(?:\"location\": \[.*\])"
RE_ROT = r"(?:\"rotation\": \[.*\])"
RE_ENERGY = r"(?:\"energy\": .*)"

#config file base structure
CONFIG_BASE_CONTENT = (
    "{\n"
    "  \"version\": 3,\n"
    "  \"setup\": {\n"
    "    \"blender_install_path\": \"/home_local/HiWi2/blender/\",\n"
    "    \"pip\": [\n"
    "      \"h5py\",\n"
    "      \"scikit-image\"\n"
    "    ]\n"
    "  },\n"
    "  \"modules\": [\n"
    "    {\n"
    "      \"module\": \"main.Initializer\",\n"
    "      \"config\": {\n"
    "        \"global\": {\n"
    "          \"output_dir\": \"<args:2>\",\n"
    "          \"max_bounces\": 5,\n"
    "          \"diffuse_bounces\": 5,\n"
    "          \"glossy_bounces\": 5,\n"
    "          \"transmission_bounces\": 0,\n"
    "          \"transparency_bounces\": 0\n"
    "        }\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"loader.BlendLoader\",\n"
    "      \"config\": {\n"
    "        \"path\": \"<args:1>\"\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"manipulators.WorldManipulator\",\n"
    "      \"config\": {\n"
    "        \"cf_set_world_category_id\": 0  # this sets the worlds background category id to 0\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"lighting.LightLoader\",\n"
    "      \"config\": {\n"
    "        \"lights\": [\n"
    "          {\n"
    "            \"type\": \"AREA\",\n"
    "            \"location\": [0, 0, 0],\n"
    "            \"rotation\": [0, 0, 0],\n"
    "            \"energy\": 140000\n"
    "          }\n"
    "        ]\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"camera.CameraLoader\",\n"
    "      \"config\": {\n"
    "        \"path\": \"<args:0>\",\n"
    "        \"file_format\": \"location rotation/value\",\n"
    "        \"intrinsics\": {\n"
    "          \"fov\": 1.5708,\n"
    "          \"resolution_x\": 400,\n"
    "          \"resolution_y\": 400\n"
    "        }\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"renderer.RgbRenderer\",\n"
    "      \"config\": {\n"
    "        \"output_key\": \"colors\",\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"renderer.SegMapRenderer\",\n"
    "      \"config\": {\n"
    "        \"map_by\": [\"class\",\"instance\", \"name\"]\n"
    "      }\n"
    "    },\n"
    "    {\n"
    "      \"module\": \"writer.Hdf5Writer\",\n"
    "      \"config\": {\n"
    "        \"postprocessing_modules\": {\n"
    "          \"distance\": [\n"
    "          {\"module\": \"postprocessing.TrimRedundantChannels\"},\n"
    "          {\"module\": \"postprocessing.Dist2Depth\"}\n"
    "          ]\n"
    "        }\n"
    "      }\n"
    "    }\n"
    "  ]\n"
    "}\n")
#endregion

#region METHODS

def change_light_params(config_content=CONFIG_BASE_CONTENT, light_loc='[0, 0, 0]', light_rot='[0, 0, 0]', energy='140000',path=''):
    subst_loc = "\"location\": "+ light_loc
    subst_rot = "\"rotation\": "+ light_rot
    subst_energy = "\"energy\": "+ energy
    config_content = re.sub(RE_LOC, subst_loc, CONFIG_BASE_CONTENT, 0, re.MULTILINE)
    config_content = re.sub(RE_ROT, subst_rot, config_content, 0, re.MULTILINE)
    config_content = re.sub(RE_ENERGY, subst_energy, config_content, 0, re.MULTILINE)
    dest = open(path, "w")
    dest.write(config_content)
    dest.close()

def cam_pos_writer(cam_pos,path=''):
    cam_pos_txt = open(path,'w')
    for entry in cam_pos:
        for num in entry:
            cam_pos_txt.write(f"{num} ")
    cam_pos_txt.close()

def Rx(theta):
    return np.matrix([[1, 0          , 0           ],
                     [0, m.cos(theta),-m.sin(theta)],
                     [0, m.sin(theta), m.cos(theta)]])

def Ry(theta):
    return np.matrix([[m.cos(theta), 0, m.sin(theta)],
                     [0            , 1, 0           ],
                     [-m.sin(theta), 0, m.cos(theta)]])

def Rz(theta):
    return np.matrix([[m.cos(theta),-m.sin(theta), 0],
                     [m.sin(theta) , m.cos(theta), 0],
                     [0            , 0           , 1]])

def calc_light_position(cam_loc = np.matrix([0,0,0]), cam_rot = np.matrix([0,0,0]), offset = LED_OFFSET):
    alpha = cam_rot[2]
    beta  = cam_rot[1]
    gamma = cam_rot[0]
    yaw_mat   = Rz(alpha)
    pitch_mat = Ry(beta)
    roll_mat  = Rx(gamma)
    rot_mat = yaw_mat * pitch_mat * roll_mat
    light_loc = cam_loc + (rot_mat * offset).transpose()
    return light_loc

def generate_additional_poses(base_poses):
    cam_poses = []
    for p in base_poses:
        for i in range(1+RAND_POSES_PER_POSE):
            cam_poses.append(p)
    for p in cam_poses:
        for l in p:              
            ctr = 0
            for v in range(len(l)):
                #first 3 entries are location, others are rotation
                if ctr < 3:
                    l[v] += random.uniform(-0.1,0.1)
                else:
                    l[v] += random.uniform(-0.0349,0.0349)
                ctr+=1
    return cam_poses
#endregion

count = 0
# set up paths
wd = os.getcwd()
default_scene_path = os.path.join(wd,'defaultscene.blend')
generate_defects_path = os.path.join(wd,'generatedefects.py')
randomize_texture_path = os.path.join(wd,'randomizetexture.py')
dataset_dir = os.path.join(wd, f"dataset{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
os.mkdir(dataset_dir)
scene_path = os.path.join(wd,'scene.blend')
blender_proc_dir = os.path.join(wd,os.pardir)
bp_run_path = os.path.join(blender_proc_dir,'run.py')
config_path = os.path.join(dataset_dir,'config.yaml')
inspection_path_poses_path = os.path.join(wd,INSPECTION_PATH_FILE)
cam_pos_path = os.path.join(dataset_dir,'cam_pos.txt')
temp = open(cam_pos_path,'a')
temp.write('0 0 0 0 0 0')
temp.close()
output_base_path = os.path.join(dataset_dir,'output')

# load camera poses on inspection path
inspection_path_poses = []
with open(inspection_path_poses_path,'r') as f:
    lines = f.readlines()
    for line in lines:
        dict = ast.literal_eval(line)
        tup = ([dict['X'],dict['Y'],dict['Z']],[dict['A'],dict['B'],dict['C']])
        inspection_path_poses.append(tup)

# generate data set
for i in range(DEFECT_MODELS_AMOUNT):

    #generate defects
    p_defects = subprocess.Popen([BLENDER_PATH, default_scene_path, "--background", "--python", generate_defects_path], shell=True).wait()

    cam_poses = generate_additional_poses(inspection_path_poses)
    
    for cam_pos in cam_poses:
        #generate cam_pos.txt for next BP run
        cam_pos_writer(cam_pos,path=cam_pos_path)

        #calculate light position for current camera pose
        light_loc = calc_light_position(cam_loc=cam_pos[0],cam_rot = cam_pos[1])
        light_loc_list = np.array(light_loc)[0].tolist()

        #set light parameters (pose and energy) in config file, generate config file
        light_energy = random.randint(LIGHT_ENERGY*0.3,LIGHT_ENERGY*3)
        change_light_params(config_content=CONFIG_BASE_CONTENT, light_loc=f"{light_loc_list}", light_rot=f"{cam_pos[1]}", energy=f"{light_energy}",path=config_path)

        for img in range(IMGS_PER_POSE):
            p_texture = subprocess.Popen([BLENDER_PATH, scene_path, "--background", "--python", randomize_texture_path], shell=True).wait()

            subprocess.run(f"python {bp_run_path} {config_path} {cam_pos_path} {scene_path} {output_base_path}{count}", shell=True)

            count += 1