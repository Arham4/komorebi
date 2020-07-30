import logging

from gi.repository import Clutter, Cogl, GdkPixbuf, Gio, GLib

import komorebi
from komorebi.overlays.base import Overlay, OverlayType


class Asset(Overlay):
    # Screen info
    screen_width = None
    screen_height = None

    # Settings
    visible = None
    animation_mode = None
    animation_speed = None
    asset_width = None
    asset_height = None

    # Image(Asset) and its pixbuf
    image = None
    pixbuf = None

    asset_animation_timeout_handle = None

    # Animation-specific variables
    clouds_direction = 'right'
    fade_type = 'in'

    def __init__(self, screen, config_file):
        Overlay.__init__(self)
        logging.debug('Loading Asset...')

        self.screen_width = screen.width
        self.screen_height = screen.height
        self.set_size(self.screen_width, self.screen_height)
        self.image = Clutter.Image()

        name = config_file.get_string('Info', 'Name')
        self.load_settings(config_file)
        self.set_asset(name)

        self.set_content(self.image)
        logging.debug('Loaded Asset')

    def on_unload(self):
        logging.debug('Unloading Asset...')
        if self.asset_animation_timeout_handle:
            GLib.source_remove(self.asset_animation_timeout_handle)
            self.asset_animation_timeout_handle = 0

    def __del__(self):
        logging.debug('Unloaded Asset')

    def load_settings(self, config_file):
        self.visible = config_file.get_boolean(OverlayType.ASSET.value, 'Visible')

        self.animation_mode = config_file.get_string(OverlayType.ASSET.value, 'AnimationMode')
        self.animation_speed = config_file.get_integer(OverlayType.ASSET.value, 'AnimationSpeed')

        self.asset_width = config_file.get_integer(OverlayType.ASSET.value, 'Width')
        self.asset_height = config_file.get_integer(OverlayType.ASSET.value, 'Height')

    def register_menu_actions(self, menu):
        def _on_menu_open(_1, _2, self):
            # FIXME: Looks ugly to hide the asset overlay, try to blend in
            self.hide()
            return False

        def _on_menu_close(_, self):
            self.show()
            return False

        menu.connect_weak('menu_opened', _on_menu_open, self)
        menu.connect_weak('menu_closed', _on_menu_close, self)

    def set_asset(self, name):
        if self.asset_width <= 0:
            self.asset_width = self.screen_width
        if self.asset_height <= 0:
            self.asset_height = self.screen_height

        asset_path = f'{komorebi.__package_datadir__}/{name}/assets.png'

        if not Gio.File.new_for_path(asset_path).query_exists():
            logging.warning(f'asset with path: {asset_path} does not exist!')
            return

        if self.asset_width != 0 and self.asset_height != 0:
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(asset_path, self.asset_width, self.asset_height, False)
        else:
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(asset_path)

        self.image.set_data(self.pixbuf.get_pixels(),
                            Cogl.PixelFormat.RGBA_8888 if self.pixbuf.get_has_alpha() else Cogl.PixelFormat.RGB_888,
                            self.pixbuf.get_width(), self.pixbuf.get_height(), self.pixbuf.get_rowstride())

        self.set_x(0)
        self.set_y(0)
        self.set_opacity(255)
        self.remove_all_transitions()

        self.animate() if self.should_animate() else self.fade_in()

    def should_animate(self):
        if self.animation_mode == 'noanimation':
            if self.asset_animation_timeout_handle:
                GLib.Source.remove(self.asset_animation_timeout_handle)
                self.asset_animation_timeout_handle = 0

            self.remove_all_transitions()
            self.fade_out()
            return False

        return True

    def animate(self):
        def _on_animation_timeout(self):
            if self.animation_mode == 'clouds':
                if self.clouds_direction == 'right':
                    if self.get_x() + (self.get_width() / 2) >= self.screen_width:
                        self.clouds_direction = 'left'
                    else:
                        self.save_easing_state()
                        self.set_easing_duration(self.animation_speed * 100)
                        self.props.x += 60
                        self.set_easing_mode(Clutter.AnimationMode.LINEAR)
                        self.restore_easing_state()
                else:
                    if self.get_x() <= 0:
                        self.clouds_direction = 'right'
                    else:
                        self.save_easing_state()
                        self.set_easing_duration(self.animation_speed * 100)
                        self.props.x -= 60
                        self.set_easing_mode(Clutter.AnimationMode.LINEAR)
                        self.restore_easing_state()
            elif self.animation_mode == 'light':
                if self.fade_type == 'in':
                    self.fade_in(self.animation_speed * 100)
                    self.fade_type = 'out'
                else:
                    self.fade_out(self.animation_speed * 100)
                    self.fade_type = 'in'

            return True

        if self.animation_speed <= 10:
            self.animation_speed = 100
            logging.warning('The Asset Animation Speed has been adjusted in this wallpaper.'
                            'Please consider updating it to at least 100')

        self.asset_animation_timeout_handle = GLib.timeout_add(self.animation_speed * 30, _on_animation_timeout, self)

    def fade_in(self, custom_duration=90):
        self.save_easing_state()
        self.set_easing_duration(custom_duration)
        self.props.opacity = 255
        self.set_easing_mode(Clutter.AnimationMode.LINEAR)
        self.restore_easing_state()

    def fade_out(self, custom_duration=90):
        self.save_easing_state()
        self.set_easing_duration(custom_duration)
        self.props.opacity = 0
        self.set_easing_mode(Clutter.AnimationMode.LINEAR)
        self.restore_easing_state()
