"""树林场景与纯色几何体构造器。"""
from copy import deepcopy
from ursina import AmbientLight, DirectionalLight, Entity, Sky, Vec3, camera, color, scene
from ursina.collider import BoxCollider
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
from ursina.shaders import lit_with_shadows_shader
from .config import SLOTS

def build_world(rng):
    # 圆柱和圆锥使用程序网格，避免依赖并不存在的同名模型文件。
    meshes = {'cylinder': Cylinder(resolution=16, start=-.5),
              'cone': Cone(resolution=12)}
    cone = meshes['cone']
    normals = []
    for index in range(0, len(cone.vertices), 3):
        a, b, c = (Vec3(v) for v in cone.vertices[index:index + 3])
        normal = (b - a).cross(c - a).normalized()
        normals.extend([normal] * 3)
    cone.normals = normals
    cone.generate()

    def tint(r, g, b):
        return color.rgb32(r, g, b)

    def part(parent=scene, model='cube', position=(0, 0, 0),
             scale=(1, 1, 1), shade=None, rotation=(0, 0, 0), solid=False):
        model = deepcopy(meshes[model]) if model in meshes else model
        return Entity(parent=parent, model=model, position=position, scale=scale,
                      color=shade if shade is not None else color.white,
                      rotation=rotation, collider='box' if solid else None,
                      shader=lit_with_shadows_shader)

    Sky()
    AmbientLight(color=tint(185, 192, 183))
    sun = DirectionalLight(shadows=False, color=tint(210, 193, 159))
    sun.look_at(Vec3(1, -2, -1))
    scene.fog_color = tint(162, 189, 196)
    scene.fog_density = (25, 70)
    part(position=(0, -.5, 12), scale=(65, 1, 70),
         shade=tint(104, 120, 79), solid=True)
    # 小径与散落石块为纯色几何体；天空使用引擎自带资源。
    part(position=(0, .006, 0), scale=(5, .01, 30), shade=tint(155, 144, 108))
    for _ in range(38):
        x, z = rng.uniform(-27, 27), rng.uniform(-14, 40)
        if abs(x) < 4:
            continue
        part(model='sphere', position=(x, .14, z),
             scale=(rng.uniform(.4, 1.3), .35, .7), shade=tint(126, 132, 113))

    # 两侧和远处的树林保留中央射击视野；树干有碰撞，树冠仅用于装饰。
    for side in (-1, 1):
        for index in range(15):
            x = side * rng.uniform(12, 27)
            z = -12 + index * 3.8
            height = rng.uniform(6, 10)
            part(model='cylinder', position=(x, height / 2, z),
                 scale=(.65, height, .65), shade=tint(83, 66, 48), solid=True)
            for tier in range(3):
                part(model='cone', position=(x, height * .58 + tier * 1.4, z),
                     scale=(5 - tier, 3.6, 5 - tier),
                     shade=tint(49 + tier * 5, 81 + tier * 7, 57 + tier * 4))
    for x in (-15, -9, 0, 9, 15):
        part(model='sphere', position=(x, 1.1, 36), scale=(13, 7, 10),
             shade=tint(100, 125, 105))

    # 栅栏标示可活动区域，隐藏碰撞墙防止走出场地。
    for z in (-15, 30):
        for x in range(-12, 13, 3):
            part(position=(x, .65, z), scale=(.16, 1.3, .16), shade=tint(98, 78, 53))
        for y in (.45, .95):
            part(position=(0, y, z), scale=(24, .12, .1), shade=tint(127, 102, 67))
    for pos, size in [((-16, 3, 7), (1, 6, 46)), ((16, 3, 7), (1, 6, 46)),
                      ((0, 3, -15.5), (33, 6, 1)), ((0, 3, 30.5), (33, 6, 1))]:
        wall = Entity(model='cube', position=pos, scale=size, collider='box')
        wall.visible = False

    return part, tint
