#region IMPORTS
import bpy
import random
import os
#endregion

#region CONSTANTS
DEFECTS_PER_PART = 101
DEFECT_NAME = 'Sphere'
BLOWHOLE_ID = 2
MAIN_OBJ_NAME = 'Turbosupercharger'

#cloud noise texture randomization values
CLOUD_TXTR_MIN_NOISE_STR = -0.8
CLOUD_TXTR_MAX_NOISE_STR = 0.8
CLOUD_TXTR_MIN_NOISE_SCALE = 2
CLOUD_TXTR_MAX_NOISE_SCALE = 10
CLOUD_TXTR_MIN_NOISE_DEPTH = 0
CLOUD_TXTR_MAX_NOISE_DEPTH = 20
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

def copy_object(tocopy, col = None):
    new_obj = None
    to_copy = get_object(tocopy)
    col_ref = None

    if col == None:
        col_ref = get_active_collection()
    elif type(col) == str:
        if collection_exists(col):
            col_ref = col
        else:
            col_ref = create_collection(col)
    else:
        col_ref = col
    
    new_obj = to_copy.copy()
    if new_obj.data is not None:
        new_obj.data = to_copy.data.copy()
    col_ref.objects.link(new_obj)
    return new_obj
   
#endregion

#region MESHES
def get_vertices(ref):
    if type(ref) == str:
        return get_object(ref).data.vertices
    else:
        return ref.data.vertices
#endregion

#region COLLECTIONS
def get_active_collection():
    return bpy.context.view_layer.active_layer_collection.collection

def collection_exists(col):
    if type(col) == str:
        return col in bpy.data.collections
    return col.name in bpy.data.collections

def create_collection(name):
    bpy.data.collections.new(name)
    colref = bpy.data.collections[name]
    bpy.context.scene.collection.children.link(colref)
    return colref
#endregion

#region MODIFIERS
def make_solid(ref = None, tar_thickness = 0.01):
    target = get_object(ref)
    tar_mods = bpy.data.objects[target.name].modifiers
    if any([m for m in tar_mods if m.name == "Solid"]):
        change_thickness(target, tar_thickness)
    else:
        solid_mod = tar_mods.new(name='Solid', type ='SOLIDIFY')
        solid_mod.thickness = tar_thickness

#doesn't work as expected: setting thickness to 0 makes the object hollow!
def change_thickness(ref=None, thickness = 0.001):
   target = get_object(ref)
   #this is not a great solution, since the mod name is hard coded
   bpy.data.objects[target.name].modifiers['Solid'].thickness = thickness
    
def make_boolean_difference(main_ref = None, tool_ref = None):
    main_obj = get_object(main_ref)
    tool_obj = get_object(tool_ref)
    bool_mod = main_obj.modifiers.new(name='Bool_Diff', type='BOOLEAN')
    bool_mod.object = tool_obj
    bool_mod.operation = 'DIFFERENCE'
    #TODO: could add if condition here (don't want to apply immediately)
    bpy.ops.object.modifier_apply({"object": main_obj}, modifier=bool_mod.name)
    
def make_boolean_intersection(main_ref = None, tool_ref = None):
    main_obj = get_object(main_ref)
    tool_obj = get_object(tool_ref)
    bool_mod = main_obj.modifiers.new(name='Bool_Inter', type='BOOLEAN')
    bool_mod.object = tool_obj
    bool_mod.operation = 'INTERSECT'
    #TODO: could add if condition here (don't want to apply immediately)
    bpy.ops.object.modifier_apply({"object": main_obj}, modifier=bool_mod.name)

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
#endregion

#region CUSTOM_METHODS
def create_defect(main_obj_ref, tool_ref, vert, category_id = -1):
    tool_ref.location = vert.co - random.uniform(0,0.3)*vert.normal
    
    #TODO: move the randomization elsewhere
    noise_strength = random.uniform(CLOUD_TXTR_MIN_NOISE_STR, CLOUD_TXTR_MAX_NOISE_STR)
    noise_depth = int(random.uniform(CLOUD_TXTR_MIN_NOISE_DEPTH, CLOUD_TXTR_MAX_NOISE_DEPTH))
    noise_scale = random.uniform(CLOUD_TXTR_MIN_NOISE_SCALE, CLOUD_TXTR_MAX_NOISE_SCALE)
    add_noisy_displacement(tool_ref, noise_strength, noise_depth, noise_scale)

    main_obj_copy = copy_object(main_obj_ref)    
    add_category_id(main_obj_copy,category_id)
  
    make_boolean_difference(main_obj_ref,tool_ref)

    make_solid(tool_ref)

    make_boolean_intersection(main_obj_copy, tool_ref)
    tool_ref.modifiers.clear()

def select_defect_verts(mo_vertices, number_of_defects=DEFECTS_PER_PART):
    vertex_count = len(mo_vertices)
    #avoid intersecting defects
    step_size = int(vertex_count/(1.3*number_of_defects))
    starting_vert_number = random.randint(0,step_size)
    v_index = starting_vert_number
    defect_vert_indices = []
    while(v_index + step_size < (1/1.3)*vertex_count):
        defect_vert_indices.append(v_index)
        v_index += step_size
    return defect_vert_indices

def add_category_id(obj_ref, category_id = -1):
    obj_ref['category_id'] = category_id
#endregion

#region CREATE DEFECTS

#object names must match names in the .blend file
main_obj_ref = get_object(MAIN_OBJ_NAME)

tool_ref = get_object(DEFECT_NAME)

mo_vertices = get_vertices(main_obj_ref)
defect_vert_indices = select_defect_verts(mo_vertices)

for v in defect_vert_indices:   
    create_defect(main_obj_ref, tool_ref, mo_vertices[v], BLOWHOLE_ID)

#remove defect tool
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects[DEFECT_NAME].select_set(True)
bpy.ops.object.delete()

#smooth objects to remove artifacts
ctx = bpy.context.copy()
all_objects = [o for o in bpy.data.objects if o.type == "MESH"]
o = all_objects[0]
ctx['object'] = o
ctx['active_object'] = o
ctx['selected_objects'] = all_objects
ctx['selected_editable_objects'] = all_objects
bpy.ops.object.shade_smooth(ctx)
for m in bpy.data.meshes:
    m.use_auto_smooth = True


#save the scene
wd = os.getcwd()
scene_path = os.path.join(wd,'scene.blend')
print("Defects were created. Will now be saved")
bpy.ops.wm.save_mainfile(filepath=scene_path)

#endregion
