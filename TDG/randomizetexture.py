#region IMPORTS
import bpy
import random
import os
#endregion

#region CONSTANTS

MAIN_OBJ_NAME = 'Turbosupercharger'

#nodes noise scale rand values
NODE_NOISE_MIN_SCALE_0 = 0.8*20
NODE_NOISE_MAX_SCALE_0 = 1.2*20
NODE_NOISE_MIN_SCALE_1 = 0.8*8
NODE_NOISE_MAX_SCALE_1 = 1.2*8
NODE_NOISE_MIN_SCALE_2 = 0.8*0.2
NODE_NOISE_MAX_SCALE_2 = 1.2*0.2
NODES_NOISE_SCALE_MIN_MAX = [
    NODE_NOISE_MIN_SCALE_0, NODE_NOISE_MAX_SCALE_0,
    NODE_NOISE_MIN_SCALE_1, NODE_NOISE_MAX_SCALE_1,
    NODE_NOISE_MIN_SCALE_2, NODE_NOISE_MAX_SCALE_2]

#noise amplification rand values
NODE_MULT_MIN = 5
NODE_MULT_MAX = 10

#nodes roughness rand values
NODE_ROUGH_MIN = 0.05
NODE_ROUGH_MAX = 0.15
#endregion

#region OBJECTS
def get_active_object():
    return bpy.context.active_object

def get_object(ref=None):
    objref = None
    if ref is None:
        objref = get_active_object()
    else:
        if type(ref) == str:
            objref = bpy.data.objects[ref]
        else:
            objref = ref
    return objref
#endregion

#region MODIFIERS
def add_noisy_displacement(main_ref = None, strength = 0, noise_depth = 4, noise_scale = 6):
    main_obj = get_object(main_ref)
    displace = main_obj.modifiers.new(name="Displace", type='DISPLACE')
    displace.texture = add_noise_texture(noise_depth, noise_scale)
    displace.strength = strength
#endregion

#region TEXTURES
def add_noise_texture(noise_depth = 4, noise_scale = 6):
    noise_texture = bpy.data.textures.new("Noise", 'CLOUDS')
    noise_texture.noise_basis = 'BLENDER_ORIGINAL'
    noise_texture.noise_type = 'SOFT_NOISE'
    noise_texture.noise_depth = noise_depth
    noise_texture.noise_scale = noise_scale
    return noise_texture

def rnd_cast_iron(main_obj_ref):
    mat = main_obj_ref.active_material
    nodes = mat.node_tree.nodes
    i = 0
    for node in nodes:
        if node.type == "TEX_NOISE":
            node.inputs["Scale"].default_value = random.uniform(
                NODES_NOISE_SCALE_MIN_MAX[i],NODES_NOISE_SCALE_MIN_MAX[i+1])
            i+=2
        elif node.type == "BSDF_PRINCIPLED":
            node.inputs["Base Color"].default_value = (random.uniform(0,1),
                random.uniform(0,1), random.uniform(0,1), 1)
            node.inputs["Roughness"].default_value = random.uniform(
                NODE_ROUGH_MIN, NODE_ROUGH_MAX)
        elif node.type == "MATH":
            node.inputs[1].default_value = random.uniform(NODE_MULT_MIN,NODE_MULT_MAX)
#endregion

#region EXECUTION
wd = os.getcwd()
scene_path = os.path.join(wd,'scene.blend')

#object names must match names in the .blend file
main_obj_ref = get_object(MAIN_OBJ_NAME)

rnd_cast_iron(main_obj_ref)

#save the scene
bpy.ops.wm.save_mainfile(filepath=scene_path)

#endregion
