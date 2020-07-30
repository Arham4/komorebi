import logging
import os

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk, Clutter

import komorebi.utilities
from komorebi.settings import ConfigKeys, Settings


class Thumbnail(Gtk.EventBox):
    name = ''
    overlay = None
    thumbnail_image = None
    border_image = None
    revealer = None

    def __init__(self, path, name):
        Gtk.EventBox.__init__(self)

        self.name = name
        self.overlay = Gtk.Overlay()
        self.thumbnail_image = Gtk.Image(pixbuf=GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                         os.path.join(path, self.name, 'wallpaper.jpg'), 150, 100, False
                                         ))
        self.border_image = Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/thumbnail_border.svg')
        self.revealer = Gtk.Revealer()

        self.revealer.set_reveal_child(False)
        self.revealer.add(self.border_image)

        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.revealer.set_transition_duration(200)
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)

        self.overlay.add(self.thumbnail_image)
        self.overlay.add_overlay(self.revealer)
        self.add(self.overlay)

    def set_border(self, visible):
        self.revealer.set_reveal_child(visible)


class WallpapersSelector(Gtk.ScrolledWindow):
    # Komorebi can't find wallpapers if this variable doesn't have a trailing slash. Hacky, but it works. Fix later on.
    path = f'{komorebi.__package_datadir__}/'

    grid = None
    row = None
    column = None

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        logging.debug('Loading WallpapersSelector..')

        # Setup widgets and properties
        self.grid = Gtk.Grid()
        self.row = self.column = 0

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        self.props.margin = 20

        self.grid.set_halign(Gtk.Align.CENTER)
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(20)

        self.add(self.grid)

        logging.debug('Loaded WallpapersSelector...')

    def get_wallpapers(self):
        # Internal callback for thumbnail selection
        def _on_thumb_button_press_event(self, e, wallpaper_selector):
            if e.button == Gdk.BUTTON_PRIMARY:
                # Make the selection on wallpaper_Selector
                for thumb in wallpaper_selector.grid.get_children():
                    thumb.set_border(self.name == thumb.name)

                wallpaper_selector.emit('wallpaper_changed', self.name)
            return True

        self.clear_grid()

        # Fetch existing wallpapers
        for path in Settings.get_wallpaper_paths():
            wallpapers_folder = Gio.File.new_for_path(path)
            try:
                enumerator = wallpapers_folder.enumerate_children('standard::*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)
                info = enumerator.next_file()

                while info is not None:
                    name = info.get_name()
                    full_path = os.path.join(path, name)

                    if (Gio.File.new_for_path(os.path.join(full_path, 'wallpaper.jpg')).query_exists()
                            and Gio.File.new_for_path(os.path.join(full_path, 'config')).query_exists()):
                        # Wallpaper detected
                        logging.debug(f"Loading wallpaper thumbnail \"{name}\"")

                        thumb = Thumbnail(path, name)
                        self.add_thumbnail(thumb)
                        if name == Settings.wallpaper_name:
                            thumb.set_border(True)
                        thumb.connect('button_press_event', _on_thumb_button_press_event, self)
                    else:
                        logging.warning(f'found an invalid wallpaper with name: {name}')

                    info = enumerator.next_file()
            except GLib.Error:
                logging.warning(f"could not read directory '{path}'")

    def add_thumbnail(self, thumbnail):
        self.grid.attach(thumbnail, self.column, self.row, 1, 1)

        if self.column >= 3:
            self.row += 1
            self.column = 0
        else:
            self.column += 1

        thumbnail.show_all()

    def clear_grid(self):
        for widget in self.grid.get_children():
            self.grid.remove(widget)

        self.row = self.column = 0

    @GObject.Signal(arg_types=(str,))
    def wallpaper_changed(self, wallpaper_name):
        pass


class PreferencesWindow(Gtk.Window):
    header_bar = None

    hide_button = None
    quit_button = None

    # Contains two page (Preferences and Wallpapers)
    notebook = None

    # Contains preferences page widgets
    preferences_page = None

    about_grid = None

    title_box = None
    title_label = None
    about_label = None

    twenty_four_hours_button = None
    enable_autostart_button = None
    show_desktop_icons_button = None
    enable_video_wallpapers_button = None
    mute_playback_button = None
    pause_playback_button = None

    bottom_preferences_box = None

    donate_button = None
    report_button = None

    # Contains wallpapers page widgets
    wallpapers_page = None

    info_bar = None

    wallpapers_selector = None

    bottom_wallpapers_box = None

    current_wallpaper_label = None

    # Triggered when pointer leaves window
    can_destroy = None

    # Add some style
    notebook_css = """
        *{
            background: none;
            background-color: rgba(0, 0, 0, 0.60);
            box-shadow: none;
            color: white;
            border-width: 0;
        }
        .notebook.header {
            background-color: rgb(0,0,0);
        }
        .notebook notebook:focus tab {
            background: none;
            border-width: 0;
            border-radius: 0px;
            border-color: transparent;
            border-image-width: 0;
            border-image: none;
            background-color: red;
        }
        """

    header_css = """
        *{
            background: rgba(0, 0, 0, 0.7);
            background-color: rgb(0, 0, 0);
            box-shadow: none;
            color: white;
            border-width: 0px;
            box-shadow: none;
            border-image: none;
            border: none;
        }
        """

    info_bar_css = """
        *{
            background: #f44336;
            background-color: #f44336;
            box-shadow: none;
            color: white;
            border-width: 0px;
            box-shadow: none;
            border-image: none;
            border: none;
        }
        """

    def __init__(self):
        Gtk.Window.__init__(self)
        logging.debug('Loading PreferencesWindow...')

        # Initialize widgets
        self.header_bar = Gtk.HeaderBar()
        self.hide_button = Gtk.Button(label='Hide', margin_top=6, margin_start=6, halign=Gtk.Align.START)
        self.quit_button = Gtk.Button(label='Quit Komorebi', margin_top=6, margin_start=6)

        self.notebook = Gtk.Notebook(hexpand=True, vexpand=True)
        self.preferences_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin_top=20,
                                        margin_bottom=10, margin_left=20, margin_right=20, halign=Gtk.Align.CENTER)
        self.about_grid = Gtk.Grid(halign=Gtk.Align.CENTER, margin_bottom=30, column_spacing=0, row_spacing=0)

        self.title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin_top=15,
                                 margin_start=10, halign=Gtk.Align.START)
        self.title_label = Gtk.Label()
        self.about_label = Gtk.Label()

        self.twenty_four_hours_button = Gtk.CheckButton(label='Use 24-hour time')
        self.enable_autostart_button = Gtk.CheckButton(label='Launch Komorebi on system startup')
        self.show_desktop_icons_button = Gtk.CheckButton(label='Show desktop icons')
        self.enable_video_wallpapers_button = Gtk.CheckButton(label='Enable Video Wallpaper')
        self.mute_playback_button = Gtk.CheckButton(label='Mute Video playback')
        self.pause_playback_button = Gtk.CheckButton(label='Pause Video playback on un-focus')

        self.bottom_preferences_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_top=10)
        self.donate_button = Gtk.Button(label='Donate', valign=Gtk.Align.CENTER)
        self.report_button = Gtk.Button(label='Report an issue', valign=Gtk.Align.CENTER)

        self.wallpapers_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.info_bar = Gtk.InfoBar(message_type=Gtk.MessageType.WARNING, show_close_button=False)
        self.wallpapers_selector = WallpapersSelector()
        self.bottom_wallpapers_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.current_wallpaper_label = Gtk.Label(selectable=True)

        self.can_destroy = False

        # Configure the window
        self.set_size_request(760, 500)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_titlebar(self.header_bar)
        komorebi.utilities.apply_css([self.notebook], self.notebook_css)
        komorebi.utilities.apply_css([self.info_bar], self.info_bar_css)
        komorebi.utilities.apply_css([self.header_bar, self.hide_button, self.quit_button, self.donate_button,
                                     self.report_button], self.header_css)
        komorebi.utilities.apply_alpha([self])

        # Setup widgets
        self.title_label.set_markup("<span font='Lato Light 30px' color='white'>Komorebi</span>")
        self.about_label.set_markup("<span font='Lato Light 15px' color='white'>by Komorebi Team</span>")

        self.twenty_four_hours_button.set_active(Settings.time_twenty_four)
        self.enable_autostart_button.set_active(Settings.autostart)
        self.show_desktop_icons_button.set_active(Settings.show_desktop_icons)
        self.enable_video_wallpapers_button.set_active(Settings.enable_video_wallpapers)
        self.mute_playback_button.set_active(Settings.mute_playback)
        self.pause_playback_button.set_active(Settings.pause_playback)

        self.set_wallpaper_name_label()

        # Properties
        self.bottom_wallpapers_box.props.margin = 25
        self.bottom_wallpapers_box.set_margin_top(10)

        self.setup_signals()

        # Add widgets
        self.header_bar.add(self.hide_button)
        self.header_bar.pack_end(self.quit_button)

        self.title_box.add(self.title_label)
        self.title_box.add(self.about_label)

        self.about_grid.attach(Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/komorebi.svg'), 0, 0, 1, 1)
        self.about_grid.attach(self.title_box, 1, 0, 1, 1)

        self.bottom_preferences_box.pack_start(self.donate_button, True, True, 0)
        self.bottom_preferences_box.pack_end(self.report_button, True, True, 0)

        self.preferences_page.add(self.about_grid)
        self.preferences_page.add(self.twenty_four_hours_button)
        self.preferences_page.add(self.enable_autostart_button)
        self.preferences_page.add(self.show_desktop_icons_button)
        self.preferences_page.add(self.enable_video_wallpapers_button)
        self.preferences_page.add(self.mute_playback_button)
        self.preferences_page.add(self.pause_playback_button)
        self.preferences_page.pack_end(self.bottom_preferences_box, True, True, 0)

        self.bottom_wallpapers_box.add(Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/info.svg'))
        self.bottom_wallpapers_box.add(self.current_wallpaper_label)

        if not komorebi.utilities.can_play_videos():
            self.info_bar.get_content_area().add(Gtk.Label(label="gstreamer1.0-libav is missing. "
                                                                 "You won't be able to set video wallpapers without it."))
            self.wallpapers_page.add(self.info_bar)

        self.wallpapers_page.add(self.wallpapers_selector)
        self.wallpapers_page.add(self.bottom_wallpapers_box)

        self.notebook.append_page(self.wallpapers_page, Gtk.Label(label='Wallpapers'))
        self.notebook.append_page(self.preferences_page, Gtk.Label(label='Preferences'))

        self.notebook.child_set_property(self.preferences_page, 'tab-expand', True)
        self.notebook.child_set_property(self.wallpapers_page, 'tab-expand', True)

        self.add(self.notebook)

        # Start hidden; this is created at initialization, not on request
        self.hide()

        logging.debug("Loaded PreferencesWindow")

    # Overrides
    def show(self, wallpaper_menu):
        self.wallpapers_selector.get_wallpapers()
        self.show_all()
        self.notebook.set_current_page(0 if wallpaper_menu else 1)
        self.grab_focus()

    # Signals
    def setup_signals(self):
        def _on_hide_button_released(*args):
            self.hide()

        def _on_quit_button_released(*args):
            logging.info('Quitting Komorebi. Good bye :)')
            Clutter.main_quit()

        def _on_donate_button_released(*args):
            logging.info('Thank you <3')
            Gio.AppInfo.launch_default_for_uri('https://goo.gl/Yr1RQe', None)   # Thank you <3
            self.hide()

        def _on_report_button_released(*args):
            logging.info('Thank you <3')
            Gio.AppInfo.launch_default_for_uri('https://goo.gl/aaJgN7', None)   # Thank you <3
            self.hide()

        def _on_twenty_four_hours_button_toggled(_, self):
            Settings.time_twenty_four = self.twenty_four_hours_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.TIME_TWENTY_FOUR)

        def _on_enable_autostart_button_toggled(_, self):
            Settings.autostart = self.enable_autostart_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.AUTOSTART)

        def _on_show_desktop_icons_button_toggled(_, self):
            Settings.show_desktop_icons = self.show_desktop_icons_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.SHOW_DESKTOP)

        def _on_enable_video_wallpapers_button_toggled(_, self):
            Settings.enable_video_wallpapers = self.enable_video_wallpapers_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.ENABLE_VIDEO)

        def _on_mute_playback_button_toggled(_, self):
            Settings.mute_playback = self.mute_playback_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.MUTE_PLAYBACK)

        def _on_pause_playback_button_toggled(_, self):
            Settings.pause_playback = self.pause_playback_button.props.active
            Settings.save_configuration_file()
            self.emit('settings-changed', ConfigKeys.PAUSE_PLAYBACK)

        def _on_wallpaper_changed(_, wallpaper_name, self):
            Settings.wallpaper_name = wallpaper_name
            Settings.save_configuration_file()
            self.set_wallpaper_name_label()
            self.emit('settings-changed', ConfigKeys.WALLPAPER_NAME)

        self.hide_button.connect('released', _on_hide_button_released)
        self.quit_button.connect('released', _on_quit_button_released)
        self.donate_button.connect('released', _on_donate_button_released)
        self.report_button.connect('released', _on_report_button_released)
        self.twenty_four_hours_button.connect('toggled', _on_twenty_four_hours_button_toggled, self)
        self.enable_autostart_button.connect('toggled', _on_enable_autostart_button_toggled, self)
        self.show_desktop_icons_button.connect('toggled', _on_show_desktop_icons_button_toggled, self)
        self.enable_video_wallpapers_button.connect('toggled', _on_enable_video_wallpapers_button_toggled, self)
        self.mute_playback_button.connect('toggled', _on_mute_playback_button_toggled, self)
        self.pause_playback_button.connect('toggled', _on_pause_playback_button_toggled, self)
        self.wallpapers_selector.connect('wallpaper_changed', _on_wallpaper_changed, self)

    # Changes the wallpaper name label
    def set_wallpaper_name_label(self):
        pretty_name = komorebi.utilities.beautify_wallpaper_name(Settings.wallpaper_name)
        self.current_wallpaper_label.set_markup(f"<span font='Lato Light 15px' color='#bebebee6'>{pretty_name}</span>")

    @GObject.Signal(arg_types=(GObject.TYPE_PYOBJECT,))
    def settings_changed(self, config_key):
        pass
