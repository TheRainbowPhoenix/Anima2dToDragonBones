import yaml
from PIL import Image, ImageOps
import os

from shapely.geometry import Polygon, mapping
from shapely.geometry import MultiPoint
from shapely.ops import triangulate


# os.mkdir("unpack")

def generate_edges(vertices: list) -> list:
    points = [(x, y) for x, y in zip(vertices[::2], vertices[1::2])]
    poly = Polygon(points)

    coords = poly.exterior.coords[:]

    out = sum(
        [
            [
                points.index(coords[i]),
                points.index(coords[i+1]),
            ]
            for i in range(len(coords)-1)],
        [])

    return out


def generate_triangles(vertices: list) -> list:
    points = [(x, y) for x, y in zip(vertices[::2], vertices[1::2])]
    poly = Polygon(points)
    triangles = triangulate(poly)

    triangles_list = []

    for triangle in triangles:
        coords = triangle.exterior.coords[:]

        coords_out = []
        for coord in coords:
            if coord in points:
                i = points.index(coord)
                if i not in coords_out:
                    coords_out.append(i)
        if len(coords_out) == 3:
            triangles_list.append(coords_out)

    return triangles_list


def generate_uvs(outline: list, width: int, height: int) -> list:
    """
    Generate UVS from outline
    :param height: Base height
    :param width: Base width
    :param outline: list of x,y for each node
    :return: list of uv
    """

    """
            Translate
                 Base :     To:
                    y
            +    +--^--+    +-----> x   +
            |    |  |  |    |     |     |
    height  |    <--+--> x  |     |     |  1
            |    |  |  |    |     |     |
            +    +--v--+    v-----+     +
                    y
            +-----+    +-----+
             width       1

    Translate a point :
        x= x+w/2
        y= y-h/2
    Revert y axis:
        y= -1*y
    Scale from (h,w) to (1,1)
        x= x/w
        y= y/h
    """

    points = []

    # FIXME: bug, textures are flipped upside down !

    for coords in outline:
        c_x = coords['x']
        c_y = coords['y']

        x = c_x + width/2
        y = c_y + height/2
        # y = -1*(c_y - height / 2)

        o_x = round(x / width, 5)
        o_y = round(1-(y / height), 5)

        points.append(o_x)
        points.append(o_y)



    # return sum(
    #     [[
    #         round((-1 * (-i['y'] - height / 2)) / height, 5),  # y
    #         round((i['x'] + width / 2) / width, 5),  # x
    #
    #     ] for i in outline],
    #     [])

    return points

def anima2d_to_dragon_bones():
    anima2d_name = "hasumiTfront"

    data = {
        "frameRate": 24,
        "name": f"{anima2d_name}",
        "version": "5.5",
        "compatibleVersion": "5.5",
        "armature": [
            {
                "type": "Armature",
                "frameRate": 24,
                "name": "hair",
                "aabb": {
                    "x": -32.5,
                    "y": -150.51,
                    "width": 219.3,
                    "height": 250
                },
                "bone": [
                    {
                        "name": "root"
                    }
                ],
                "slot": [
                    # {
                    #     "name": "name",
                    #     "parent": "root"
                    # }
                ],
                "skin": [
                    {
                        "slot": [

                        ]
                    }
                ],
                "animation": [
                    {
                        "duration": 0,
                        "playTimes": 0,
                        "name": "animtion0"
                    }
                ],
                "defaultActions": [
                    {
                        "gotoAndPlay": "animtion0"
                    }
                ]
            }
        ]
    }

    im = Image.open(f"image_{anima2d_name}.png")
    Iwidth, Iheight = im.size

    with open(f'image_{anima2d_name}.png.meta', 'r') as file:
        image_hasumiTfront = yaml.safe_load(file)

    spriteSheet = image_hasumiTfront['TextureImporter']['spriteSheet']

    for sprite in spriteSheet['sprites']:
        width = sprite['rect']['width']
        height = sprite['rect']['height']

        x = sprite['rect']['x']
        y = Iheight - height - sprite['rect']['y']

        name = sprite['name']

        pivot = sprite['pivot'] if 'pivot' in sprite else {'x': 0.50, 'y': 0.50}

        rotate = None

        outline = sprite['outline'] if 'outline' in sprite else []
        physics_shape = sprite['physicsShape'] if 'physicsShape' in sprite else []

        print(name)
        print(sprite['border'])
        print(sprite['outline'])
        print(sprite['physicsShape'])

        im1 = im.crop((x, y, x + width, y + height))

        filename = "unpack/" + name

        data['armature'][0]['slot'].append({
            'name': name,
            "parent": "root"
        })

        vertices = sum(
            [[i['x'], -i['y']] for i in outline[0]],
            []
        )

        data['armature'][0]['skin'][0]['slot'].append({
            'name': name,
            'display': [
                {
                    'name': name,
                    "transform": {
                        "x": round(x, 3),
                        "y": round(y, 3)
                    },

                    'pivot': pivot,

                    "type": "mesh",
                    "width": int(width),
                    "height": int(height),
                    # "vertices": [],
                    # "uvs": [],
                    # "triangles": [],
                    # "edges": [],
                    # "userEdges": []

                    "vertices": vertices,

                    # "vertices": [
                    #     -round(width/2, 3), -round(height/2, 3),
                    #     round(width/2, 3), -round(height/2, 3),
                    #     -round(width/2, 3), round(height/2, 3),
                    #     round(width/2, 3), round(height/2, 3)
                    # ],

                    "uvs": generate_uvs(outline[0], width, height),

                    # "triangles": [
                    #     0, 1, 2,
                    #     1, 3, 2
                    # ],

                    "triangles": sum(generate_triangles(vertices), []),

                    # "edges": [
                    #     0, 1,
                    #     1, 3,
                    #     3, 2,
                    #     2, 0
                    # ],
                    "edges": generate_edges(vertices),
                    "userEdges": []
                }
            ]
        })

        if len(physics_shape) > 0:
            data['armature'][0]['slot'].append({
                'name': f'{name}_boundingBox',
                "parent": name
            })

            transform = {
                "x": round(x, 3),
                "y": round(y, 3),
            }

            if rotate:
                transform.update({
                    "skX": round(rotate['x'] * 100, 3),
                    "skY": round(rotate['y'] * 100, 3)
                })

            data['armature'][0]['skin'][0]['slot'].append({
                'name': f'{name}_boundingBox',
                'display': [
                    {
                        'name': f'{name}_boundingBox',
                        'type': "boundingBox",
                        'subType': "polygon",
                        'pivot': pivot,
                        "vertices": sum(
                            [[i['x'], -i['y']] for i in physics_shape[0]],
                            []),
                        "transform": transform
                    }
                ]
            })

        # Hack cause I'm terrible with UV
        # im1 = ImageOps.flip(im1)
        im1.save(filename + ".png", "PNG")

    with open(f"{anima2d_name}_ske.json", "w+") as out:
        import json
        json.dump(data, out, indent=2)


def do_tests():
    width = 65
    height = 104

    vertices = [
        -108, -63.5,
        -43, -63.5,
        -108, 40.5,
        -43, 40.5
    ]

    outline = [[
        {'x': -108, 'y': 63.5},
        {'x': -43, 'y': 63.5},
        {'x': -108, 'y': -40.5},
        {'x': -43, 'y': -40.5},
    ]]

    expected_uvs = [
        0, 0,
        1, 0,
        0, 1,
        1, 1
    ]

    expected_triangles = [
        1, 0, 3,
        0, 2, 3
    ]

    expected_edges = [
        0, 1,
        1, 3,
        3, 2,
        2, 0
    ]

    uvs = generate_uvs(outline[0], width, height)

    edges = generate_edges(vertices)

    triangles = generate_triangles(vertices)

    print(uvs)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and 'test' in sys.argv[1:]:
        do_tests()
    else:
        anima2d_to_dragon_bones()
