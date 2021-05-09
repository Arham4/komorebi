import logging

from gi.repository import Clutter, Gdk, GObject, Gtk, GtkClutter

from komorebi.bubblemenu.menu import BubbleMenu
from komorebi.bubblemenu.item import BubbleMenuItem
import komorebi.utilities


class Screen(Gtk.Window):
    # Screen information
    width = 0
    height = 0
    index = -1

    # Signal information
    signal_handlers = []

    # Bubble Menu
    dimmed = False
    bubble_menu = None

    # Bubble Menu Items
    change_wallpaper_item = None
    settings_item = None

    # Clutter main stage
    embed = None
    stage = None

    # Root nodes
    wallpaper_root = None
    overlay_root = None
    menu_root = None

    def __init__(self, monitor_index):
        logging.debug(f'Initializing background window for monitor {monitor_index}...')
        Gtk.Window.__init__(self, title=f'Komorebi - Screen {monitor_index}')

        # Get monitor info
        display = Gdk.Display.get_default()
        rectangle = display.get_monitor(monitor_index).get_geometry()

        self.width = rectangle.width
        self.height = rectangle.height
        self.index = monitor_index
        if self.width == 0 or self.height == 0:
            raise RuntimeError(f"Couldn't get monitor geometry for monitor {monitor_index}")
        logging.debug(f'{monitor_index} - Rectangle geometry: x={rectangle.x} y={rectangle.y} '
                      f'w={rectangle.width} h={rectangle.height}')
        self.set_gravity(Gdk.Gravity.STATIC)
        self.move(rectangle.x, rectangle.y)

        # Set window properties
        logging.debug(f'{monitor_index} - Setting window properties...')
        self.set_size_request(self.width, self.height)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.set_app_paintable(False)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_accept_focus(True)
        self.stick()
        self.set_decorated(False)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK
                        | Gdk.EventMask.SMOOTH_SCROLL_MASK)

        # Configure Clutter variables and wallpaper
        self.embed = GtkClutter.Embed()
        self.stage = self.embed.get_stage()
        self.stage.set_background_color(Clutter.Color.from_string('black')[1])
        self.stage.set_size(self.width, self.height)

        # Configure root nodes
        self.wallpaper_root = Clutter.Actor()
        self.overlay_root = Clutter.Actor()
        self.signals_setup()

        # Setup BubbleMenu and items
        self.bubble_menu = BubbleMenu(self)

        self.change_wallpaper_item = BubbleMenuItem("Change Wallpaper", self.menu_change_wallpaper)
        self.settings_item = BubbleMenuItem("Desktop Preferences", self.menu_open_settings)

        self.bubble_menu.meta_options.add_child(self.change_wallpaper_item)
        self.bubble_menu.meta_options.add_child(self.settings_item)

        self.stage.add_child(self.wallpaper_root)
        self.stage.add_child(self.overlay_root)
        self.stage.add_child(self.bubble_menu)

        self.add(self.embed)

    def signals_setup(self):
        def _on_button_press_event(_, e, self):
            if e.type == Clutter.EventType.BUTTON_PRESS:
                if e.button == Gdk.BUTTON_SECONDARY and not self.dimmed:
                    self.dim_wallpaper()
                    self.bubble_menu.fade_in(e)
                elif self.dimmed:
                    self.un_dim_wallpaper()
                    self.bubble_menu.fade_out()
            return True

        self.stage.connect('button_press_event', _on_button_press_event, self)

    def connect_weak(self, detailed_signal, handler, *args):
        self.signal_handlers.append(super().connect(detailed_signal, handler, *args))

    def on_settings_changed(self, setting_key):
        # There's only one wallpaper
        for wallpaper in self.wallpaper_root.get_children():
            if wallpaper.on_settings_changed(setting_key):
                self.wallpaper_root.remove_all_children()

        # Iterate over the children
        temp_list = self.overlay_root.get_children()    # We have to copy the list, as it might be modified
        for overlay in temp_list:
            if overlay.on_settings_changed(setting_key):
                self.overlay_root.remove_child(overlay)

        # Let utilities handle adding overlays required
        new_overlays = komorebi.utilities.on_settings_changed(self, setting_key)
        for n_overlay in new_overlays:
            self.overlay_root.add_child(n_overlay)
            n_overlay.register_menu_actions(self.bubble_menu)

    def menu_change_wallpaper(self, item, e):
        logging.debug("Change Wallpaper clicked")
        self.emit('settings_requested', True)
        return False

    def menu_open_settings(self, item, e):
        logging.debug("Open Settings clicked")
        self.emit('settings_requested', False)
        return False

    def load_wallpaper(self, name):
        # Warn all elements of unloading
        for wallpaper in self.wallpaper_root.get_children():
            wallpaper.on_unload()
        for overlay in self.overlay_root.get_children():
            overlay.on_unload()

        # Disconnect all custom signals to allow proper cleanup
        self.bubble_menu.disconnect_all()
        for signal in self.signal_handlers:
            self.disconnect(signal)
        self.signal_handlers = []

        wallpaper_info = komorebi.utilities.get_wallpaper_config_file(name)
        wallpaper = komorebi.utilities.load_wallpaper(self, wallpaper_info)
        overlays = komorebi.utilities.load_overlays(self, wallpaper_info)

        self.wallpaper_root.destroy_all_children()
        self.overlay_root.destroy_all_children()

        self.wallpaper_root.add_child(wallpaper)
        wallpaper.register_menu_actions(self.bubble_menu)

        for overlay in overlays:
            self.overlay_root.add_child(overlay)
            overlay.register_menu_actions(self.bubble_menu)

    def fade_in(self):
        self.show_all()

    def dim_wallpaper(self):
        logging.debug("Dim wallpaper")
        self.wallpaper_root.save_easing_state()
        self.wallpaper_root.set_easing_duration(400)
        self.wallpaper_root.set_opacity(100)
        self.wallpaper_root.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.wallpaper_root.restore_easing_state()

        self.dimmed = True

    def un_dim_wallpaper(self):
        logging.debug("Undim wallpaper")
        self.wallpaper_root.save_easing_state()
        self.wallpaper_root.set_easing_duration(400)
        self.wallpaper_root.set_opacity(255)
        self.wallpaper_root.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.wallpaper_root.restore_easing_state()

        self.dimmed = False

    @GObject.Signal(arg_types=(GObject.TYPE_BOOLEAN,))
    def settings_requested(self, isWallpaper):
        pass
