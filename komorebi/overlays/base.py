import enum

from gi.repository import Clutter


class Overlay(Clutter.Actor):
    def __init__(self):
        Clutter.Actor.__init__(self)

    # Called whenever it's time to register behaviour dependent on the menu
    def register_menu_actions(self, menu):
        pass

    # Called whenever a setting was changed globally.
    # Returns if the object is to be removed or not.
    def on_settings_changed(self, setting_key):
        pass

    # Called when this object is about to be unloaded
    def on_unload(self):
        pass


class OverlayType(enum.Enum):
    CLOCK = 'DateTime'
    ASSET = 'Asset'
    DESKTOP = 'Desktop'
