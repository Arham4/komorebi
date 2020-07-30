import logging
import os
from enum import IntEnum

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk

import komorebi
from komorebi.overlays.base import OverlayType
from komorebi.settings import ConfigKeys, Settings
from komorebi.wallpapers.base import WallpaperType


# Helper classes to index tuples of information
class MarginIndex(IntEnum):
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOTTOM = 3


class RotationIndex(IntEnum):
    X = 0
    Y = 1
    Z = 2


# Global clipboard
clipboard = None


def init_clipboard(display):
    global clipboard
    logging.info("Initializing clipboard...")

    if clipboard is None:
        clipboard = Gtk.Clipboard.get_for_display(display, Gdk.SELECTION_CLIPBOARD)
    else:
        logging.warning("Clipboard is already initialized!")


def get_wallpaper_config_file(name):
    # Prepare paths
    wallpaper_path = ''
    wallpaper_config_path = ''
    wallpaper_found = False

    # Ensure that wallpaper exists
    for path in Settings.get_wallpaper_paths():
        wallpaper_path = os.path.join(path, name)
        wallpaper_config_path = os.path.join(wallpaper_path, 'config')

        if (name is None or not Gio.File.new_for_path(wallpaper_path).query_exists()
                or not Gio.File.new_for_path(wallpaper_config_path).query_exists()):
            continue

        wallpaper_found = True
        break

    # If not, fallback to the default type
    if not wallpaper_found:
        name = 'foggy_sunny_mountain'
        wallpaper_path = f'{komorebi.__package_datadir__}/{name}'
        wallpaper_config_path = f'{wallpaper_path}/config'

        logging.error(f'got an invalid wallpaper. Setting to default: {name}')

    # Retrieve the wallpaper config
    wallpaper_config = GLib.KeyFile.new()
    wallpaper_config.load_from_file(wallpaper_config_path, GLib.KeyFileFlags.NONE)

    # Add required keys since the new version; this will later be
    # enforced more properly with a file format revision
    update_wallpaper(wallpaper_config, wallpaper_path, name)

    return wallpaper_config


def update_wallpaper(wallpaper_config, wallpaper_path, name):
    # Add a Name section in the metadata
    wallpaper_config.set_string('Info', 'Name', name)

    # Add the Path in the metadata
    wallpaper_config.set_string('Info', 'Path', wallpaper_path)

    # Set up the Order property, which specifies the order of overlays
    order = ''
    if wallpaper_config.has_group('Asset'):
        order = 'Asset'
        if wallpaper_config.has_group('DateTime'):
            order = 'Asset,DateTime' if wallpaper_config.get_boolean('DateTime', 'AlwaysOnTop') else 'DateTime,Asset'
    elif wallpaper_config.has_group('DateTime'):
        order = 'DateTime'

    wallpaper_config.set_string('Info', 'Order', order)


def load_wallpaper(screen, wallpaper_config):
    wallpaper_type = wallpaper_config.get_string('Info', 'WallpaperType')
    if wallpaper_type == WallpaperType.VIDEO.value and not Settings.enable_video_wallpapers:
        wallpaper_type = WallpaperType.IMAGE.value
    wallpaper = None
    if wallpaper_type == WallpaperType.IMAGE.value:
        from komorebi.wallpapers.image import ImageWallpaper
        wallpaper = ImageWallpaper(screen, wallpaper_config)
    elif wallpaper_type == WallpaperType.VIDEO.value:
        from komorebi.wallpapers.video import VideoWallpaper
        wallpaper = VideoWallpaper(screen, wallpaper_config)
    elif wallpaper_type == WallpaperType.WEB.value:
        from komorebi.wallpapers.web import WebWallpaper
        wallpaper = WebWallpaper(screen, wallpaper_config)
    else:
        logging.warning(f"Invalid wallpaper type: {wallpaper_type}")
        raise RuntimeError("Invalid wallpaper type")

    return wallpaper


def load_overlays(screen, wallpaper_config):
    overlays = []

    for overlay in wallpaper_config.get_string('Info', 'Order').split(','):
        if overlay == OverlayType.CLOCK.value:
            from komorebi.overlays.clock import Clock
            overlays.append(Clock(screen, wallpaper_config))
        if overlay == OverlayType.ASSET.value:
            from komorebi.overlays.asset import Asset
            overlays.append(Asset(screen, wallpaper_config))
        # elif overlay == OverlayType.DESKTOP.value: 	# This doesn't exist on wallpaper specification *yet*
    if Settings.show_desktop_icons:					# so for now we simply use this
        from komorebi.overlays.desktop import Desktop
        overlays.append(Desktop(screen))

    return overlays


def on_settings_changed(screen, setting_key):
    overlays = []

    if (setting_key == ConfigKeys.SHOW_DESKTOP
            and Settings.show_desktop_icons):
        from komorebi.overlays.desktop import Desktop
        overlays.append(Desktop(screen))

    return overlays


def get_icon_from(icon, icon_size):
    '''
    Returns an icon detected from file, IconTheme, etc...
    '''
    iconPixbuf = None

    if icon is None or icon == '':
        return iconPixbuf

    # Try those methods:
    # 1- Icon is a file, somewhere in '/'.
    # 2- Icon is an icon in a IconTheme.
    # 3- Icon isn't in the current IconTheme.
    # 4- Icon is not available, use default.
    if Gio.File.new_for_path(icon).query_exists():
        iconPixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon, icon_size, icon_size, False)
        return iconPixbuf

    iconTheme = Gtk.IconTheme.get_default()
    iconTheme.prepend_search_path('/usr/share/pixmaps')

    try:
        iconPixbuf = iconTheme.load_icon(icon, icon_size, Gtk.IconLookupFlags.FORCE_SIZE)
    except GLib.Error:
        if iconPixbuf is None:
            iconPixbuf = iconTheme.load_icon('application-default-icon', icon_size, Gtk.IconLookupFlags.FORCE_SIZE)

    return iconPixbuf


def apply_css(widgets, css):
    provider = Gtk.CssProvider()
    provider.load_from_data(str.encode(css))

    for widget in widgets:
        widget.get_style_context().add_provider(provider, 800)


def apply_alpha(widgets):
    for widget in widgets:
        widget.set_visual(widget.get_screen().get_rgba_visual() or widget.get_screen().get_system_visual())


def can_play_videos():
    '''
    A dirty way to check if gstreamer is installed
    '''
    # FIXME: Horrible way to detect presence of libgstlibav.so
    paths = [
        '/usr/lib',
        '/usr/lib64',
        '/usr/lib/i386-linux-gnu',
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib/arm-linux-gnueabihf'
    ]

    for path in paths:
        if Gio.File.new_for_path(f'{path}/gstreamer-1.0/libgstlibav.so').query_exists():
            return True

    return False


def beautify_wallpaper_name(wallpaper_name):
    '''
    Beautifies the name of the wallpaper
    '''
    result_string = ''

    for word in wallpaper_name.split('_'):
        result_string += word.title() + ' '

    return result_string


def toggle_autostart():
    '''
    Toggle autostart for Komorebi
    '''
    desktop_file_name = 'org.komorebiteam.komorebi.desktop'
    dest_paths = [
        os.environ.get('XDG_CONFIG_HOME', ''),
        os.path.join(GLib.get_home_dir(), '.config')
    ]

    if Settings.autostart:
        # Enable autostart, aka copy the .desktop file to the appropriate folder
        desktop_file = Gio.File.new_for_path(os.path.join(komorebi.__datadir__, 'applications', desktop_file_name))
        if not desktop_file.query_exists():
            logging.warning('Desktop file not found, autostart won\'t work!')
            return

        for path in dest_paths:
            if path == '' or not Gio.File.new_for_path(path).query_exists():
                continue

            dest_file = Gio.File.new_for_path(os.path.join(path, 'autostart', desktop_file_name))
            desktop_file.copy(dest_file, Gio.FileCopyFlags.NONE)
            return

        logging.warning('Couldn\'t find any user directory config, autostart won\'t work!')
    else:
        # Disable autostart, aka delete the .desktop file present on the autostart folder
        for path in dest_paths:
            if path == '' or not Gio.File.new_for_path(path).query_exists():
                continue

            desktop_file = Gio.File.new_for_path(os.path.join(path, 'autostart', desktop_file_name))
            desktop_file.delete()
            return
