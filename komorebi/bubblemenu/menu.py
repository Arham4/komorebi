import logging

from gi.repository import Clutter, GObject


class BubbleMenu(Clutter.Actor):
    # Screen info
    screen_width = None
    screen_height = None

    # Signal handlers
    signal_handlers = []

    # Layout
    options_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.VERTICAL, spacing=5)
    hierarchy_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.VERTICAL)

    # Hierarchies
    overlay_options = None
    wallpaper_options = None
    meta_options = None

    def __init__(self, screen):
        Clutter.Actor.__init__(self)
        logging.debug('Loading BubbleMenu...')

        # Get screen dimensions
        self.screen_width = screen.width
        self.screen_height = screen.height

        # Set initial properties
        self.set_layout_manager(self.hierarchy_layout)
        self.set_opacity(0)
        self.set_margin_top(5)
        self.set_margin_right(5)
        self.set_margin_left(20)
        self.set_margin_bottom(5)

        # Initialize and add hierarchies
        self.overlay_options = Clutter.Actor()
        self.wallpaper_options = Clutter.Actor()
        self.meta_options = Clutter.Actor()
        for hierarchy in [self.overlay_options, self.wallpaper_options, self.meta_options]:
            hierarchy.set_layout_manager(self.options_layout)
            hierarchy.set_x_align(Clutter.ActorAlign.START)
            hierarchy.set_x_expand(True)
            self.add_child(hierarchy)

        logging.debug('Loaded BubbleMenu')

    def connect_weak(self, detailed_signal, handler, *args):
        self.signal_handlers.append(super().connect(detailed_signal, handler, *args))

    def disconnect_all(self):
        for signal in self.signal_handlers:
            self.disconnect(signal)
        self.signal_handlers = []

    def fade_in(self, e):
        # Make sure we don't display offscreen
        x = min(e.x, self.screen_width - (self.get_width() + 15 * 2))
        y = min(e.y, self.screen_height - (self.get_height() + 15 * 2))

        self.set_opacity(0)
        self.set_x(x)
        self.set_y(y)
        self.save_easing_state()
        self.set_easing_duration(90)

        self.set_x(x + 15)
        self.set_y(y + 15)
        self.set_scale(1, 1)
        self.set_opacity(255)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

        self.emit('menu_opened', e)

        for hierarchy in self.get_children():
            for child in hierarchy.get_children():
                child.show_item()

        logging.debug("BubbleMenu faded in")

    def fade_out(self):
        self.save_easing_state()
        self.set_easing_duration(90)
        self.set_scale(0.9, 0.9)
        self.set_opacity(0)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

        self.emit('menu_closed')

        for hierarchy in self.get_children():
            for child in hierarchy.get_children():
                child.hide_item()

        logging.debug("BubbleMenu faded out")

    @GObject.Signal(arg_types=(GObject.TYPE_PYOBJECT,))
    def menu_opened(self, event):
        pass

    @GObject.Signal()
    def menu_closed(self):
        pass
