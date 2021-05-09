import logging

from gi.repository import Gtk

import komorebi.wallpaper_creator.utilities as utilities
import komorebi.wallpaper_creator.pages as pages

from komorebi.utilities import apply_alpha, apply_css


class WallpaperWindow(Gtk.Window):
    # Main elements
    stack = None
    layout = None

    # Pages
    options_page = None

    # Custom headerbar
    header_bar = None
    close_btn = None
    add_layer_btn = None
    next_btn = None

    # Confirmation popover
    popover = None
    popover_grid = None
    confirmation_lbl = None
    cancel_btn = None
    yes_btn = None

    # Error box
    revealer = None
    info_bar = None
    error_lbl = None

    # CSS definitions
    main_css = """
        *{
            background-color: rgba(0, 0, 0, 0.6);
            box-shadow: none;
            color: white;
            border-width: 0px;
        }
    """

    header_css = """
        *{
            background-color: rgba(0, 0, 0, 0);
            box-shadow: none;
            color: white;
            border-width: 0px;
        }
    """

    def __init__(self):
        logging.debug('Loading WallpaperWindow...')
        Gtk.Window.__init__(self, title='New Komorebi Wallpaper')

        # Initialize elements
        self.stack = Gtk.Stack()
        self.layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.header_bar = Gtk.HeaderBar()
        self.close_btn = Gtk.Button(label='Close')
        self.add_layer_btn = Gtk.Button(label='Add Layer')
        self.next_btn = Gtk.Button(label='Next')

        self.popover = Gtk.Popover()
        self.popover_grid = Gtk.Grid()
        self.confirmation_lbl = Gtk.Label(label='Are you sure?')
        self.cancel_btn = Gtk.Button(label='Cancel')
        self.yes_btn = Gtk.Button(label='Yes')

        self.revealer = Gtk.Revealer()
        self.info_bar = Gtk.InfoBar(message_type=Gtk.MessageType.ERROR)
        self.error_lbl = Gtk.Label()

        # Setup window
        self.set_size_request(1050, 700)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_titlebar(self.header_bar)
        apply_css([self.layout], self.main_css)
        apply_css([self.header_bar], self.header_css)
        apply_alpha([self])

        # Setup widgets
        self.close_btn.set_margin_top(6)
        self.close_btn.set_margin_start(6)
        self.close_btn.set_halign(Gtk.Align.START)

        self.add_layer_btn.set_margin_top(6)
        self.add_layer_btn.set_margin_start(6)
        self.add_layer_btn.set_halign(Gtk.Align.START)

        self.next_btn.set_margin_top(6)
        self.next_btn.set_margin_end(6)

        self.popover.set_relative_to(self.close_btn)

        self.popover_grid.set_margin_top(15)
        self.popover_grid.set_margin_bottom(15)
        self.popover_grid.set_margin_left(15)
        self.popover_grid.set_margin_right(15)
        self.popover_grid.set_row_spacing(20)
        self.popover_grid.set_column_spacing(5)

        self.revealer.set_transition_duration(200)
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)

        self.stack.set_transition_duration(400)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

        # Setup signals
        def _on_close_btn_released(_, self):
            self.popover.show_all()

        def _on_add_layer_btn_released(_, self):
            file_choose_dialog = Gtk.FileChooserDialog(title='Select an image', parent=self,
                                                       action=Gtk.FileChooserAction.OPEN)
            file_choose_dialog.add_buttons(
                'Cancel', Gtk.ResponseType.CANCEL,
                'Accept', Gtk.ResponseType.ACCEPT
            )

            file_filter = Gtk.FileFilter()
            file_filter.add_mime_type('image/*')
            file_choose_dialog.set_filter(file_filter)

            if file_choose_dialog.run() == Gtk.ResponseType.ACCEPT:
                utilities.asset_path = file_choose_dialog.get_file().get_path()
                self.options_page.set_asset(utilities.asset_path)

            file_choose_dialog.close()

        def _on_next_btn_released(_, self):
            current_page = self.stack.get_visible_child_name()

            if current_page == 'initial':
                if (utilities.wallpaper_name is None
                        or (utilities.wallpaper_type == 'image' or utilities.wallpaper_type == 'video')
                        and utilities.file_path is None):
                    self.display_error('Please enter a wallpaper name and choose a file')
                    return True
                elif (utilities.wallpaper_name is None or utilities.wallpaper_type == 'web_page'
                        and utilities.web_page_url is None):
                    self.display_error('Please enter a wallpaper name, a valid URL, and a thumbnail')
                    return True

                self.options_page = pages.OptionsPage()
                self.add_layer_btn.set_visible(utilities.wallpaper_type == 'image')
                if utilities.wallpaper_type == 'image':
                    self.options_page.set_image(utilities.file_path)
                else:
                    self.options_page.set_blank()

                self.stack.add_named(self.options_page, 'options')

                self.options_page.show_all()

                self.stack.set_visible_child_name('options')
                self.revealer.set_reveal_child(False)
            else:
                self.options_page.update_ui()
                self.stack.add_named(pages.FinalPage(), 'final')

                self.show_all()

                self.stack.set_visible_child_name('final')
                self.close_btn.set_visible(False)
                self.next_btn.set_visible(False)
                self.add_layer_btn.set_visible(False)

        def _on_cancel_btn_released(_, self):
            self.popover.hide()

        def _on_yes_btn_released(_):
            Gtk.main_quit()

        def _on_destroy(self):
            Gtk.main_quit()

        self.close_btn.connect('released', _on_close_btn_released, self)
        self.add_layer_btn.connect('released', _on_add_layer_btn_released, self)
        self.next_btn.connect('released', _on_next_btn_released, self)
        self.cancel_btn.connect('released', _on_cancel_btn_released, self)
        self.yes_btn.connect('released', _on_yes_btn_released)
        self.connect('destroy', _on_destroy)

        # Add widgets
        self.header_bar.add(self.close_btn)
        self.header_bar.add(self.add_layer_btn)
        self.header_bar.pack_end(self.next_btn)

        self.popover_grid.attach(self.confirmation_lbl, 0, 0, 1, 1)
        self.popover_grid.attach(self.cancel_btn, 0, 1, 1, 1)
        self.popover_grid.attach(self.yes_btn, 1, 1, 1, 1)

        self.popover.add(self.popover_grid)

        self.info_bar.get_content_area().add(self.error_lbl)
        self.revealer.add(self.info_bar)

        self.stack.add_named(pages.InitialPage(), 'initial')

        self.layout.add(self.revealer)
        self.layout.add(self.stack)

        self.add(self.layout)
        self.add_layer_btn.set_visible(False)

        logging.debug('Loaded WindowWallpaper')

    def display_error(self, error_msg):
        self.error_lbl.set_label(error_msg)
        self.revealer.set_reveal_child(True)
