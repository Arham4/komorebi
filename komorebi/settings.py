import logging
import os
from enum import Enum

from gi.repository import Gio, GLib

import komorebi


class ConfigKeys(Enum):
    WALLPAPER_NAME = 'WallpaperName'
    TIME_TWENTY_FOUR = 'TimeTwentyFour'
    AUTOSTART = 'Autostart'
    SHOW_DESKTOP = 'ShowDesktopIcons'
    ENABLE_VIDEO = 'EnableVideoWallpapers'
    MUTE_PLAYBACK = 'MutePlayback'
    PAUSE_PLAYBACK = 'PausePlayback'


class Settings:
    key_file_group = 'KomorebiProperties'

    # Settings
    wallpaper_name = 'foggy_sunny_mountain'
    time_twenty_four = True
    show_desktop_icons = True
    enable_video_wallpapers = True
    mute_playback = False
    pause_playback = True
    autostart = False

    # Internal settings files
    _config_key_file = None
    _config_file = None

    def _str2bool(string):
        if type(string) == bool:
            return string
        elif type(string) == str:
            return string.lower() == 'true'

    def _optional(key, default):
        try:
            return Settings._config_key_file.get_value(Settings.key_file_group, key)
        except GLib.Error as err:
            if err.code == GLib.KeyFileError.KEY_NOT_FOUND:
                logging.warning(f'Key not found for property "{key}", using default value "{default}"')
                return default

    def load_settings():
        logging.info("Loading configuration...")
        logging.debug(f'Config dir is "{Settings.get_config_dir()}"')

        config_path = os.path.join(Settings.get_config_dir(), 'komorebi.prop')
        Settings._config_file = Gio.File.new_for_path(config_path)
        Settings._config_key_file = GLib.KeyFile()

        # If the file doesn't exist, then perform first setup
        if not Settings._config_file.query_exists():
            Settings.bootstrap_config_path()
            if not Settings._config_file.query_exists():
                logging.info("No configuration file found. Creating a new one...")
                Settings.save_configuration_file()
                return

        logging.debug("Reading config file...")

        Settings._config_key_file.load_from_file(config_path, GLib.KeyFileFlags.NONE)

        if not Settings._config_key_file.has_group(Settings.key_file_group):
            logging.warning('Invalid configuration file found, Fixing...')
            Settings.save_configuration_file()

        # Required keys
        Settings.wallpaper_name = str(Settings._optional(ConfigKeys.WALLPAPER_NAME.value, 'foggy_sunny_mountain'))
        Settings.time_twenty_four = Settings._str2bool(Settings._optional(ConfigKeys.TIME_TWENTY_FOUR.value, True))
        Settings.show_desktop_icons = Settings._str2bool(Settings._optional(ConfigKeys.SHOW_DESKTOP.value, True))
        Settings.enable_video_wallpapers = Settings._str2bool(Settings._optional(ConfigKeys.ENABLE_VIDEO.value, True))
        Settings.mute_playback = Settings._str2bool(Settings._optional(ConfigKeys.MUTE_PLAYBACK.value, False))
        Settings.pause_playback = Settings._str2bool(Settings._optional(ConfigKeys.PAUSE_PLAYBACK.value, True))
        Settings.autostart = Settings._str2bool(Settings._optional(ConfigKeys.AUTOSTART.value, False))

        Settings.fix_conflicts()

    def fix_conflicts():
        # Disable/Enabled nautilus to fix bug when clicking on another monitor
        Gio.Settings.new('org.gnome.desktop.background').set_boolean('show-desktop-icons', False)

        # Check if we have nemo installed
        settingsSchemaSource = Gio.SettingsSchemaSource.new_from_directory('/usr/share/glib-2.0/schemas', None, False)
        settingsSchema = settingsSchemaSource.lookup('org.nemo.desktop', False)

        if settingsSchema is not None:
            # Disable/Enable Nemo's desktop icons
            Gio.Settings.new('org.nemo.desktop').set_boolean('show-desktop-icons', False)

    def bootstrap_config_path():
        '''
        Bootstraps the base configuration path if it doesn't exist, and detects older versions of this app
        '''
        config_path = Gio.File.new_for_path(os.path.join(Settings.get_config_dir(), 'wallpapers'))
        if not config_path.query_exists():
            config_path.make_directory_with_parents()

        old_config_file = Gio.File.new_for_path(os.path.join(GLib.get_home_dir(), '.Komorebi.prop'))
        if old_config_file.query_exists():
            logging.info('Found config file from old version, converting it to new one...')
            destination_path = Gio.File.new_for_path(os.path.join(Settings.get_config_dir(), 'komorebi.prop'))
            old_config_file.copy(destination_path, Gio.FileCopyFlags.NONE)

        Settings._config_file = Gio.File.new_for_path(os.path.join(Settings.get_config_dir(), 'komorebi.prop'))

    def save_configuration_file():
        for group in Settings._config_key_file.get_groups()[0]:
            if group != Settings.key_file_group:
                Settings._config_key_file.remove_group(group)

        # Sets base properties
        Settings._config_key_file.set_string(Settings.key_file_group, ConfigKeys.WALLPAPER_NAME.value, Settings.wallpaper_name)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.TIME_TWENTY_FOUR.value, Settings.time_twenty_four)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.SHOW_DESKTOP.value, Settings.show_desktop_icons)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.ENABLE_VIDEO.value, Settings.enable_video_wallpapers)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.MUTE_PLAYBACK.value, Settings.mute_playback)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.PAUSE_PLAYBACK.value, Settings.pause_playback)
        Settings._config_key_file.set_boolean(Settings.key_file_group, ConfigKeys.AUTOSTART.value, Settings.autostart)

        # Delete the file
        if Settings._config_file.query_exists():
            Settings._config_file.delete()

        # Save the key file
        stream = Gio.DataOutputStream.new(Settings._config_file.create(Gio.FileCreateFlags.NONE))
        stream.put_string(Settings._config_key_file.to_data()[0])
        stream.close()

    def get_config_dir():
        '''
        Returns the path for hosting configuration files and wallpapers
        '''
        paths = [
            os.environ.get('XDG_CONFIG_PATH', ''),
            os.path.join(GLib.get_home_dir(), '.config'),
            GLib.get_home_dir()
        ]

        for path in paths:
            if path != '':
                return os.path.join(path, 'komorebi')

    def get_wallpaper_paths():
        '''
        Returns the list of paths to search for wallpapers
        '''
        return [
            os.path.join(Settings.get_config_dir(), 'wallpapers'),
            komorebi.__package_datadir__
        ]
