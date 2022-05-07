import yaml
import json

# TypeScript changed me
from typing import TypedDict, Optional, Dict, List


# Type defs
class Coordinates(TypedDict):
    x: str
    y: str
    z: str
    w: Optional[str]


class Color(TypedDict):
    r: str
    g: str
    b: str
    a: Optional[str]


class Bone(TypedDict):
    name: str
    rotation: Optional[Coordinates]
    position: Optional[Coordinates]
    scale: Optional[Coordinates]
    euler_angles: Optional[Coordinates]
    color: Optional[Color]
    length: Optional[str]
    child: Optional[str]
    children: List[int]


class Bones(TypedDict):
    root: Optional[Bone]
    id: Optional[List[Bone]]

# Unity consts - Screaming at y'a
TRANSFORM = '4'
GAME_OBJECT = '1'
SKINNED_MESH_RENDERER = '137'
MONO_BEHAVIOUR = '114'

# Will store transforms and GameObject for further mapping
transforms = {}
game_objects = {}
skin_mesh_rend = {}

# Bones, for now just a test
bones: Bones = {}
behaviours = {}

export_mode_bones = []

# Used to locate back Transforms when applying to DragonBones Skeleton
game_object_lookup_transform = {}

# Scale it ! 100 seems safe from Unity => DragonBones
SCALE_FACTOR = 100


FILENAME = 'Base1.unity'

# Opens te hardcoded file
with open(FILENAME, 'r', encoding='utf-8') as file:
    # Little hack ! Unity YAML use multiple documents, with their tag as header. Currently, PyYAML doesn't support
    # it. This little hack make things way easier, and help locating stuff without the need of complex parsing (hence
    # the "dumb" filename). If it doesn't work for you, feel free to open a PR with more details :D
    #
    # Header structure seems to always be '--- !u!0000 &1111' where 0000 is the unity asset type and 1111 its "fileID"
    # Using some split and index, it is possible to get documents. So far it worked flawlessly !
    for block in file.read().split('--- !u!')[1:]:
        block_type = block[:block.index(' ')]
        file_id_index = block.index('&')
        file_id_index_end = block.index('\n')
        file_id = block[file_id_index+1:file_id_index_end]

        if block_type == TRANSFORM:
            transforms[file_id] = yaml.safe_load(block[file_id_index_end:])

            # print(f'{file_id} -> Transform')
        elif block_type == GAME_OBJECT:
            # Filtering only needed values for now
            # if 'm_Name: image_hasumiTfront_' in block:
            game_objects[file_id] = yaml.safe_load(block[file_id_index_end:])

                # print(f'{file_id} -> GameObject')
        elif block_type == SKINNED_MESH_RENDERER:
            skin_mesh_rend[file_id] = yaml.safe_load(block[file_id_index_end:])
            # print(f'{file_id} -> SkinnedMeshRenderer')

        elif block_type == MONO_BEHAVIOUR:
            behaviours[file_id] = yaml.safe_load(block[file_id_index_end:])

# Get the root bone and try to build index from it

def fetch_children_bone_from(bone_id):
    """Fetch children from bone, recursively"""
    bone_id_s = str(bone_id)
    if bone_id not in bones['id'] and bone_id_s in transforms:

        bone = transforms[bone_id_s]['Transform']

        game_object_id: int = bone['m_GameObject']['fileID']
        game_object_id_s: str = str(game_object_id)

        name: str = f'Unnamed_bone_{bone_id_s}'

        children: List[int] = [i['fileID'] for i in bone['m_Children']]

        rotation: Coordinates = bone['m_LocalRotation']
        position: Coordinates = bone['m_LocalPosition']
        scale: Coordinates = bone['m_LocalScale']
        euler_angles: Coordinates = bone['m_LocalEulerAnglesHint']

        my_bone: Bone = {
            'name': name,
            'rotation': rotation,
            'position': position,
            'scale': scale,
            'euler_angles': euler_angles,
            'children': children
        }

        if game_object_id_s in game_objects:
            game_object = game_objects[game_object_id_s]['GameObject']

            if 'm_Component' in game_object:
                for c in game_object['m_Component']:
                    file_id = str(c['component']['fileID'])
                    if file_id in behaviours:
                        b = behaviours[file_id]['MonoBehaviour']
                        if 'm_Color' in b:
                            my_bone['color'] = b['m_Color']
                        if 'm_Length' in b:
                            my_bone['length'] = b['m_Length']
                        # Behaviour is unknown ? IK maybe ?
                        # else:
                        #     print(b)

            # TODO: get layer from m_Layer ?
            my_bone['name'] = game_object["m_Name"]

        bones['id'][bone_id] = my_bone

        for child_id in children:
            if child_id not in bones['id']:
                new_bone: Bone = fetch_children_bone_from(child_id)
                if new_bone is not None:
                    db_bone = {
                        "length": str(round(float(new_bone['length'])*SCALE_FACTOR)) if 'length' in new_bone else '0',
                        "name": new_bone['name'],
                        "parent": my_bone['name'],
                        "transform": {
                            "x": new_bone['position']['x']*SCALE_FACTOR,
                            "y": -1 * new_bone['position']['y']*SCALE_FACTOR
                        },
                    }

                    # euler_angles Z is the rotation
                    if 'euler_angles' in new_bone and 'z' in new_bone['euler_angles']:
                        z_rotate = round(float(new_bone['euler_angles']['z']), 3)

                        if z_rotate != 0:
                            db_bone["transform"]["skX"] = z_rotate
                            db_bone["transform"]["skY"] = z_rotate

                    export_mode_bones.append(db_bone)

        return my_bone
    return None


ROOT_BONE = 'Bones_Tfront'  # OR HasumiEd0318 ??



for file_id, g in game_objects.items():
    game_object = g['GameObject']

    if game_object["m_Name"] == ROOT_BONE:
        root_components_id = [i['component']['fileID'] for i in game_object['m_Component']]

        for root_component_id in root_components_id:
            root_component_id_s = str(root_component_id)

            # Try to find if id is in transforms
            # parent-child relation is made by the transform, where the name is found by the game_object
            if root_component_id_s in transforms:
                t = transforms[root_component_id_s]

                transform = t['Transform']

                children = [i['fileID'] for i in transform['m_Children']]

                bones['root']: Bone = {
                    'name': game_object["m_Name"],
                    'children': children
                }

                # print(transform)

        for root_component_id in root_components_id:
            root_component_id_s = str(root_component_id)

            if root_component_id_s in behaviours:
                b = behaviours[root_component_id_s]['MonoBehaviour']
                print(b)

                if 'root' in bones:
                    if 'm_Color' in b:
                        bones['root']['color'] = b['m_Color']
                    if 'm_Length' in b:
                        bones['root']['length'] = b['m_Length']
                    if 'm_ChildTransform' in b:
                        child = b['m_ChildTransform']['fileID']
                        if str(child) in transforms:
                            bones['root']['child'] = child

                    # color: Optional[str]
                    #     alpha: Optional[str]
                    #     length: Optional[str]
                    #     child: Optional[str]

        if 'root' in bones:

            # export_mode_bones.append({
            #     "name": bones['root']['name'],
            #     "parent": "root",
            #     "transform": {
            #         "x": -13.06,
            #         "y": -65.03
            #     },
            # })

            bones['id'] = {}
            for bone_id in bones['root']['children']:
                new_bone = fetch_children_bone_from(bone_id)

                db_bone = {
                    "length": str(round(float(new_bone['length']) * SCALE_FACTOR)) if 'length' in new_bone else '0',
                    "name": new_bone['name'],
                    "parent": "root",
                    "transform": {
                        "x": new_bone['position']['x'] * SCALE_FACTOR,
                        "y": -1 * new_bone['position']['y'] * SCALE_FACTOR
                    },
                }

                if 'euler_angles' in new_bone and 'z' in new_bone['euler_angles']:
                    z_rotate = round(float(new_bone['euler_angles']['z']), 3)

                    if z_rotate != 0:
                        db_bone["transform"]["skX"] = z_rotate
                        db_bone["transform"]["skY"] = z_rotate

                export_mode_bones.append(db_bone)

            print(bones)
            break


# save mid-stage bones tree
with open('hasumiTfront_bones_struct.json', 'w+', encoding='utf-8') as file:
    json.dump(bones, file)

# Loading the DragonBones skeleton to inject its position back
with open('hasumiTfront_ske.json', encoding='utf-8') as file:
    hasumiTfront_ske = json.load(file)


# print bones

MAX_INDENT_SIZE_WITH_NAME = 42


def print_bone(bone: Bone, bone_id: int = 0, header: str = '', space=False, indent=0, position=0, size=0):
    """Print a bone pretty"""
    name = bone['name']
    # ─ │ ┐ ┘ ┌ └ ├ ┤ ┬ ┴ ┼

    # if position == size:
    #     header += '  '
    # else:
    #     header += '│ '

    if indent > 0:
        if space:
            header += '  '
        else:
            header += '│ '

    indent += 1

    tail = ''
    # if indent >= 1:
    #   head = '│ '*(indent-1)
    if position < size:
        tail += '├─'
        space = False
    else:
        tail += '└─'
        space = True

    details = ' ' * (MAX_INDENT_SIZE_WITH_NAME - (len(name) + 2*(indent+1)))
    if 'position' in bone:
        details += f"\tP {bone['position']['x']}:{bone['position']['y']}:{bone['position']['z']}"
    if 'rotation' in bone:
        details += f" R {bone['rotation']['x']}:{bone['rotation']['y']}:{bone['rotation']['z']}"
    if 'scale' in bone:
        details += f"\tS {bone['scale']['x']}:{bone['scale']['y']}:{bone['scale']['z']}"
    if 'euler_angles' in bone:
        details += f"\tE {bone['euler_angles']['x']}:{bone['euler_angles']['y']}:{bone['euler_angles']['z']}"
    if 'color' in bone:
        details += f"\tC {bone['color']['r']}:{bone['color']['g']}:{bone['color']['b']}"
    if 'child' in bone:
        details += f"\tT {bone['child']} (Transform)"
    if 'length' in bone:
        details += f"\tL {bone['length']}"

        # rotation
    # position
    # scale
    # euler_angles

    print(f"{header}{tail}{name} [{bone_id:^6}] {details}")

    i = 0
    l = len(bone['children'])

    for child_id in bone['children']:
        i += 1

        if child_id in bones['id']:
            print_bone(bones['id'][child_id], child_id, header, space, indent, position=i, size=l)


if 'root' in bones:
    print(":: BONES LIST  ::")
    print_bone(bones['root'])
    print("\n")

# Save all bones to skel

hasumiTfront_ske['armature'][0]['bone'] = [
    {
        "name": "root",
        "transform": {
            "x": -0.8394,
            "y": -6.7154,
        }
    }
]
hasumiTfront_ske['armature'][0]['bone'].extend(export_mode_bones)

# Keeping track of the drawing order
draw_order = {}

for file_id, t in transforms.items():
    # Getting the transforms from the Scene and mapping them to their GameObjects

    transform = t['Transform']
    # So that's how we link GameObject to Transforms, no wonder why Unity is that slow !
    game_object_id = str(transform['m_GameObject']['fileID'])

    if game_object_id in game_objects:
        # I guess the easiest way to use transform in the GameObject, should refactor this if it get serious
        game_objects[game_object_id]['_transform'] = transform

        if game_objects[game_object_id]['GameObject']["m_Name"].startswith('image_hasumiTfront_'):
            # Get that drawing order for later
            order = transform['m_RootOrder']
            draw_order[order] = {
              "name": game_objects[game_object_id]['GameObject']["m_Name"],
              "parent": "root"
            }

for file_id, s in skin_mesh_rend.items():
    # Getting the linked bones
    skin_mesh = s['SkinnedMeshRenderer']
    game_object_id = str(skin_mesh['m_GameObject']['fileID'])

    if game_object_id in game_objects:
        game_objects[game_object_id]['_skin_mesh'] = skin_mesh


# Reading the GameObjects and displaying them with some Unity-looking T-UI !
for file_id, g in game_objects.items():
    game_object = g['GameObject']

    icon = '#'
    m_icon = game_object['m_Icon']
    if 'fileID' in m_icon and m_icon['fileID'] == 0:
        icon = '🧊'  # The 3D-BOX

    name = game_object["m_Name"]

    if not 'image_hasumiTfront_' in name:
        continue

    print(f'{icon} {name:<28} \t\t\t\t :{file_id}')

    if '_transform' in g:
        # Looking for the best 3D-axis-looking unicode
        # "△⋏∴ 🌠 ▣▢▦▨▾◐"
        # https://unicode-table.com/en/sets/symbols-for-steam/
        transform = g['_transform']

        game_object_lookup_transform[name] = transform

        pos = transform['m_LocalPosition']
        rot = transform['m_LocalRotation']
        scl = transform['m_LocalScale']
        s = ' '*2
        print(f'{s} ∴  Transform')
        print(f'{s} Position      \t X {pos["x"]:<12} \t Y {pos["y"]:<12} \t Z {pos["z"]:<12}')
        print(f'{s} Rotation      \t X {rot["x"]:<12} \t Y {rot["y"]:<12} \t Z {rot["z"]:<12}')
        print(f'{s} Scale         \t X {scl["x"]:<12} \t Y {scl["y"]:<12} \t Z {scl["z"]:<12}')
        print('')

    if '_skin_mesh' in g:
        skin_mesh = g['_skin_mesh']

        s = ' ' * 2
        print(f'{s} ▧  Skinned Mesh Renderer')

        # TODO: get the meshes
        bones_id = [str(i['fileID']) for i in skin_mesh['m_Bones']]
        root_bone_id = str(skin_mesh['m_RootBone']['fileID'])
        root_bone_dislay = None
        if root_bone_id in transforms:
            root_bone = transforms[root_bone_id]['Transform']
            root_bone_go_id = str(root_bone['m_GameObject']['fileID'])
            if root_bone_go_id in game_objects:
                root_bone_go = game_objects[root_bone_go_id]['GameObject']

                all_bones = []

                for bone_id in bones_id:
                    if bone_id in transforms:
                        bone_trf_go_id = str(transforms[bone_id]['Transform']['m_GameObject']['fileID'])
                        if bone_trf_go_id in game_objects:
                            all_bones.append(game_objects[bone_trf_go_id]['GameObject'])

                all_bones_names = ', '.join([i["m_Name"] for i in all_bones])
                print(f'{s} Root Bone      \t 🧊 {root_bone_go["m_Name"]}')
                if len(all_bones) > 1:
                    print(f'{s}      Bones     \t [ {all_bones_names} ]')

        bounds = skin_mesh['m_AABB']
        center = bounds['m_Center']
        extent = bounds['m_Extent']

        print(f'{s} Bounds Center  \t X {center["x"]:<12} \t Y {center["y"]:<12} \t Z {center["z"]:<12}')
        print(f'{s}        Extent  \t X {extent["x"]:<12} \t Y {extent["y"]:<12} \t Z {extent["z"]:<12}')
        print('')

    print('')

    # Looks like they isn't transforms in the linked components...

    # for c in game_object['m_Component']:
    #     c_id = c['component']['fileID']
    #     if c_id in transforms:
    #         transform = transforms[c_id]
    #         print(f'>   {transform}')

# Note :
# Draw Order is ['armature'][0]['slot'] order, it's displayed reversed

# Keeping track of older slots, sorting new one and merging old slots back ! Python's awesome
old_slots_order = hasumiTfront_ske['armature'][0]['slot']

slots = [draw_order[k] for k in sorted(draw_order)]
slots.extend(s for s in old_slots_order if s not in slots)

hasumiTfront_ske['armature'][0]['slot'] = slots


for slot in hasumiTfront_ske['armature'][0]['skin'][0]['slot']:
    name = slot['name'].replace('_boundingBox', '')

    # Use the lookup to find back the transform !
    if name in game_object_lookup_transform:
        transform = game_object_lookup_transform[name]

        # Change the transform, inverting the Y because of Unity => DragonBones format
        slot['display'][0]['transform']['x'] = round(transform['m_LocalPosition']["x"] * SCALE_FACTOR, 3)
        slot['display'][0]['transform']['y'] = round(-1 * transform['m_LocalPosition']["y"] * SCALE_FACTOR, 3)

# And finally write back our happy skeleton !
with open('hasumiTfront_out_withBones_ske.json', 'w+', encoding='utf-8') as file:
    json.dump(hasumiTfront_ske, file)
