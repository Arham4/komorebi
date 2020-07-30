from komorebi.settings import ConfigKeys
import logging

from gi.repository import Clutter, Cogl, Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

from komorebi.bubblemenu.item import BubbleMenuItem, ViewMode
from komorebi.overlays.base import Overlay

from komorebi.settings import Settings
import komorebi.utilities


class RowLabel(Gtk.EventBox):
    # Switch between mainBox and 'Copied' label
    stack = None

    # Contains both labels
    main_box = None

    name_label = None
    value_label = None
    copied_label = None

    css = """*, *:disabled {
            transition: 150ms ease-in;
            background-color: @transparent;
            background-image: none;
            border: none;
            border-color: @transparent;
            box-shadow: inset 1px 2px rgba(0,0,0,0);
            border-radius: 3px;
            color: white;
            text-shadow:0px 2px 3px rgba(0,0,0,0.9);
            -gtk-icon-shadow: 0px 1px 4px rgba(0, 0, 0, 0.4);
        }
        .:hover {
            transition: 50ms ease-out;
            border-style: outset;
            background-color: rgba(0, 0, 0, 0.9);
        }"""

    def __init__(self, name_str):
        Gtk.EventBox.__init__(self)

        self.stack = Gtk.Stack()
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.name_label = Gtk.Label(label=name_str)
        self.value_label = Gtk.Label(label='Value')
        self.copied_label = Gtk.Label(label=name_str + ' copied')

        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_left(10)
        self.set_margin_right(10)
        self.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
        komorebi.utilities.apply_css([self], self.css)

        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(300)

        self.value_label.set_line_wrap(True)
        self.value_label.set_max_width_chars(19)
        self.value_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        self.name_label.set_halign(Gtk.Align.START)
        self.value_label.set_halign(Gtk.Align.END)

        # Signals
        self.setup_signals()

        self.main_box.pack_start(self.name_label, True, True, 0)
        self.main_box.pack_end(self.value_label, True, True, 0)

        self.stack.add_named(self.main_box, 'main_box')
        self.stack.add_named(self.copied_label, 'copied_label')

        self.stack.set_visible_child(self.main_box)

        self.add(self.stack)

    def setup_signals(self):
        def _on_button_press_event(self, e):
            # Set the clipboard's value
            komorebi.utilities.clipboard.set_text(self.value_label.get_label(), -1)
            self.stack.set_visible_child(self.copied_label)

            def _on_timeout():
                self.stack.set_visible_child(self.main_box)
                return False

            GLib.timeout_add(600, _on_timeout)
            return False

        self.connect('button_press_event', _on_button_press_event)

    def set_value(self, value_str):
        if value_str:
            self.value_label.set_label(value_str)
            self.value_label.set_tooltip_text(value_str)


class ResponsiveGrid(Overlay):
    # Limit of items per column
    items_limit = 8

    # Layouts (HORIZONTAL/VERTICAL)
    horizontal_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.HORIZONTAL, spacing=50)
    vertical_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.VERTICAL, spacing=30)

    def __init__(self, screen):
        Overlay.__init__(self)

        self.set_size(screen.width, screen.height)

        self.set_layout_manager(self.horizontal_layout)
        self.set_y_align(Clutter.ActorAlign.START)

    def append(self, item):
        last_child = self.get_last_child()
        if last_child is not None:
            if last_child.get_n_children() < self.items_limit:
                last_child.add_child(item)
                return

        # Create a new column and add the new item to it
        column_actor = Clutter.Actor(layout_manager=self.vertical_layout, y_align=Clutter.ActorAlign.START, y_expand=True)

        column_actor.add_child(item)
        self.add_child(column_actor)

    def clear_icons(self):
        for child in self.get_children():
            child.destroy_all_children()
            self.remove_child(child)


class Icon(Clutter.Actor):
    # Title of the file
    title_name = ''

    box_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.VERTICAL)

    icon_actor = None
    icon_image = None
    title_text = None

    # Ability to drag
    drag_action = None

    def __init__(self, name, pixbuf, icon_size):
        Clutter.Actor.__init__(self)

        self.title_name = name

        self.main_actor = Clutter.Actor()
        self.icon_actor = Clutter.Actor()
        self.icon_image = Clutter.Image()
        self.title_text = Clutter.Text()
        self.drag_action = Clutter.DragAction()

        # Setup widgets
        self.icon_image.set_data(pixbuf.get_pixels(),
                                 Cogl.PixelFormat.RGBA_8888 if pixbuf.get_has_alpha() else Cogl.PixelFormat.RGB_888,
                                 icon_size, icon_size, pixbuf.get_rowstride())
        self.title_text.set_markup(f"<span color='white' font='Lato Bold 11'>{self.title_name}</span>")

        self.set_layout_manager(self.box_layout)
        self.set_reactive(True)
        self.set_height(83)
        self.set_opacity(0)

        self.set_pivot_point(0.5, 0.5)

        self.icon_actor.set_size(icon_size, icon_size)

        self.title_text.set_line_wrap(True)
        self.title_text.set_max_length(10)
        self.title_text.set_ellipsize(Pango.EllipsizeMode.END)

        self.setup_signals()

        # Add widgets
        self.icon_actor.add_action(self.drag_action)
        self.icon_actor.set_content(self.icon_image)
        self.add_child(self.icon_actor)
        self.add_child(self.title_text)

    def setup_signals(self):
        def _on_button_press_event(self, event):
            if event.button != Gdk.BUTTON_SECONDARY:
                self.scaled_scale()
            return False

        def _on_button_release_event(self, event):
            self.save_easing_state()
            self.set_easing_duration(90)
            self.set_scale(1.0, 1.0)
            self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
            self.restore_easing_state()

        self.connect('button_press_event', _on_button_press_event)
        self.connect('button_release_event', _on_button_release_event)

    def scaled_scale(self):
        self.save_easing_state()
        self.set_easing_duration(90)
        self.set_scale(0.9, 0.9)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    def trash(self):
        self.save_easing_state()
        self.set_easing_duration(90)
        self.set_scale(0.9, 0.9)
        self.set_opacity(0)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    def dim_icon(self):
        self.save_easing_state()
        self.set_easing_duration(400)
        self.set_opacity(100)
        self.title_text.set_opacity(100)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    def un_dim_icon(self, with_scale=False):
        if with_scale:
            self.set_scale(0.5, 0.5)

        self.save_easing_state()
        self.set_easing_duration(400)
        self.set_opacity(255)
        if with_scale:
            self.set_scale(1.0, 1.0)

        self.title_text.set_opacity(255)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()


class TrashIcon(Icon):
    def __init__(self, icon_size):
        Icon.__init__(self, 'Trash', komorebi.utilities.get_icon_from('user-trash', icon_size), icon_size)

        # Signals
        self.setup_trash_signals()

    def setup_trash_signals(self):
        def _on_button_trash_release_event(_, event):
            if event.button == Gdk.BUTTON_PRIMARY:
                Gio.AppInfo.launch_default_for_uri('trash://', None)
            return False

        self.connect('button_release_event', _on_button_trash_release_event)


class FolderIcon(Icon):
    # Path from file to later be opened
    path = ''

    def __init__(self, name, pixbuf, path, icon_size):
        Icon.__init__(self, name, pixbuf, icon_size)

        self.path = path

        self.setup_folder_signals()

    def setup_folder_signals(self):
        def _on_button_folder_release_event(_, event):
            if event.button == Gdk.BUTTON_PRIMARY:
                Gio.AppInfo.launch_default_for_uri(f'file://{self.path}', None)
            return False

        self.connect('button_release_event', _on_button_folder_release_event)


class ApplicationIcon(Icon):
    # Path from application to later be opened
    path = None
    command = None

    def __init__(self, name, pixbuf, path, command, icon_size):
        Icon.__init__(self, name, pixbuf, icon_size)

        self.path = path
        self.command = command

        self.setup_application_signals()

    def setup_application_signals(self):
        def _on_button_application_release_event(_, event):
            if event.button == Gdk.BUTTON_PRIMARY:
                Gio.AppInfo.create_from_commandline(self.command, None, Gio.AppInfoCreateFlags.NONE).launch(None, None)
            return False

        self.connect('button_release_event', _on_button_application_release_event)


class InfoWindow(Gtk.Window):
    # Box containing everything
    main_box = None

    # Box contains close button (acts like HeaderBar)
    header_bar = None

    # Box contains title label, and size
    top_box = None

    # Close/Hide button
    close_button = None

    # File/Directory title
    title_label = None

    # File/Directory size
    size_label = None

    # Separator
    separator = None

    # Box more file info and properties
    file_info_box = None

    # Location
    location_label = None

    # Type
    type_label = None

    # Accessed
    accessed_label = None

    # Modified
    modified_label = None

    # Owner
    owner_label = None

    header_bar_css = """*{
        background-color: rgba(25,25,25,0.7);
        border-width: 0px;
        box-shadow: none;
        border-top-left-radius: 0.6em;
        border-top-right-radius: 0.6em;
        border-color: @transparent;
        }"""
    window_css = """*{
        background-color: rgba(25,25,25,0.7);
        border-width: 0px;
        box-shadow: none;
        border-bottom-left-radius: 0.6em;
        border-bottom-right-radius: 0.6em;
        color: white;
        }"""
    separator_css = """*{
        color: rgba(51,51,51,0.6);
        }"""

    def __init__(self):
        Gtk.Window.__init__(self)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.close_button = Gtk.Button()
        self.title_label = Gtk.Label(label='No name')
        self.size_label = Gtk.Label(label='Size unknown')
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.file_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.location_label = RowLabel('Location')
        self.type_label = RowLabel('Type')
        self.accessed_label = RowLabel('Accessed')
        self.modified_label = RowLabel('Modified')
        self.owner_label = RowLabel('Owner')

        # Configure window
        self.set_size_request(340, 390)
        self.set_resizable(False)
        self.set_titlebar(self.header_bar)
        komorebi.utilities.apply_alpha(self)
        komorebi.utilities.apply_css([self], self.window_css)

        # Configure widgets
        komorebi.utilities.apply_css([self.header_bar], self.header_bar_css)
        self.close_button.set_halign(Gtk.Align.START)

        self.title_label.set_halign(Gtk.Align.CENTER)
        self.title_label.set_line_wrap(True)
        self.title_label.set_max_width_chars(19)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.title_label.set_selectable(True)

        self.separator.set_margin_top(10)
        self.separator.set_margin_bottom(10)
        komorebi.utilities.apply_css([self.separator], self.separator_css)

        self.file_info_box.set_margin_top(20)
        self.file_info_box.set_margin_bottom(20)
        self.file_info_box.set_margin_left(20)
        self.file_info_box.set_margin_right(20)

        # Signals
        self.signals_setup()

        # Add widgets
        self.close_button.add(Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/close_btn.svg'))
        self.header_bar.pack_start(self.close_button, False, False, 0)

        self.top_box.add(self.title_label)
        self.top_box.add(self.size_label)

        self.file_info_box.add(self.location_label)
        self.file_info_box.add(self.type_label)
        self.file_info_box.add(self.accessed_label)
        self.file_info_box.add(self.modified_label)
        self.file_info_box.add(self.owner_label)

        self.main_box.add(self.top_box)
        self.main_box.add(self.separator)
        self.main_box.add(self.file_info_box)

        self.add(self.main_box)
        self.close_button.grab_focus()

    def signals_setup(self):
        def _on_close_button_button_press_event(*args):
            self.hide()
            return False

        self.close_button.connect('button_press_event', _on_close_button_button_press_event)

    # Set window information
    def set_info_from_path(self, path):
        file = Gio.File.new_for_path(path)
        file_info = file.query_info(f'{Gio.FILE_ATTRIBUTE_STANDARD_SIZE},{Gio.FILE_ATTRIBUTE_STANDARD_TYPE},'
                                    f'{Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE},{Gio.FILE_ATTRIBUTE_TIME_ACCESS},'
                                    f'{Gio.FILE_ATTRIBUTE_TIME_CHANGED},{Gio.FILE_ATTRIBUTE_OWNER_USER}',
                                    Gio.FileQueryInfoFlags.NONE)

        accessed_time = file_info.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_ACCESS)
        modified_time = file_info.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_CHANGED)
        owner = file_info.get_attribute_string(Gio.FILE_ATTRIBUTE_OWNER_USER)

        self.title_label.set_markup(f"<span font='Lato 13'>{file.get_basename()}</span>")
        self.size_label.set_markup(f"<span font='Lato 10'>{GLib.format_size(file_info.get_size())}</span>")

        self.location_label.set_value(path)
        self.type_label.set_value(file_info.get_attribute_string(Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE))

        format_str = '%m/%d/%Y %H:%M' if Settings.time_twenty_four else '%m/%d/%Y %l:%M %p'

        self.accessed_label.set_value(GLib.DateTime.new_from_unix_utc(accessed_time).to_local().format(format_str))
        self.modified_label.set_value(GLib.DateTime.new_from_unix_utc(modified_time).to_local().format(format_str))
        self.owner_label.set_value(owner)


class Desktop(ResponsiveGrid):
    # Screen info
    screen_height = None

    # Menu options
    new_folder_item = None
    copy_path_item = None
    paste_item = None
    move_to_trash_item = None
    get_info_item = None

    # Utils
    icon_size = None
    desktop_path = None

    info_window = None
    file_monitor = None
    file_monitor_signal = None
    icons_list = None
    selected_icon = None

    def __init__(self, screen):
        ResponsiveGrid.__init__(self, screen)
        logging.debug('Loading Desktop...')

        self.screen_height = screen.height
        self.set_size(screen.width, self.screen_height)

        self.info_window = InfoWindow()
        self.icons_list = []

        self.set_margin_top(60)
        self.set_margin_left(120)
        self.set_y_expand(True)
        self.icon_size = 64
        self.desktop_path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)

        self.monitor_changes()
        self.get_desktops()

        logging.debug('Loaded Desktop')

    def on_unload(self):
        logging.debug('Unloading Desktop...')
        self.new_folder_item.destroy()
        self.copy_path_item.destroy()
        self.paste_item.destroy()
        self.move_to_trash_item.destroy()
        self.get_info_item.destroy()

        if self.file_monitor_signal:
            self.file_monitor.disconnect(self.file_monitor_signal)

    def __del__(self):
        logging.debug('Unloaded Desktop')

    def on_settings_changed(self, setting_key):
        if (setting_key == ConfigKeys.SHOW_DESKTOP
                and not Settings.show_desktop_icons):
            self.on_unload()
            return True
        return False

    # Internal callbacks
    def _on_create_new_folder(self, item, e):
        untitled_folder = Gio.File.new_for_path(self.get_untitled_folder_name())
        untitled_folder.make_directory_async(GLib.PRIORITY_DEFAULT, None, None, None)
        return False

    def _on_copy_path(self, item, e):
        icon = self.selected_icon
        komorebi.utilities.clipboard.set_text(icon.path, len(icon.path))
        komorebi.utilities.clipboard.store()
        return False

    def _on_paste(self, item, e):
        # Get the actual GLib file
        path = komorebi.utilities.clipboard.wait_for_text()
        file = Gio.File.new_for_path(path)
        desktop_file = Gio.File.new_for_path(self.desktop_path + '/' + file.get_basename())
        file.copy(desktop_file, Gio.FileCopyFlags.NONE, None)
        return False

    def _on_move_to_trash(self, item, e):
        icon = self.selected_icon

        icon.trash()
        source_file = Gio.File.new_for_path(icon.path)

        try:
            source_file.trash()
        except GLib.Error as err:
            logging.warning(f'Error deleting {icon.title_name}: {err}')

        return False

    def _on_get_info(self, item, e):
        icon = self.selected_icon
        self.info_window.set_info_from_path(icon.path)
        self.info_window.show_all()
        return False

    def register_menu_actions(self, menu):
        # Register the actions
        self.new_folder_item = BubbleMenuItem('New Folder', self._on_create_new_folder)
        self.copy_path_item = BubbleMenuItem('Copy Path', self._on_copy_path)
        self.paste_item = BubbleMenuItem('Paste', self._on_paste)
        self.move_to_trash_item = BubbleMenuItem('Move to Trash', self._on_move_to_trash)
        self.get_info_item = BubbleMenuItem('Get Info', self._on_get_info)

        # Add them to the menu
        menu.overlay_options.add_child(self.move_to_trash_item)
        menu.overlay_options.add_child(self.copy_path_item)
        menu.overlay_options.add_child(self.get_info_item)
        menu.overlay_options.add_child(self.new_folder_item)
        menu.overlay_options.add_child(self.paste_item)

        # Callbacks for when menu opens and closes
        def _on_menu_open(menu, e, self):
            # Dim unselected icons
            for icon in self.icons_list:
                if e.source != icon:
                    icon.dim_icon()
                else:
                    self.selected_icon = icon

            # If there's a selected icon, configure avaliable options
            if self.selected_icon:
                # Hide meta options
                menu.meta_options.hide()
                menu.wallpaper_options.hide()
                if isinstance(self.selected_icon, TrashIcon):
                    for item in [self.move_to_trash_item, self.copy_path_item, self.get_info_item,
                                 self.new_folder_item, self.paste_item]:
                        item.set_view_mode(ViewMode.INVISIBLE)
                else:
                    self.move_to_trash_item.set_view_mode(ViewMode.VISIBLE)
                    self.copy_path_item.set_view_mode(ViewMode.VISIBLE)
                    self.get_info_item.set_view_mode(ViewMode.VISIBLE)
                    self.new_folder_item.set_view_mode(ViewMode.INVISIBLE)
                    self.paste_item.set_view_mode(ViewMode.INVISIBLE)
            else:
                self.move_to_trash_item.set_view_mode(ViewMode.INVISIBLE)
                self.copy_path_item.set_view_mode(ViewMode.INVISIBLE)
                self.get_info_item.set_view_mode(ViewMode.INVISIBLE)
                self.new_folder_item.set_view_mode(ViewMode.VISIBLE)
                # FIXME: This line hangs if user "spams" the menu with right-click; investigate further
                if komorebi.utilities.clipboard.wait_for_text() is not None:
                    self.paste_item.set_view_mode(ViewMode.VISIBLE)
                else:
                    self.paste_item.set_view_mode(ViewMode.GREYED)

            return False

        def _on_menu_close(_, self):
            # Restore meta options
            menu.meta_options.show()
            menu.wallpaper_options.show()

            for icon in self.icons_list:
                icon.un_dim_icon()
            self.selected_icon = None

            return False

        menu.connect_weak('menu_opened', _on_menu_open, self)
        menu.connect_weak('menu_closed', _on_menu_close, self)

    def monitor_changes(self):
        def _on_file_monitor_changed(file_mon, file, other_file, event):
            if event is Gio.FileMonitorEvent.DELETED or event is Gio.FileMonitorEvent.CREATED:
                self.get_desktops()

        self.file_monitor = Gio.File.new_for_path(self.desktop_path).monitor(Gio.FileMonitorFlags.NONE)
        self.file_monitor_signal = self.file_monitor.connect("changed", _on_file_monitor_changed)

    # Get .desktop's
    def get_desktops(self):
        self.icons_list.clear()
        self.grab_desktop_paths()
        self.add_trash_icon()
        self.add_icons_from_queue()

    # Adds all icons from the queue
    def add_icons_from_queue(self):
        import math
        self.items_limit = math.floor(self.screen_height / (83 + self.vertical_layout.get_spacing()))
        self.clear_icons()
        self.destroy_all_children()

        for icon in self.icons_list:
            self.append(icon)
            icon.un_dim_icon()

    # Async get desktop items
    def grab_desktop_paths(self):
        desktop_file = Gio.File.new_for_path(self.desktop_path)

        it = desktop_file.enumerate_children('standard::*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)
        info = it.next_file()

        while info is not None:
            name = info.get_name()
            file_path = self.desktop_path + "/" + name
            desktop_file = Gio.File.new_for_path(file_path)
            icon = None

            # Check if file is .desktop
            if desktop_file.get_basename().endswith(".desktop"):
                key_file = GLib.KeyFile()
                key_file.load_from_file(desktop_file.get_path(), GLib.KeyFileFlags.NONE)

                # Make sure the key_file has the required keys
                if (key_file.get_value(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME) is None
                        or key_file.get_value(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON) is None
                        or key_file.get_value(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_EXEC) is None):
                    continue

                name = key_file.get_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_NAME)
                icon_path = key_file.get_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON)
                icon_pixbuf = komorebi.utilities.get_icon_from(icon_path, self.icon_size)
                command = key_file.get_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_EXEC)
                icon = ApplicationIcon(name, icon_pixbuf, desktop_file.get_path(), command, self.icon_size)
            else:
                icon_path = self.load_icon(desktop_file)

                if icon_path is None:
                    if desktop_file.query_file_type(Gio.FileQueryInfoFlags.NONE) is Gio.FileType.DIRECTORY:
                        icon_path = "folder"
                    else:
                        icon_query = desktop_file.query_info("standard::icon", Gio.FileQueryInfoFlags.NONE) \
                                                 .get_icon().to_string().split(' ')
                        if len(icon_query) > 1:
                            icon_path = icon_query[-1]

                    icon_pixbuf = komorebi.utilities.get_icon_from(icon_path, self.icon_size)
                else:
                    icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, self.icon_size, self.icon_size, False)

                icon = FolderIcon(name, icon_pixbuf, desktop_file.get_path(), self.icon_size)

            self.icons_list.append(icon)

            info = it.next_file()

    # Adds trash icon
    def add_trash_icon(self):
        self.icons_list.append(TrashIcon(self.icon_size))

    # Finds the icon of a file and returns as str
    def load_icon(self, file):
        # Check if it's a .desktop
        if file.get_basename().endswith(".desktop"):
            try:
                key_file = GLib.KeyFile()
                key_file.load_from_file(file.get_path(), GLib.KeyFileFlags.NONE)
                return key_file.get_string(GLib.KEY_FILE_DESKTOP_GROUP, GLib.KEY_FILE_DESKTOP_KEY_ICON)
            except GLib.Error:
                pass

        standard = Gio.FILE_ATTRIBUTE_STANDARD_ICON
        thumb = Gio.FILE_ATTRIBUTE_THUMBNAIL_PATH
        custom_icon = 'standard::icon'
        custom_name = 'metadata::custom-icon-name'

        query = f'{standard},{thumb},{custom_icon},{custom_name}'

        info = file.query_info(query, Gio.FileQueryInfoFlags.NONE)

        # Looks for a thumbnail
        thumb_icon = info.get_attribute_byte_string(thumb)
        if thumb_icon is not None and thumb_icon != '':
            return thumb_icon

        # Otherwise try to get the icon from the fileinfo
        return None

    def fade_in(self):
        self.save_easing_state()
        self.set_easing_duration(200)
        self.set_opacity(255)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    def fade_out(self):
        self.save_easing_state()
        self.set_easing_duration(200)
        self.set_opacity(0)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    # Returns a new Untitled Folder name
    def get_untitled_folder_name(self, count=0):
        path = self.desktop_path + f'/New Folder{count}'
        if Gio.File.new_for_path(path).query_exists():
            path = self.get_untitled_folder_name(count + 1)
        return path
