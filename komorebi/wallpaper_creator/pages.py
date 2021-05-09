import os

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk

import komorebi.wallpaper_creator.utilities as utilities
from komorebi.settings import Settings


def rgbaToHex(rgba):
    return '#{:02x}{:02x}{:02x}'.format(int(rgba.red * 255),
                                        int(rgba.green * 255),
                                        int(rgba.blue * 255))


class InitialPage(Gtk.Box):
    # Widgets
    about_grid = None
    title_box = None
    title_lbl = None
    about_lbl = None

    name_lbl = None
    name_entry = None

    type_lbl = None
    type_combo_box = None

    choose_file_lbl = None
    location_box = None
    location_entry = None
    choose_file_btn = None

    revealer = None
    thumbnail_box = None
    choose_thumbnail_lbl = None
    choose_thumbnail_btn = None

    # Filters
    image_filter = None
    video_filter = None

    def __init__(self):
        Gtk.Box.__init__(self, spacing=10, hexpand=True, vexpand=True,
                         orientation=Gtk.Orientation.VERTICAL,
                         halign=Gtk.Align.CENTER,
                         valign=Gtk.Align.CENTER)

        # Initialize elements
        self.about_grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,
                                   margin_bottom=30, column_spacing=0,
                                   row_spacing=0)
        self.title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                 spacing=5, margin_top=15, margin_start=10)
        self.title_lbl = Gtk.Label(halign=Gtk.Align.START)
        self.about_lbl = Gtk.Label(halign=Gtk.Align.START)

        self.name_lbl = Gtk.Label(label='Give your wallpaper a name:')
        self.name_entry = Gtk.Entry(placeholder_text='Mountain Summit')

        self.type_lbl = Gtk.Label('My wallpaper is')
        self.type_combo_box = Gtk.ComboBoxText()

        self.choose_file_lbl = Gtk.Label('Where is the image located?')
        self.location_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.location_entry = Gtk.Entry(placeholder_text='~/Pictures/my_picture.jpg')
        self.choose_file_btn = Gtk.FileChooserButton(title='Choose File',
                                                     action=Gtk.FileChooserAction.OPEN,
                                                     width_chars=10)

        self.revealer = Gtk.Revealer()
        self.thumbnail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.choose_thumbnail_lbl = Gtk.Label(label='Where is the thumbnail located?')
        self.choose_thumbnail_btn = Gtk.FileChooserButton(title='Choose Thumbnail',
                                                          action=Gtk.FileChooserAction.OPEN,
                                                          width_chars=10)

        self.image_filter = Gtk.FileFilter()
        self.video_filter = Gtk.FileFilter()

        # Setup widgets
        self.title_lbl.set_markup("<span font='Lato Light 30px' color='white'>Komorebi Wallpaper Creator</span>")
        self.about_lbl.set_markup("<span font='Lato Light 15px' color='white'>by Komorebi Team</span>")

        self.type_combo_box.append('image', 'An image')
        self.type_combo_box.append('video', 'A video')
        self.type_combo_box.append('web_page', 'A web page')
        self.type_combo_box.set_active(0)

        utilities.wallpaper_type = 'image'

        self.image_filter.add_mime_type('image/*')
        self.video_filter.add_mime_type('video/*')

        self.choose_file_btn.set_filter(self.image_filter)
        self.choose_thumbnail_btn.set_filter(self.image_filter)

        self.location_entry.set_sensitive(False)

        # Setup signals
        def _on_name_entry_changed(name_entry):
            utilities.wallpaper_name = name_entry.get_text() if len(name_entry.get_text()) > 0 else None

        def _on_type_combo_box_changed(_, self):
            utilities.wallpaper_type = self.type_combo_box.get_active_id()

            if utilities.wallpaper_type == 'image':
                self.choose_file_lbl.set_label('Where is the image located?')
                self.location_entry.set_placeholder_text('~/Pictures/my_picture.jpg')
            elif utilities.wallpaper_type == 'web_page':
                self.choose_file_lbl.set_label('What is the URL?')
                self.location_entry.set_placeholder_text('https://sample.com/random/{{screen_width}}x{{screen_height}}')
            else:
                self.choose_file_lbl.set_label('Where is the video located?')
                self.location_entry.set_placeholder_text('~/my_video.mp4')
            self.choose_file_btn.set_filter(self.video_filter if utilities.wallpaper_type == 'video' else self.image_filter)
            self.location_entry.set_sensitive(utilities.wallpaper_type == 'web_page')
            self.revealer.set_reveal_child(utilities.wallpaper_type == 'web_page' or utilities.wallpaper_type == 'video')
            if utilities.wallpaper_type == 'web_page':
                self.choose_file_btn.hide()
            else:
                self.choose_file_btn.show()

        def _on_choose_file_btn_file_set(choose_file_btn):
            utilities.file_path = choose_file_btn.get_file().get_path()

        def _on_choose_thumbnail_btn_file_set(choose_thumbnail_btn):
            utilities.thumbnail_path = choose_thumbnail_btn.get_file().get_path()

        def _on_location_entry_changed(location_entry):
            text = location_entry.get_text()
            if '://' in text and (text.startswith('http') or text.startswith('file')):
                utilities.web_page_url = text
            else:
                utilities.web_page_url = None

        self.name_entry.connect('changed', _on_name_entry_changed)
        self.type_combo_box.connect('changed', _on_type_combo_box_changed, self)
        self.choose_file_btn.connect('file_set', _on_choose_file_btn_file_set)
        self.choose_thumbnail_btn.connect('file_set', _on_choose_thumbnail_btn_file_set)
        self.location_entry.connect('changed', _on_location_entry_changed)

        # Add widgets
        self.title_box.add(self.title_lbl)
        self.title_box.add(self.about_lbl)

        self.about_grid.attach(Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/wallpaper_creator.svg'), 0, 0, 1, 1)
        self.about_grid.attach(self.title_box, 1, 0, 1, 1)

        self.thumbnail_box.add(self.choose_thumbnail_lbl)
        self.thumbnail_box.add(self.choose_thumbnail_btn)

        self.revealer.add(self.thumbnail_box)

        self.location_box.pack_start(self.location_entry, True, True, 0)
        self.location_box.add(self.choose_file_btn)

        self.add(self.about_grid)
        self.add(self.name_lbl)
        self.add(self.name_entry)

        self.add(self.type_lbl)
        self.add(self.type_combo_box)

        self.add(self.choose_file_lbl)
        self.add(self.location_box)

        self.add(self.revealer)


class OptionsPage(Gtk.Box):
    # Widgets
    wallpaper_box = None
    overlay = None
    wallpaper_image = None
    date_time_box = None
    time_lbl = None
    date_lbl = None
    asset_image = None

    # List of long options
    scrolled_window = None
    options_box = None

    wallpaper_title_lbl = None
    wallpaper_parallax_combo_box = None

    date_time_title_lbl = None
    date_time_visible_combo_box = None
    date_time_parallax_combo_box = None
    date_time_margins_lbl = None
    date_time_margins_grid = None
    date_time_margin_left_entry = None
    date_time_margin_right_entry = None
    date_time_margin_top_entry = None
    date_time_margin_bottom_entry = None

    date_time_position_lbl = None
    date_time_position_combo_box = None

    date_time_alignment_lbl = None
    date_time_alignment_combo_box = None

    date_time_always_on_top_combo_box = None

    date_time_color_lbl = None
    date_time_color_box = None
    date_time_color_btn = None
    date_time_alpha_entry = None

    date_time_shadow_color_lbl = None
    date_time_shadow_color_box = None
    date_time_shadow_color_btn = None
    date_time_shadow_alpha_entry = None

    time_font_lbl = None
    time_font_btn = None

    date_font_lbl = None
    date_font_btn = None

    # Asset (Layer)
    asset_title_lbl = None

    asset_visible_combo_box = None

    asset_animation_lbl = None
    asset_animation_box = None
    asset_mode_combo_box = None
    asset_speed_entry = None

    def __init__(self):
        Gtk.Box.__init__(self, spacing=10, orientation=Gtk.Orientation.HORIZONTAL,
                         halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER,
                         hexpand=False, vexpand=True)

        # Initialize widgets
        self.wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                     spacing=10, margin_top=20, margin_bottom=20,
                                     margin_start=20, margin_end=0,
                                     valign=Gtk.Align.CENTER, halign=Gtk.Align.START)
        self.overlay = Gtk.Overlay()
        self.wallpaper_image = Gtk.Image()
        self.date_time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                                     hexpand=True, vexpand=True, halign=Gtk.Align.CENTER,
                                     valign=Gtk.Align.CENTER)
        self.time_lbl = Gtk.Label()
        self.date_lbl = Gtk.Label()
        self.asset_image = Gtk.Image()
        self.scrolled_window = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                                   margin_top=20, margin_bottom=20, margin_end=20,
                                   margin_start=0, halign=Gtk.Align.START, hexpand=True)
        self.wallpaper_title_lbl = Gtk.Label()
        self.wallpaper_parallax_combo_box = Gtk.ComboBoxText()
        self.date_time_title_lbl = Gtk.Label(margin_top=15)
        self.date_time_visible_combo_box = Gtk.ComboBoxText()
        self.date_time_parallax_combo_box = Gtk.ComboBoxText()
        self.date_time_margins_lbl = Gtk.Label(label='Margins:')
        self.date_time_margins_grid = Gtk.Grid()
        self.date_time_margin_left_entry = Gtk.SpinButton.new_with_range(0, 2000, 5)
        self.date_time_margin_right_entry = Gtk.SpinButton.new_with_range(0, 2000, 5)
        self.date_time_margin_top_entry = Gtk.SpinButton.new_with_range(0, 2000, 5)
        self.date_time_margin_bottom_entry = Gtk.SpinButton.new_with_range(0, 2000, 5)
        self.date_time_position_lbl = Gtk.Label('Position:')
        self.date_time_position_combo_box = Gtk.ComboBoxText()
        self.date_time_alignment_lbl = Gtk.Label('Alignment:')
        self.date_time_alignment_combo_box = Gtk.ComboBoxText()
        self.date_time_always_on_top_combo_box = Gtk.ComboBoxText()
        self.date_time_color_lbl = Gtk.Label('Color and Alpha:')
        self.date_time_color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.date_time_color_btn = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(222, 222, 222, 255))
        self.date_time_alpha_entry = Gtk.SpinButton.new_with_range(0, 255, 1)
        self.date_time_shadow_color_lbl = Gtk.Label(label='Shadow Color and Alpha:')
        self.date_time_shadow_color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.date_time_shadow_color_btn = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(222, 222, 222, 255))
        self.date_time_shadow_alpha_entry = Gtk.SpinButton.new_with_range(0, 255, 1)
        self.time_font_lbl = Gtk.Label(label='Time Font:')
        self.time_font_btn = Gtk.FontButton.new_with_font('Lato Light 30')
        self.date_font_lbl = Gtk.Label(label='Date Font:')
        self.date_font_btn = Gtk.FontButton.new_with_font('Lato Light 20')
        self.asset_title_lbl = Gtk.Label(margin_top=15)
        self.asset_visible_combo_box = Gtk.ComboBoxText()
        self.asset_animation_lbl = Gtk.Label('Animation Mode & Speed:')
        self.asset_animation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.asset_mode_combo_box = Gtk.ComboBoxText()
        self.asset_speed_entry = Gtk.SpinButton.new_with_range(100, 1000, 1)

        # Setup widgets
        self.wallpaper_title_lbl.set_markup("<span font='Lato Light 15'>Wallpaper Options:</span>")
        self.date_time_title_lbl.set_markup("<span font='Lato Light 15'>Date &amp; Time Options:</span>")
        self.asset_title_lbl.set_markup("<span font='Lato Light 15'>Layer Options:</span>")

        self.date_time_alpha_entry.set_value(255)
        self.date_time_shadow_alpha_entry.set_value(255)
        self.time_font_btn.set_use_font(True)
        self.date_font_btn.set_use_font(True)

        self.date_time_visible_combo_box.append('show', 'Show date & time')
        self.date_time_visible_combo_box.append('hide', 'Hide date & time')
        self.date_time_visible_combo_box.set_active(0)

        self.wallpaper_parallax_combo_box.append('enable', 'Enable parallax')
        self.wallpaper_parallax_combo_box.append('disable', 'Disable parallax')
        self.wallpaper_parallax_combo_box.set_active(1)

        self.date_time_parallax_combo_box.append('enable', 'Enable parallax')
        self.date_time_parallax_combo_box.append('disable', 'Disable parallax')
        self.date_time_parallax_combo_box.set_active(1)

        self.date_time_position_combo_box.append_text('Top Left')
        self.date_time_position_combo_box.append_text('Top Center')
        self.date_time_position_combo_box.append_text('Top Right')
        self.date_time_position_combo_box.append_text('Center Left')
        self.date_time_position_combo_box.append_text('Center')
        self.date_time_position_combo_box.append_text('Center Right')
        self.date_time_position_combo_box.append_text('Bottom Left')
        self.date_time_position_combo_box.append_text('Bottom Center')
        self.date_time_position_combo_box.append_text('Bottom Right')
        self.date_time_position_combo_box.set_active(4)

        self.date_time_alignment_combo_box.append_text('Start')
        self.date_time_alignment_combo_box.append_text('Center')
        self.date_time_alignment_combo_box.append_text('End')
        self.date_time_alignment_combo_box.set_active(1)

        self.date_time_always_on_top_combo_box.append('enable', 'Always show on top')
        self.date_time_always_on_top_combo_box.append('disable', 'Show under layer')
        self.date_time_always_on_top_combo_box.set_active(0)

        self.asset_visible_combo_box.append('show', 'Show layer')
        self.asset_visible_combo_box.append('hide', 'Hide layer')
        self.asset_visible_combo_box.set_active(0)

        self.asset_mode_combo_box.append('noanimation', 'No Animation')
        self.asset_mode_combo_box.append('light', 'Glowing Light')
        self.asset_mode_combo_box.append('clouds', 'Moving Clouds')
        self.asset_mode_combo_box.set_active(0)

        # Setup signals
        self.wallpaper_parallax_combo_box.connect('changed', self.update_ui, self)
        self.date_time_visible_combo_box.connect('changed', self.update_ui, self)
        self.date_time_parallax_combo_box.connect('changed', self.update_ui, self)
        self.date_time_margin_top_entry.connect('changed', self.update_ui, self)
        self.date_time_margin_right_entry.connect('changed', self.update_ui, self)
        self.date_time_margin_left_entry.connect('changed', self.update_ui, self)
        self.date_time_margin_bottom_entry.connect('changed', self.update_ui, self)
        self.date_time_position_combo_box.connect('changed', self.update_ui, self)
        self.date_time_alignment_combo_box.connect('changed', self.update_ui, self)
        self.date_time_color_btn.connect('color_set', self.update_ui, self)
        self.date_time_alpha_entry.connect('changed', self.update_ui, self)
        self.time_font_btn.connect('font_set', self.update_ui, self)
        self.date_font_btn.connect('font_set', self.update_ui, self)

        # Add widgets
        self.date_time_box.add(self.time_lbl)
        self.date_time_box.add(self.date_lbl)

        self.overlay.add(self.wallpaper_image)
        self.overlay.add_overlay(self.date_time_box)
        self.overlay.add_overlay(self.asset_image)

        self.wallpaper_box.add(self.overlay)

        self.date_time_margins_grid.attach(self.date_time_margin_top_entry, 0, 0, 1, 1)
        self.date_time_margins_grid.attach(self.date_time_margin_right_entry, 0, 1, 1, 1)
        self.date_time_margins_grid.attach(self.date_time_margin_left_entry, 1, 0, 1, 1)
        self.date_time_margins_grid.attach(self.date_time_margin_bottom_entry, 1, 1, 1, 1)

        if utilities.wallpaper_type == 'image':
            self.options_box.add(self.wallpaper_title_lbl)
            self.options_box.add(self.wallpaper_parallax_combo_box)

        self.options_box.add(self.date_time_title_lbl)

        self.options_box.add(self.date_time_visible_combo_box)
        self.options_box.add(self.date_time_parallax_combo_box)

        self.options_box.add(self.date_time_position_lbl)
        self.options_box.add(self.date_time_position_combo_box)

        self.options_box.add(self.date_time_margins_lbl)
        self.options_box.add(self.date_time_margins_grid)

        self.options_box.add(self.date_time_alignment_lbl)
        self.options_box.add(self.date_time_alignment_combo_box)

        self.options_box.add(self.date_time_always_on_top_combo_box)

        self.options_box.add(self.date_time_color_lbl)

        self.date_time_color_box.add(self.date_time_color_btn)
        self.date_time_color_box.add(self.date_time_alpha_entry)

        self.options_box.add(self.date_time_color_box)

        self.options_box.add(self.date_time_shadow_color_lbl)

        self.date_time_shadow_color_box.add(self.date_time_shadow_color_btn)
        self.date_time_shadow_color_box.add(self.date_time_shadow_alpha_entry)

        self.options_box.add(self.date_time_shadow_color_box)

        self.options_box.add(self.time_font_lbl)
        self.options_box.add(self.time_font_btn)

        self.options_box.add(self.date_font_lbl)
        self.options_box.add(self.date_font_btn)

        if utilities.wallpaper_type == 'image':
            self.options_box.add(self.asset_title_lbl)
            self.options_box.add(self.asset_visible_combo_box)
            self.options_box.add(self.asset_animation_lbl)
            self.asset_animation_box.add(self.asset_mode_combo_box)
            self.asset_animation_box.add(self.asset_speed_entry)
            self.options_box.add(self.asset_animation_box)

        self.scrolled_window.add(self.options_box)

        self.pack_start(self.wallpaper_box, True, True, 0)
        self.pack_start(self.scrolled_window, True, True, 0)

        self.set_date_time_label()

        for child in self.options_box.get_children():
            child.set_halign(Gtk.Align.START)

    def update_ui(*args):
        self = args[-1]
        utilities.wallpaper_parallax = self.wallpaper_parallax_combo_box.get_active_id() == 'enable'

        utilities.show_date_time = self.date_time_visible_combo_box.get_active_id() == 'show'
        utilities.date_time_parallax = self.date_time_parallax_combo_box.get_active_id() == 'enable'

        if self.date_time_margin_top_entry.get_text() != '':
            utilities.margin_top = int(self.date_time_margin_top_entry.get_text())
        if self.date_time_margin_right_entry.get_text() != '':
            utilities.margin_right = int(self.date_time_margin_right_entry.get_text())
        if self.date_time_margin_left_entry.get_text() != '':
            utilities.margin_left = int(self.date_time_margin_left_entry.get_text())
        if self.date_time_margin_bottom_entry.get_text() != '':
            utilities.margin_bottom = int(self.date_time_margin_bottom_entry.get_text())

        self.date_time_box.set_opacity(255 * utilities.show_date_time)
        self.date_time_box.set_visible(False)

        self.date_time_box.set_margin_top(utilities.margin_top)
        self.date_time_box.set_margin_right(utilities.margin_right)
        self.date_time_box.set_margin_left(utilities.margin_left)
        self.date_time_box.set_margin_bottom(utilities.margin_bottom)

        self.set_position()
        self.set_alignment()

        utilities.date_time_always_on_top = self.date_time_always_on_top_combo_box.get_active_id() == 'enable'

        self.set_colors()
        self.set_fonts()
        self.set_opacity()

        utilities.show_asset = self.asset_visible_combo_box.get_active_id() == 'show'
        self.asset_image.set_opacity(255 * utilities.show_asset)

        self.set_animation_mode()
        if self.asset_speed_entry.get_text() != '':
            utilities.animation_speed = int(self.asset_speed_entry.get_text())

        self.set_date_time_label(utilities.date_time_color, utilities.time_font, utilities.date_font)
        self.show_all()

    def set_position(self):
        active = self.date_time_position_combo_box.get_active_text()
        utilities.position = active.replace(' ', '_').lower()
        if active == 'Top Left':
            self.date_time_box.set_halign(Gtk.Align.START)
            self.date_time_box.set_valign(Gtk.Align.START)
        elif active == 'Top Center':
            self.date_time_box.set_halign(Gtk.Align.CENTER)
            self.date_time_box.set_valign(Gtk.Align.START)
        elif active == 'Top Right':
            self.date_time_box.set_halign(Gtk.Align.END)
            self.date_time_box.set_valign(Gtk.Align.START)
        elif active == 'Center Right':
            self.date_time_box.set_halign(Gtk.Align.END)
            self.date_time_box.set_valign(Gtk.Align.CENTER)
        elif active == 'Center':
            self.date_time_box.set_halign(Gtk.Align.CENTER)
            self.date_time_box.set_valign(Gtk.Align.CENTER)
        elif active == 'Center Left':
            self.date_time_box.set_halign(Gtk.Align.START)
            self.date_time_box.set_valign(Gtk.Align.CENTER)
        elif active == 'Bottom Right':
            self.date_time_box.set_halign(Gtk.Align.END)
            self.date_time_box.set_valign(Gtk.Align.END)
        elif active == 'Bottom Center':
            self.date_time_box.set_halign(Gtk.Align.CENTER)
            self.date_time_box.set_valign(Gtk.Align.END)
        elif active == 'Bottom Left':
            self.date_time_box.set_halign(Gtk.Align.START)
            self.date_time_box.set_valign(Gtk.Align.END)

    def set_alignment(self):
        utilities.alignment = self.date_time_alignment_combo_box.get_active_text().lower()

        if utilities.alignment == 'start':
            self.time_lbl.set_halign(Gtk.Align.START)
        elif utilities.alignment == 'center':
            self.time_lbl.set_halign(Gtk.Align.CENTER)
        else:
            self.time_lbl.set_halign(Gtk.Align.END)

    def set_colors(self):
        rgba = self.date_time_color_btn.get_rgba()
        utilities.date_time_color = rgbaToHex(rgba)

        rgba = self.date_time_shadow_color_btn.get_rgba()
        utilities.shadow_color = rgbaToHex(rgba)

    def set_fonts(self):
        utilities.time_font = self.time_font_btn.get_font_name()
        utilities.date_font = self.date_font_btn.get_font_name()

    def set_opacity(self):
        if self.date_time_alpha_entry.get_text() != '':
            alpha = float(self.date_time_alpha_entry.get_text())
            self.time_lbl.set_opacity(alpha / 255)
            self.date_lbl.set_opacity(alpha / 255)
            utilities.date_time_alpha = int(alpha)

        if self.date_time_shadow_alpha_entry.get_text() != '':
            alpha = int(self.date_time_shadow_alpha_entry.get_text())
            utilities.shadow_alpha = int(alpha)

    def set_image(self, path):
        self.wallpaper_image.props.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 600, 400, True)

    def set_blank(self):
        self.wallpaper_image.props.pixbuf = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
            '/org/komorebi-team/komorebi/blank.svg', 600, 400, True
        )

    def set_asset(self, path):
        self.asset_image.props.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 600, 400, True)

    def set_animation_mode(self):
        utilities.animation_mode = self.asset_mode_combo_box.get_active_id()

    def set_date_time_label(self, color='white', time_font='Lato Light 30', date_font='Lato Light 20'):
        self.time_lbl.set_markup(f"<span color='{color}' font='{time_font}'>10:21 PM</span>")
        self.date_lbl.set_markup(f"<span color='{color}' font='{date_font}'>Sunday, August 22</span>")


class FinalPage(Gtk.Box):
    # Widgets
    logo = None
    title_lbl = None
    desc_lbl = None
    close_btn = None

    def __init__(self):
        Gtk.Box.__init__(self, spacing=10, hexpand=True, vexpand=True,
                         orientation=Gtk.Orientation.VERTICAL,
                         halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)

        # Initialize widgets
        self.logo = Gtk.Image.new_from_resource('/org/komorebi-team/komorebi/done.svg')
        self.title_lbl = Gtk.Label()
        self.desc_lbl = Gtk.Label()
        self.close_btn = Gtk.Button(label='Close', margin_top=20, halign=Gtk.Align.CENTER)

        # Setup widgets
        self.logo.set_margin_bottom(30)
        self.desc_lbl.set_justify(Gtk.Align.CENTER)
        self.desc_lbl.set_halign(Gtk.Align.CENTER)
        self.desc_lbl.set_hexpand(False)
        self.desc_lbl.set_selectable(True)

        utilities.wallpaper_name = utilities.wallpaper_name.replace(" ", "_").replace(".", "_").lower()

        self.title_lbl.set_markup("<span font='Lato 20'>Done</span>")

        wallpaper_path = os.path.join(Settings.get_config_dir(), 'wallpapers', utilities.wallpaper_name)
        self.desc_lbl.set_markup(f"<span font='Lato Light 12'>Your wallpaper was copied to:\n<b>{wallpaper_path}</b>\n"
                                 "You can now change the wallpaper in <i>'Change Wallpaper'</i>.</span>")

        # Setup signals
        def _on_close_btn_released(_):
            Gtk.main_quit()

        self.close_btn.connect('released', _on_close_btn_released)

        # Add widgets
        self.add(self.logo)
        self.add(self.title_lbl)
        self.add(self.desc_lbl)
        self.add(self.close_btn)

        self.create_wallpaper()

    def create_wallpaper(self):
        # Create a new directory
        utilities.wallpaper_name = utilities.wallpaper_name.replace(' ', '_').replace('.', '_').lower()

        dir_path = os.path.join(Settings.get_config_dir(), 'wallpapers', utilities.wallpaper_name)
        Gio.File.new_for_path(dir_path).make_directory_with_parents()
        config_path = dir_path + '/config'
        config_file = Gio.File.new_for_path(config_path)

        config_key_file = GLib.KeyFile()

        config_key_file.set_string('Info', 'WallpaperType', utilities.wallpaper_type)

        if utilities.wallpaper_type == 'video':
            video_file_name = utilities.file_path.split('/')[-1]
            config_key_file.set_string('Info', 'VideoFileName', video_file_name)

            # Copy the video into our new dir
            Gio.File.new_for_path(utilities.file_path).copy(Gio.File.new_for_path(os.path.join(dir_path, video_file_name)),
                                                            Gio.FileCopyFlags.NONE)
        elif utilities.wallpaper_type == 'web_page':
            config_key_file.set_string('Info', 'WebPageUrl', utilities.web_page_url)

        if utilities.wallpaper_type == 'video' or utilities.wallpaper_type == 'web_page':
            # Move the thumbnail
            Gio.File.new_for_path(utilities.thumbnail_path).copy(
                Gio.File.new_for_path(os.path.join(dir_path, 'wallpaper.jpg')),
                Gio.FileCopyFlags.NONE
            )
        else:
            # Copy the wallpaper into our new dir
            Gio.File.new_for_path(utilities.file_path).copy(Gio.File.new_for_path(os.path.join(dir_path, 'wallpaper.jpg')),
                                                            Gio.FileCopyFlags.NONE)

        config_key_file.set_boolean('DateTime', 'Visible', utilities.show_date_time)
        config_key_file.set_boolean('DateTime', 'Parallax', utilities.date_time_parallax)

        config_key_file.set_integer('DateTime', 'MarginTop', utilities.margin_top)
        config_key_file.set_integer('DateTime', 'MarginRight', utilities.margin_right)
        config_key_file.set_integer('DateTime', 'MarginLeft', utilities.margin_left)
        config_key_file.set_integer('DateTime', 'MarginBottom', utilities.margin_bottom)

        # TODO: Add support for rotations
        config_key_file.set_integer('DateTime', 'RotationX', 0)
        config_key_file.set_integer('DateTime', 'RotationY', 0)
        config_key_file.set_integer('DateTime', 'RotationZ', 0)

        config_key_file.set_string('DateTime', 'Position', utilities.position)
        config_key_file.set_string('DateTime', 'Alignment', utilities.alignment)
        config_key_file.set_boolean('DateTime', 'AlwaysOnTop', utilities.date_time_always_on_top)

        config_key_file.set_string('DateTime', 'Color', utilities.date_time_color)
        config_key_file.set_integer('DateTime', 'Alpha', utilities.date_time_alpha)

        config_key_file.set_string('DateTime', 'ShadowColor', utilities.shadow_color)
        config_key_file.set_integer('DateTime', 'ShadowAlpha', utilities.shadow_alpha)

        config_key_file.set_string('DateTime', 'TimeFont', utilities.time_font)
        config_key_file.set_string('DateTime', 'DateFont', utilities.date_font)

        if utilities.wallpaper_type == 'image':
            config_key_file.set_boolean('Wallpaper', 'Parallax', utilities.wallpaper_parallax)

            if not utilities.asset_path or utilities.asset_path == '':
                utilities.show_asset = False

            config_key_file.set_boolean('Asset', 'Visible', utilities.show_asset)
            config_key_file.set_string('Asset', 'AnimationMode', utilities.animation_mode)
            config_key_file.set_integer('Asset', 'AnimationSpeed', utilities.animation_speed)

            config_key_file.set_integer('Asset', 'Width', 0)
            config_key_file.set_integer('Asset', 'Height', 0)

            if utilities.asset_path:
                # Move the asset into our new dir
                Gio.File.new_for_path(utilities.asset_path).copy(Gio.File.new_for_path(os.path.join(dir_path, 'assets.png')),
                                                                 Gio.FileCopyFlags.NONE)

        # Save the key file
        stream = Gio.DataOutputStream.new(config_file.create(Gio.FileCreateFlags.NONE))
        stream.put_string(config_key_file.to_data()[0])
        stream.close()
