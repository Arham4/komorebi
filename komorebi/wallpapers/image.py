import logging

from gi.repository import Cogl, Clutter, GdkPixbuf

from komorebi.wallpapers.base import Wallpaper


class ImageWallpaper(Wallpaper):
    # Image content
    image = None

    # Wallpaper settings
    parallax = None

    def __init__(self, screen, wallpaper_config):
        Wallpaper.__init__(self, screen, wallpaper_config)
        logging.debug("Loading ImageWallpaper...")

        path = wallpaper_config.get_string('Info', 'Path')

        image_data = GdkPixbuf.Pixbuf.new_from_file_at_scale(f'{path}/wallpaper.jpg', screen.width, screen.height, False)

        self.image = Clutter.Image()
        self.image.set_data(image_data.get_pixels(), Cogl.PixelFormat.RGB_888, image_data.get_width(),
                            image_data.get_height(), image_data.get_rowstride())

        self.set_content(self.image)
        self.set_pivot_point(0.5, 0.5)
        if wallpaper_config.has_group('Wallpaper'):
            self.parallax = wallpaper_config.get_boolean('Wallpaper', 'Parallax')

        # If this wallpaper features parallax, connect to signals
        if self.parallax:
            self.set_scale(1.05, 1.05)
            self.signals_setup(screen)

        logging.debug("Loaded ImageWallpaper")

    def signals_setup(self, screen):
        def _on_motion_notify_event(screen, event, self):
            # FIXME: Hardcoded from old code, easily a customizable property
            layer_coeff = 70

            self.set_x((screen.stage.get_width() - self.get_width()) / 2
                       - (event.x - screen.stage.get_width() / 2) / layer_coeff)
            self.set_y((screen.stage.get_height() - self.get_height()) / 2
                       - (event.y - screen.stage.get_height() / 2) / layer_coeff)

        screen.connect_weak('motion_notify_event', _on_motion_notify_event, self)

    def on_unload(self):
        logging.debug('Unloading ImageWallpaper...')

    def __del__(self):
        logging.debug('Unloaded ImageWallpaper')
