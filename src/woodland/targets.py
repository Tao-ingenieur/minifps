"""鸟靶模型、命中碰撞与栖木；射击结算由 game 协调。"""
from ursina import Entity, Vec3, color
from ursina.collider import BoxCollider
from .config import SLOTS

def build_targets(part, tint, rng):
    # 鸟根节点承担命中碰撞，身体、头、喙、双翼、尾羽都是其子节点。
    birds = []
    def make_bird(position, heading=0, slot=None):
        bird = Entity(position=position, rotation_y=heading)
        bird.slot = len(birds) if slot is None else slot
        bird.collider = BoxCollider(bird, center=Vec3(0, .05, 0),
                                    size=Vec3(1.35, .85, 1))
        brown, cream = tint(137, 101, 67), tint(222, 201, 153)
        part(bird, model='sphere', scale=(.56, .49, .78), shade=brown)
        part(bird, model='sphere', position=(0, -.06, -.21),
             scale=(.40, .35, .36), shade=cream)
        part(bird, model='sphere', position=(0, .25, -.32), scale=.38, shade=brown)
        part(bird, model='cone', position=(0, .23, -.58),
             scale=(.15, .23, .15), shade=tint(217, 165, 67), rotation=(-90, 0, 0))
        for side in (-1, 1):
            part(bird, model='sphere', position=(side * .155, .30, -.43),
                 scale=.065, shade=tint(15, 20, 18))
            part(bird, model='sphere', position=(side * .175, .312, -.445),
                 scale=.018, shade=color.white)
            part(bird, model='sphere', position=(side * .34, .05, .04),
                 scale=(.55, .13, .49), shade=tint(90, 69, 49),
                 rotation=(0, side * 20, side * -12))
            part(bird, position=(side * .12, -.32, .08), scale=(.035, .20, .035),
                 shade=tint(185, 137, 66))
            part(bird, position=(side * .12, -.41, -.015), scale=(.13, .035, .20),
                 shade=tint(185, 137, 66))
        for x in (-.13, 0, .13):
            part(bird, model='sphere', position=(x, .02, .49),
                 scale=(.14, .09, .55), shade=tint(74, 60, 46), rotation=(15, x * 90, 0))
        birds.append(bird)
        return bird

    perches, perch_models = [], []
    for index, (x, y, z) in enumerate(SLOTS):
        x += rng.uniform(-.5, .5)
        perches.append((x, y, z))
        make_bird((x, y, z), rng.uniform(-35, 35), index)
        perch = Entity(position=(x, 0, z))
        perch_models.append(perch)
        part(perch, model='cylinder', position=(0, (y - .43) / 2, 0),
             scale=(.18, y - .43, .18), shade=tint(99, 77, 51), solid=True)
        part(perch, position=(0, y - .46, 0), scale=(1.3, .11, .16), shade=tint(99, 77, 51))

    return birds, make_bird, perches, perch_models
