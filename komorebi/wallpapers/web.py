import logging

from gi.repository import GtkClutter, WebKit2

from komorebi.wallpapers.base import Wallpaper
from komorebi.bubblemenu.item import BubbleMenuItem


class WebWallpaper(Wallpaper):
    # Web content
    web_view = None
    web_view_embed = None
    web_page_url = None

    # Menu options
    refresh_item_menu = None

    def __init__(self, screen, wallpaper_config):
        Wallpaper.__init__(self, screen, wallpaper_config)
        logging.debug("Loading WebWallpaper...")

        self.web_view = WebKit2.WebView()
        self.web_view_embed = GtkClutter.Actor.new_with_contents(self.web_view)
        self.web_view_embed.set_size(screen.width, screen.height)

        self.web_page_url = wallpaper_config.get_string('Info', 'WebPageUrl')
        if self.web_page_url is None:
            raise RuntimeError("Wallpaper config doesn't specify web page URL")
        self.web_page_url = self.web_page_url.replace('{{screen_width}}', f'{screen.width}') \
                                             .replace('{{screen_height}}', f'{screen.height}')
        self.web_view.load_uri(self.web_page_url)
        self.web_view_embed.set_reactive(False)

        self.add_child(self.web_view_embed)
        logging.debug("Loaded WebWallpaper")

    def _on_refresh_wallpaper_item(self, item, e):
        self.web_view.load_uri(self.web_page_url)

    def on_unload(self):
        self.refresh_item_menu.destroy()
        logging.debug('Unloading WebWallpaper...')

    def __del__(self):
        logging.debug('Unloaded WebWallpaper')

    def register_menu_actions(self, menu):
        self.refresh_item_menu = BubbleMenuItem('Refresh Wallpaper', self._on_refresh_wallpaper_item)

        menu.wallpaper_options.add_child(self.refresh_item_menu)
