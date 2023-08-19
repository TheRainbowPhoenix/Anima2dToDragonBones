import json

import yaml


class UnityLoader(yaml.SafeLoader):
    """
    Create a custom YAML loader for unity
    """
    def load74(self, node):
        """
        Load Unity's code 74 assets (animations)
        :param node: YAML Node
        :return: parsed node
        """
        return self.construct_mapping(node)


# Add Unity Loaders
UnityLoader.DEFAULT_TAGS.update({u'!u!': u'tag:unity3d.com,2011'})
UnityLoader.add_constructor("tag:unity3d.com,2011:74", UnityLoader.load74)


animation = []

def load_anim():
    """
    Loads an animation file and print its keyframes.
    :return:
    """
    with open(f'hasumi@idle_Tfront_1.anim', 'r') as file:
        anim_hasumiTfront = yaml.load(file, Loader=UnityLoader)

    anim_clip = anim_hasumiTfront['AnimationClip']
    print(f"Anim: {anim_clip['m_Name']}")

    # anims are often X.333 or X.6666s so anything*3 will round them
    T_SCALE = 9
    # Max anim duration is ~12s
    MAX_T = 12*T_SCALE

    IPS = anim_clip['m_SampleRate']

    bone = []

    bonesByNames = {}

    # Curves with keyframes
    for curve_type in [
        'm_RotationCurves',
        'm_CompressedRotationCurves',
        'm_EulerCurves',
        'm_PositionCurves',
        'm_ScaleCurves',
        'm_FloatCurves',
        'm_PPtrCurves'
    ]:
        for curve in anim_clip[curve_type]:
            c = curve['curve']

            path: str = curve['path']
            name = path.split('/')[-1]
            print(path, name)



            if name not in bonesByNames:
                bonesByNames[name] = {
                    "name": path.split('/')[-1],
                    "rotateFrame": [],
                    "translateFrame": [],
                }

            time_line = {}

            previousSlope = None

            for m in c['m_Curve']:
                # time is *IPS, so here 30 IPS => 30 = 1m
                t = round(m['time']*T_SCALE)
                val = m['value']
                inSlope = m['inSlope']
                outSlope = m['inSlope']
                # Rotation: 180 = half circle, 90 = quarter circle  /!\ rotation is inverted between unity and dragonBones
                time_line[t] = val

                if type(val) == int:
                    attribute = curve['attribute']
                    print("TODO : ", attribute)
                    # rotateFrame.append({
                    #     "duration": round(m['time'] * IPS),
                    # })
                    """
                    slot[{name="image_hasumiTfront_13", "displayFrame": [
                        {
                          "duration": 0,
                          "value": -1  # 0s, -1 = hidden 
                        },
                        {
                          "duration": 60  # 2s, visible 
                        }
                      ],
                    """
                    pass
                elif type(val) == float:
                    attribute = curve['attribute']
                    print("TODO : ", attribute)
                elif 'z' in val:
                    if val['z'] != 0:
                        slope = [
                            0.5, 0,  # o---0.5---> ^v 0
                            0.5, 0,  #            <---0.5---o ^v 0
                        ]

                        if inSlope['z'] != 0 or previousSlope != None:
                            slope = [
                                0.5, (previousSlope if previousSlope else 0) * 3,
                                0.5, round(inSlope['z'] * 3, 6),
                                     ]
                            previousSlope = None

                        if outSlope['z'] != 0:
                            previousSlope = outSlope['z']
                            # TODO : this is naive and maybe bad !

                        if name == 'b_head':
                            val['z'] -= 81.58
                        elif name == 'b_body_1':
                            val['z'] += 69.44
                        elif name == 'b_hairfront_1':
                            val['z'] += 10.52
                            val['z'] *= -1
                            val['z'] += -128


                        bonesByNames[name]["rotateFrame"].append({
                            "duration": round(m['time'] * IPS),
                            "curve": slope,
                            "rotate": -1 * val['z']
                        })

                    if val['x'] != 0 or val['y'] != 0:
                        slope = [
                            0.5, 0,  # o---0.5---> ^v 0
                            0.5, 0,  # <---0.5---o ^v 0
                        ]

                        x = (val['x'] * 125) / 2  # TODO: scale this better ?
                        y = (val['y'] * 125) / 2

                        if name == 'b_head':
                            # x -= 10.3084  # -23.06
                            # y -= 139.9169  # -85.98
                            x /= 2
                            y /= 2
                            x += 6.38
                            y -= 25.98
                        elif name == 'b_body_1':
                            # x += -1.840  # -13.06
                            # y -= 105.5688  # -65.03
                            x /= 2
                            y /= 2
                            x += 5.61
                            y -= 20.29


                        bonesByNames[name]["translateFrame"].append({
                            "duration": round(m['time'] * IPS),
                            "x": round(x, 6),  # TODO: scale this ? 200x ?
                            "y": round(y, 6),  # TODO: scale this ?
                            "curve": slope,
                        })

            # Generates steps on "MAX_T" characters
            for t in range(MAX_T):
                c = "♦" if t in time_line else ' '
                print(c, end='')
            print('')


    # print(anim_hasumiTfront)

    duration = (
            anim_clip['m_AnimationClipSettings']['m_StopTime']
            - anim_clip['m_AnimationClipSettings']['m_StartTime']
    ) * anim_clip['m_SampleRate']

    animation.append({
        "name": "hasumi@idle_Tfront_1",
        "playTimes": max(anim_clip['m_AnimationClipSettings']['m_LoopTime'] - 1, 0),
        "duration": round(duration),  # TODO
        "bone": list(bonesByNames.values())
    })

    print(json.dumps(animation))

if __name__ == '__main__':
    load_anim()
