import yaml
import json

# Unity consts - Screaming at y'a
TRANSFORM = '4'
GAME_OBJECT = '1'

# Will store transforms and GameObject for further mapping
transforms = {}
game_objects = {}

# Used to locate back Transforms when applying to DragonBones Skeleton
game_object_lookup_transform = {}

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
            if 'm_Name: image_hasumiTfront_' in block:
                game_objects[file_id] = yaml.safe_load(block[file_id_index_end:])

                # print(f'{file_id} -> GameObject')

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

        # Get that drawing order for later
        order = transform['m_RootOrder']
        draw_order[order] = {
          "name": game_objects[game_object_id]['GameObject']["m_Name"],
          "parent": "root"
        },


# Loading the DragonBones skeleton to inject its position back
with open('hasumiTfront_ske.json', encoding='utf-8') as file:
    hasumiTfront_ske = json.load(file)


# Reading the GameObjects and displaying them with some Unity-looking T-UI !
for file_id, g in game_objects.items():
    game_object = g['GameObject']

    icon = '#'
    m_icon = game_object['m_Icon']
    if 'fileID' in m_icon and m_icon['fileID'] == 0:
        icon = '🧊'  # The 3D-BOX

    name = game_object["m_Name"]

    print(f'{icon} {name:<28} \t\t\t\t :{file_id}')

    if '_transform' in g:
        # Looking for the best 3D-axis-looking unicode
        # "△⋏∴"
        transform = g['_transform']

        game_object_lookup_transform[name] = transform

        pos = transform['m_LocalPosition']
        rot = transform['m_LocalRotation']
        scl = transform['m_LocalScale']
        s = ' '*2
        print(f'{s} ∴  Transform')
        print(f'{s} Position   \t X {pos["x"]:<12} \t Y {pos["y"]:<12} \t Z {pos["z"]:<12}')
        print(f'{s} Rotation   \t X {rot["x"]:<12} \t Y {rot["y"]:<12} \t Z {rot["z"]:<12}')
        print(f'{s} Scale      \t X {scl["x"]:<12} \t Y {scl["y"]:<12} \t Z {scl["z"]:<12}')
        print('')

    # Looks like they isn't transforms in the linked components...

    # for c in game_object['m_Component']:
    #     c_id = c['component']['fileID']
    #     if c_id in transforms:
    #         transform = transforms[c_id]
    #         print(f'>   {transform}')


# Scale it ! 100 seems safe from Unity => DragonBones
SCALE_FACTOR = 100

# Note :
# Draw Order is ['armature'][0]['slot'] order, it's displayed reversed

for slot in hasumiTfront_ske['armature'][0]['skin'][0]['slot']:
    name = slot['name']

    # Use the lookup to find back the transform !
    if name in game_object_lookup_transform:
        transform = game_object_lookup_transform[name]

        # Change the transform, inverting the Y because of Unity => DragonBones format
        slot['display'][0]['transform']['x'] = round(transform['m_LocalPosition']["x"] * SCALE_FACTOR, 3)
        slot['display'][0]['transform']['y'] = round(-1 * transform['m_LocalPosition']["y"] * SCALE_FACTOR, 3)

# Keeping track of older slots, sorting new one and merging old slots back ! Python's awesome
old_slots_order = hasumiTfront_ske['armature'][0]['slot']

slots = [draw_order[k][0] for k in sorted(draw_order)]
slots.extend(s for s in old_slots_order if s not in slots)

hasumiTfront_ske['armature'][0]['slot'] = slots

# And finally write back our happy skeleton !
with open('hasumiTfront_out_ske.json', 'w+', encoding='utf-8') as file:
    json.dump(hasumiTfront_ske, file)