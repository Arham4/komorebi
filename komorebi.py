#!/usr/bin/env python3

import argparse
import os
import gi
import signal
import sys
import logging

gi.require_versions({
    'Gtk': '3.0',
    'GObject': '2.0',
    'GtkClutter': '1.0',
    'Clutter': '1.0',
    'ClutterGst': '3.0',
    'Gdk': '3.0',
    'GdkPixbuf': '2.0',
    'Gst': '1.0',
    'WebKit2': '4.0',
})

from gi.repository import Gio, Gtk, GtkClutter, Gdk, Gst, Clutter

from komorebi.preferences_window import PreferencesWindow
from komorebi.settings import ConfigKeys, Settings
import komorebi.utilities

from komorebi.screen import Screen


def check_desktop_compatible():
    return not(os.environ.get('XDG_SESSION_TYPE') == 'wayland' or os.environ.get('WAYLAND_DISPLAY'))


def main_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version',
                        action='version',
                        help='show current version',
                        version=f'Version: {komorebi.__version__}\nMaintained by: Komorebi Team')
    parser.add_argument('-ss', '--single-screen',
                        action='store_true',
                        help='force komorebi to run only on the main screen')
    parser.add_argument('-l', '--log',
                        type=str,
                        choices=['NORMAL', 'INFO', 'DEBUG'],
                        default='NORMAL',
                        help="set logging level for komorebi")
    return parser


def _on_destroy(*args):
    logging.info("Quitting...")
    Clutter.main_quit()


def main():
    print(f'Welcome to {komorebi.__package_name__}')

    # Handle Ctrl-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Parse the arguments
    parser = main_parser()
    args = parser.parse_args()

    # Setup logger
    log_level = logging.WARNING
    log_format = '[%(levelname)s]: %(message)s'

    if args.log:
        if args.log == 'INFO':
            log_level = logging.INFO
        elif args.log == 'DEBUG':
            log_level = logging.DEBUG
            log_format = '[%(levelname)s] (%(asctime)s): %(message)s'

    logging.basicConfig(format=log_format, level=log_level, datefmt='%H:%M:%S')

    # Ensure we are not on Wayland
    if not check_desktop_compatible():
        logging.error('Wayland detected. Not supported (yet) :(')
        logging.info('Contribute to Komorebi and add the support! <3')
        return

    # Initialize backends
    GtkClutter.init(sys.argv)
    logging.debug("GtkClutter initialized")

    Settings.load_settings()
    logging.debug("Configuration file read")

    logging.info('loading Gst')
    Gst.init(sys.argv)
    logging.debug('Gst initialized')

    # Load resources
    resource_path = os.path.join(komorebi.__package_datadir__, 'komorebi.gresource')
    resource = Gio.Resource.load(resource_path)
    Gio.resources_register(resource)

    display = Gdk.Display.get_default()
    if args.single_screen:
        monitor_count = 1
    else:
        monitor_count = display.get_n_monitors()
    logging.info(f"Monitor Count - {monitor_count}")

    komorebi.utilities.init_clipboard(display)

    # Initialize Screen's
    screen_list = []
    for i in range(monitor_count):
        screen_list.append(Screen(i))

    # Setup some GTK properties
    main_settings = Gtk.Settings.get_default()
    main_settings.props.gtk_application_prefer_dark_theme = True
    main_settings.props.gtk_xft_antialias = 1
    main_settings.props.gtk_xft_rgba = "none"
    main_settings.props.gtk_xft_hintstyle = "slight"

    # Setup preferences window
    def _on_settings_changed(_, setting_key):
        logging.debug("Setting " + str(setting_key) + " changed!")
        if setting_key == ConfigKeys.WALLPAPER_NAME:
            for screen in screen_list:
                screen.load_wallpaper(Settings.wallpaper_name)
        elif setting_key == ConfigKeys.AUTOSTART:
            komorebi.utilities.toggle_autostart()
        else:
            for screen in screen_list:
                screen.on_settings_changed(setting_key)
        return True

    prefs_window = PreferencesWindow()
    prefs_window.connect('settings-changed', _on_settings_changed)

    # Setup screens
    def _on_settings_request_event(_, wallpaper_tab):
        prefs_window.show(wallpaper_tab)
        return True

    for screen in screen_list:
        screen.connect("destroy", _on_destroy)
        screen.load_wallpaper(Settings.wallpaper_name)
        screen.fade_in()
        screen.connect('settings_requested', _on_settings_request_event)

    # Start Clutter backend
    logging.debug("Starting Clutter backend...")
    Clutter.main()


if __name__ == '__main__':
    main()
