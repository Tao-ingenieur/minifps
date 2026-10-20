"""HUD、准星、菜单及按钮构造；事件由 game 绑定。"""
from ursina import Entity, Button, Text, camera, color
from .config import VERSION

def build_ui(tint):
    hud = Entity(parent=camera.ui)
    Entity(parent=hud, model='quad', position=(-.51, .35), scale=(.72, .26),
           color=color.rgba32(20, 30, 25, 195))
    Text(f'WOODLAND / v{VERSION}', parent=hud, position=(-.85, .46), scale=.85,
         color=tint(220, 210, 171))
    counter = Text(parent=hud, position=(-.85, .42), scale=1)
    status = Text(parent=hud, position=(-.85, .38), scale=.85)
    feedback = Text(parent=hud, position=(-.85, .33), scale=.85, color=tint(220, 210, 171))
    personal = Text(parent=hud, position=(-.85, .28), scale=.75, color=tint(220, 210, 171))
    reticle = Entity(parent=hud)
    for pos, size in [((-.009, 0), (.009, .0015)), ((.009, 0), (.009, .0015)),
                      ((0, -.009), (.0015, .009)), ((0, .009), (.0015, .009))]:
        Entity(parent=reticle, model='quad', position=pos, scale=size,
               color=color.rgba32(245, 242, 219, 215))
    Text('WASD MOVE / MOUSE LOOK / RMB ZOOM / HOME FACE BIRDS / ESC PAUSE / F11 FULLSCREEN',
         parent=hud, position=(-.85, -.46), scale=.72, color=tint(242, 239, 220))
    toast = Text(parent=camera.ui, origin=(0, 0), position=(.3, .45), z=-.4,
                 scale=.8, color=tint(242, 225, 170), enabled=False)

    menu = Entity(parent=camera.ui)
    Entity(parent=menu, model='quad', scale=(4, 2), z=.2,
           color=color.rgba32(8, 15, 13, 175))
    Entity(parent=menu, model='quad', scale=(1.36, .96), z=.1, color=tint(27, 40, 34))
    menu_title = Text(parent=menu, origin=(0, 0), position=(0, .395), z=-.1,
                      scale=1.8, color=tint(233, 219, 169))
    menu_subtitle = Text(parent=menu, origin=(0, 0), position=(0, .325), z=-.1, scale=.95)
    details = Text(parent=menu, position=(-.58, .25), z=-.1, scale=.85, line_height=1.25)
    menu_notice = Text(parent=menu, position=(-.61, -.435), z=-.2, scale=.67,
                       color=tint(234, 207, 144))
    def button(text, x, y, shade=None):
        return Button(parent=menu, text=text, position=(x, y), z=-.1,
                      scale=(.35, .055), color=shade or tint(66, 83, 69))
    primary = button('START / ENTER', -.40, -.125, tint(88, 114, 78))
    restart_button = button('NEW ROUND / R', 0, -.125)
    history_button = button('HISTORY', .40, -.125)
    save_button = button('QUICK SAVE / F5', -.40, -.20)
    load_button = button('QUICK LOAD / F9', 0, -.20)
    export_button = button('EXPORT JSON / F6', .40, -.20)
    import_button = button('IMPORT JSON / F7', -.40, -.275)
    display_button = button('FULLSCREEN / F11', 0, -.275)
    about_button = button('ABOUT / F1', .40, -.275)
    exit_button = button('SAVE & EXIT', 0, -.35)
    face_button = button('FACE BIRDS / HOME', -.40, -.35)
    back_button = button('BACK / ESC', .40, -.35)
    buttons = [primary, restart_button, history_button, save_button, load_button,
               export_button, import_button, display_button, about_button, exit_button, face_button, back_button]
    return (hud, counter, status, feedback, personal, reticle, toast, menu,
            menu_title, menu_subtitle, details, menu_notice, primary, restart_button,
            history_button, save_button, load_button, export_button, import_button,
            display_button, about_button, exit_button, face_button, back_button, buttons)
