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

            print(curve['path'])

            time_line = {}

            for m in c['m_Curve']:
                t = round(m['time']*T_SCALE)
                val = m['value']
                time_line[t] = val

            # Generates steps on "MAX_T" characters
            for t in range(MAX_T):
                c = "♦" if t in time_line else ' '
                print(c, end='')
            print('')

    # print(anim_hasumiTfront)


if __name__ == '__main__':
    load_anim()
