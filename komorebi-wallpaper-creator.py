#!/usr/bin/env python3

import argparse
import gi
import logging
import sys
import os

gi.require_versions({
    'Clutter': '1.0',
    'Gtk': '3.0'
})

from gi.repository import Gtk, Gio

import komorebi
from komorebi.wallpaper_creator.window import WallpaperWindow


def main_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version',
                        action='version',
                        help='show current version',
                        version=f'Version: {komorebi.__version__}\nMaintained by: Komorebi Team')
    parser.add_argument('-l', '--log',
                        type=str,
                        choices=['NORMAL', 'INFO', 'DEBUG'],
                        default='NORMAL',
                        help="set logging level for komorebi")
    return parser


def main():
    print(f'Welcome to {komorebi.__package_name__} Wallpaper Creator')

    parser = main_parser()
    args = parser.parse_args()

    log_level = logging.WARNING
    log_format = ''

    if args.log:
        if args.log == 'INFO':
            log_level = logging.INFO
            log_format = '[%(levelname)s]: %(message)s'
        elif args.log == 'DEBUG':
            log_level = logging.DEBUG
            log_format = '[%(levelname)s] (%(asctime)s): %(message)s'

    logging.basicConfig(format=log_format, level=log_level, datefmt='%H:%M:%S')

    # Load resources
    resource_path = os.path.join(komorebi.__package_datadir__, 'komorebi.gresource')
    resource = Gio.Resource.load(resource_path)
    Gio.resources_register(resource)

    Gtk.init(sys.argv)
    logging.debug('Gtk initialized')

    window = WallpaperWindow()

    main_settings = Gtk.Settings.get_default()
    main_settings.props.gtk_application_prefer_dark_theme = True
    main_settings.props.gtk_xft_antialias = 1
    main_settings.props.gtk_xft_rgba = "none"
    main_settings.props.gtk_xft_hintstyle = "slight"

    window.show_all()

    Gtk.main()


if __name__ == '__main__':
    main()
