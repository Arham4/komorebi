import enum

from gi.repository import Clutter


class Wallpaper(Clutter.Actor):
    # Wallpaper name
    name = None

    def __init__(self, screen, config_file):
        Clutter.Actor.__init__(self)

        self.name = config_file.get_string('Info', 'Name')
        self.set_size(screen.width, screen.height)

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


class WallpaperType(enum.Enum):
    IMAGE = 'image'
    VIDEO = 'video'
    WEB = 'web_page'
