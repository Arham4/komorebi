import logging

from gi.repository import Clutter, GLib

from komorebi.overlays.base import Overlay, OverlayType
from komorebi.settings import Settings
from komorebi.utilities import MarginIndex, RotationIndex


class Clock(Overlay):
    # Screen info
    screen_width = None
    screen_height = None

    # Signals
    time_text_width_signal = None

    # Overlay settings
    parallax = None
    position = None
    alignment = None
    always_on_top = None
    margin = None
    rotation = None

    text_color = None
    text_font = None
    text_alpha = None

    shadow_color = None
    shadow_font = None
    shadow_alpha = None

    # Text Content
    text_container_actor = None
    time_text = None
    date_text = None

    # Shadow Content
    shadow_container_actor = None
    time_shadow_text = None
    date_shadow_text = None

    # Vertical Box Layout
    box_layout = Clutter.BoxLayout(orientation=Clutter.Orientation.VERTICAL)

    # Time updater
    timeout_handle = None

    # Time format
    time_format = None

    # Ability to drag
    drag_action = None

    def __init__(self, screen, config_file):
        Overlay.__init__(self)
        logging.debug('Loading Clock...')

        if not config_file.get_boolean('DateTime', 'Visible'):
            # FIXME: Dirty way to disable Clock when wallpaper definitions say so;
            #        When wallpaper files get rewritten this will be implicitely handled
            return

        self.screen_width = screen.width
        self.screen_height = screen.height

        self.text_container_actor = Clutter.Actor()
        self.time_text = Clutter.Text()
        self.date_text = Clutter.Text()

        self.shadow_container_actor = Clutter.Actor()
        self.time_shadow_text = Clutter.Text()
        self.date_shadow_text = Clutter.Text()

        self.drag_action = Clutter.DragAction()

        # Properties
        self.text_container_actor.set_layout_manager(self.box_layout)
        self.shadow_container_actor.set_layout_manager(self.box_layout)

        self.set_background_color(Clutter.Color(0, 0, 0, 0))
        self.set_opacity(0)
        self.set_reactive(True)

        self.text_container_actor.set_background_color(Clutter.Color(0, 0, 0, 0))
        self.shadow_container_actor.set_background_color(Clutter.Color(0, 0, 0, 0))

        self.time_text.set_x_expand(True)
        self.time_text.set_y_expand(True)

        self.time_shadow_text.set_x_expand(True)
        self.time_shadow_text.set_y_expand(True)

        # Load settings and initialize
        self.load_settings(config_file)
        self.set_date_time()

        self.shadow_container_actor.add_effect(Clutter.BlurEffect())

        self.add_action(self.drag_action)

        self.text_container_actor.add_child(self.time_text)
        self.text_container_actor.add_child(self.date_text)

        self.shadow_container_actor.add_child(self.time_shadow_text)
        self.shadow_container_actor.add_child(self.date_shadow_text)

        self.add_child(self.shadow_container_actor)
        self.add_child(self.text_container_actor)

        # Signals
        self.signals_setup(screen)

        logging.debug('Loaded Clock')

    def load_settings(self, config_file):
        self.parallax = config_file.get_boolean(OverlayType.CLOCK.value, 'Parallax')

        # Initialize margin list
        self.margin = [None] * 4
        self.margin[MarginIndex.LEFT.value] = config_file.get_integer(OverlayType.CLOCK.value, 'MarginLeft')
        self.margin[MarginIndex.TOP.value] = config_file.get_integer(OverlayType.CLOCK.value, 'MarginTop')
        self.margin[MarginIndex.BOTTOM.value] = config_file.get_integer(OverlayType.CLOCK.value, 'MarginBottom')
        self.margin[MarginIndex.RIGHT.value] = config_file.get_integer(OverlayType.CLOCK.value, 'MarginRight')

        # Initialize rotation list
        self.rotation = [None] * 3
        self.rotation[RotationIndex.X.value] = config_file.get_double(OverlayType.CLOCK.value, 'RotationX')
        self.rotation[RotationIndex.Y.value] = config_file.get_double(OverlayType.CLOCK.value, 'RotationY')
        self.rotation[RotationIndex.Z.value] = config_file.get_double(OverlayType.CLOCK.value, 'RotationZ')

        self.position = config_file.get_string(OverlayType.CLOCK.value, 'Position')
        self.alignment = config_file.get_string(OverlayType.CLOCK.value, 'Alignment')
        self.always_on_top = config_file.get_boolean(OverlayType.CLOCK.value, 'AlwaysOnTop')

        self.text_color = config_file.get_string(OverlayType.CLOCK.value, 'Color')
        self.text_alpha = config_file.get_integer(OverlayType.CLOCK.value, 'Alpha')

        self.shadow_color = config_file.get_string(OverlayType.CLOCK.value, 'ShadowColor')
        self.shadow_alpha = config_file.get_integer(OverlayType.CLOCK.value, 'ShadowAlpha')

        self.time_font = config_file.get_string(OverlayType.CLOCK.value, 'TimeFont')
        self.date_font = config_file.get_string(OverlayType.CLOCK.value, 'DateFont')

    def signals_setup(self, screen):
        def _on_motion_notify_event(screen, event, self):
            # FIXME: Hardcoded from old code, easily a customizable property
            layer_coeff = 70
            self.set_x((screen.stage.get_width() - self.get_width()) / 2
                       - (event.x - screen.stage.get_width() / 2) / layer_coeff)
            self.set_y((screen.stage.get_height() - self.get_height()) / 2
                       - (event.y - screen.stage.get_height() / 2) / layer_coeff)
            return False

        if self.parallax and self.position == 'center':
            screen.connect_weak('motion_notify_event', _on_motion_notify_event, self)

    def on_unload(self):
        logging.debug('Unloading Clock...')
        if self.timeout_handle:
            GLib.source_remove(self.timeout_handle)
        if self.time_text_width_signal:
            self.time_text.disconnect(self.time_text_width_signal)

    def __del__(self):
        logging.debug('Unloaded Clock')

    def register_menu_actions(self, menu):
        def _on_menu_open(_1, _2, self):
            self.hide()
            return False

        def _on_menu_close(_, self):
            self.show()
            return False

        menu.connect_weak('menu_opened', _on_menu_open, self)
        menu.connect_weak('menu_closed', _on_menu_close, self)

    def set_date_time(self):
        self.set_alignment()
        self.set_rotation()

        if self.get_opacity() < 1:
            self.fade_in()

        self.set_opacity(self.text_alpha)
        self.shadow_container_actor.set_opacity(self.shadow_alpha)

        self.set_position()

        def _on_notify_width_event(_1, _2, self):
            self.set_position()
            self.set_margins()

        self.time_text_width_signal = self.time_text.connect('notify::width', _on_notify_width_event, self)

        if self.timeout_handle:
            # No need to re-create timeout loop if it exists already
            return

        def _on_timeout(self):
            self.time_format = '%H:%M' if Settings.time_twenty_four else '%l:%M %p'

            glib_time = GLib.DateTime.new_now_local().format(self.time_format)
            glib_date = GLib.DateTime.new_now_local().format('%A, %B %e')

            self.time_text.set_markup(f"<span color='{self.text_color}' font='{self.time_font}'>{glib_time}</span>")
            self.date_text.set_markup(f"<span color='{self.text_color}' font='{self.date_font}'>{glib_date}</span>")

            # Apply same to shadows
            self.time_shadow_text.set_markup(f"<span color='{self.shadow_color}' font='{self.time_font}'>{glib_time}</span>")
            self.date_shadow_text.set_markup(f"<span color='{self.shadow_color}' font='{self.date_font}'>{glib_date}</span>")
            return True

        self.timeout_handle = Clutter.threads_add_timeout(GLib.PRIORITY_DEFAULT, 200, _on_timeout, self)

    def set_alignment(self):
        if self.alignment == 'start':
            self.time_text.set_x_align(Clutter.ActorAlign.START)
            self.time_shadow_text.set_x_align(Clutter.ActorAlign.START)
        elif self.alignment == 'center':
            self.time_text.set_x_align(Clutter.ActorAlign.CENTER)
            self.time_shadow_text.set_x_align(Clutter.ActorAlign.CENTER)
        else:
            self.time_text.set_x_align(Clutter.ActorAlign.END)
            self.time_shadow_text.set_x_align(Clutter.ActorAlign.END)

    def set_position(self):
        if self.position == 'top_right':
            self.set_x(self.screen_width - self.get_width())
            self.set_y(0)
        elif self.position == 'top_center':
            self.set_x((self.screen_width / 2) - (self.get_width() / 2))
            self.set_y(0)
        elif self.position == 'top_left':
            self.set_x(0)
            self.set_y(0)
        elif self.position == 'center_right':
            self.set_x(self.screen_width - self.get_width())
            self.set_y((self.screen_height / 2) - (self.get_height() / 2))
        elif self.position == 'center':
            self.set_x((self.screen_width / 2) - (self.get_width() / 2))
            self.set_y((self.screen_height / 2) - (self.get_height() / 2))
        elif self.position == 'center_left':
            self.set_x(0)
            self.set_y((self.screen_height / 2) - (self.get_height() / 2))
        elif self.position == 'bottom_right':
            self.set_x(self.screen_width - self.get_width())
            self.set_y(self.screen_height - self.get_height())
        elif self.position == 'bottom_center':
            self.set_x((self.screen_width / 2) - (self.get_width() / 2))
            self.set_y(self.screen_height - self.get_height())
        elif self.position == 'bottom_left':
            self.set_x(0)
            self.set_y(self.screen_height - self.get_height())

    def set_margins(self):
        self.set_translation(self.margin[MarginIndex.LEFT.value] - self.margin[MarginIndex.RIGHT.value],
                             self.margin[MarginIndex.TOP.value] - self.margin[MarginIndex.BOTTOM.value],
                             0)

    def set_rotation(self):
        self.set_rotation_angle(Clutter.RotateAxis.X_AXIS, self.rotation[RotationIndex.X.value])
        self.set_rotation_angle(Clutter.RotateAxis.Y_AXIS, self.rotation[RotationIndex.Y.value])
        self.set_rotation_angle(Clutter.RotateAxis.Z_AXIS, self.rotation[RotationIndex.Z.value])

    def move_to(self, x=-1, y=-1):
        self.save_easing_state()
        self.set_easing_duration(90)
        if x != -1:
            self.set_x(x)
        if y != -1:
            self.set_y(y)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()

    def fade_in(self, custom_duration=90):
        self.save_easing_state()
        self.set_easing_duration(90)
        self.set_opacity(self.text_alpha)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()
        self.set_reactive(True)

    def fade_out(self):
        self.save_easing_state()
        self.set_easing_duration(90)
        self.set_opacity(0)
        self.set_easing_mode(Clutter.AnimationMode.EASE_IN_SINE)
        self.restore_easing_state()
        self.set_reactive(False)
