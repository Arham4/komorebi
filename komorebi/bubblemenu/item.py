import logging
from enum import IntEnum

from gi.repository import Clutter


# View modes for a menu item
class ViewMode(IntEnum):
    VISIBLE = 0     # Item is visible and interactive
    GREYED = 1      # Item is visible but "greyed" out, can't be interacted with
    INVISIBLE = 2   # Item is invisible and doesn't occupy space on the menu


class BubbleMenuItem(Clutter.Text):
    # Properties
    _view_mode = ViewMode.VISIBLE

    def __init__(self, text, callback):
        Clutter.Text.__init__(self)
        logging.debug(f'Initializing BubbleMenuItem(text="{text}")')

        # Setup properties
        self.set_x_align(Clutter.ActorAlign.START)
        self.set_x_expand(True)
        self.set_reactive(False)
        self.set_selectable(False)
        self.set_margin_top(5)

        self.set_font_name('Lato 15')
        self.set_text(text)
        self.set_color(Clutter.Color.from_string('white')[1])

        self.signals_setup()

        self.hide()

        self.connect_after("button_press_event", callback)
        logging.debug('Initialized BubbleMenuItem')

    def signals_setup(self):
        def _on_button_press_event(self, e):
            self.set_opacity(100)
            return False

        def _on_motion_event(self, e):
            self.set_opacity(200)
            return True

        def _on_leave_event(self, e):
            self.set_opacity(255)
            return True

        self.connect_after("button_press_event", _on_button_press_event)
        self.connect_after("motion_event", _on_motion_event)
        self.connect_after("leave_event", _on_leave_event)

    def show_item(self):
        if self._view_mode != ViewMode.INVISIBLE:
            self.show()
            self.set_opacity(255 if self._view_mode == ViewMode.VISIBLE else 10)
            self.set_reactive(self._view_mode == ViewMode.VISIBLE)

    def hide_item(self):
        self.hide()
        self.set_reactive(False)

    def set_view_mode(self, view_mode):
        self._view_mode = view_mode
        if self._view_mode == ViewMode.VISIBLE:
            self.set_opacity(255)
        elif self._view_mode == ViewMode.GREYED:
            self.set_opacity(10)
        elif self._view_mode == ViewMode.INVISIBLE:
            self.hide()
