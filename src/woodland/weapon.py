"""摄像机上的多部件猎枪模型（无碰撞）。"""
from ursina import Entity, camera, color

def build_weapon(part, tint):
    # 多部件猎枪：木质枪托、金属机匣、长枪管、瞄准镜、扳机护圈及持枪手。
    # 全部模型是摄像机子物体且没有碰撞，不干扰射线检测。
    gun = Entity(parent=camera, position=(.25, -.25, .82),
                 rotation=(0, -7, -2), scale=.52)
    wood, dark, steel = tint(118, 72, 39), tint(38, 44, 47), tint(87, 98, 102)
    part(gun, position=(0, -.035, -.32), scale=(.16, .23, .75),
         shade=wood, rotation=(-8, 0, 0))
    part(gun, position=(0, -.09, -.68), scale=(.18, .30, .05), shade=dark)
    part(gun, position=(0, .03, .08), scale=(.145, .15, .47), shade=steel)
    part(gun, position=(0, -.04, .42), scale=(.17, .16, .39), shade=wood)
    part(gun, model='cylinder', position=(0, .11, .91), scale=(.065, 1.18, .065),
         shade=dark, rotation=(90, 0, 0))
    part(gun, model='cylinder', position=(0, .11, 1.51), scale=(.085, .045, .085),
         shade=steel, rotation=(90, 0, 0))
    part(gun, model='circle', position=(0, .11, 1.535), scale=.055,
         shade=color.black, rotation=(0, 180, 0))
    for z in (-.04, .27):
        part(gun, position=(0, .19, z), scale=(.10, .15, .06), shade=dark)
    part(gun, model='cylinder', position=(0, .29, .11), scale=(.12, .60, .12),
         shade=dark, rotation=(90, 0, 0))
    for z in (-.21, .42):
        part(gun, model='cylinder', position=(0, .29, z), scale=(.19, .12, .19),
             shade=dark, rotation=(90, 0, 0))
    part(gun, model='circle', position=(0, .29, -.275), scale=.145,
         shade=tint(45, 117, 130))
    # 护圈用三段细条，避免将扳机区域画成一整块。
    for pos, size in [((0, -.22, .02), (.045, .025, .22)),
                      ((0, -.16, -.08), (.045, .13, .025)),
                      ((0, -.16, .12), (.045, .13, .025))]:
        part(gun, position=pos, scale=size, shade=dark)
    part(gun, position=(0, -.14, 0), scale=(.025, .08, .025), shade=steel,
         rotation=(20, 0, 0))
    part(gun, model='sphere', position=(.15, .06, -.02), scale=.07, shade=steel)
    part(gun, position=(.10, .06, -.02), scale=(.16, .035, .035), shade=steel)
    for pos, size, rotation in [((.07, -.15, -.27), (.18, .19, .28), (15, 0, -15)),
                                ((-.05, -.14, .43), (.20, .15, .27), (0, 0, 15))]:
        part(gun, model='sphere', position=pos, scale=size,
             shade=tint(78, 83, 58), rotation=rotation)
    part(gun, position=(.10, -.31, -.35), scale=(.21, .36, .22),
         shade=tint(65, 77, 59), rotation=(-25, 0, -12))

    return gun
