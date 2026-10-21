from __future__ import annotations


def register(controller, toggle='f8', panic='f10'):
    import keyboard
    keyboard.add_hotkey(toggle, controller.toggle)
    keyboard.add_hotkey(panic, controller.panic)
    return keyboard
