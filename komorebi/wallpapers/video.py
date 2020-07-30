import logging

from gi.repository import ClutterGst

from komorebi.wallpapers.base import Wallpaper
from komorebi.settings import ConfigKeys, Settings

video_playback = None
video_content = ClutterGst.Content()


class VideoWallpaper(Wallpaper):
    # Signal
    video_progress_handle = None

    def __init__(self, screen, wallpaper_config):
        global video_playback
        global video_content
        Wallpaper.__init__(self, screen, wallpaper_config)
        logging.debug("Loading VideoWallpaper...")

        path = wallpaper_config.get_string('Info', 'Path')

        if not video_playback:
            video_playback = ClutterGst.Playback()

        video_playback.set_seek_flags(ClutterGst.SeekFlags.ACCURATE)
        video_content.set_player(video_playback)
        self.video_progress_handle = video_playback.connect('notify::progress', self._on_video_progress_event)
        if Settings.mute_playback:
            video_playback.set_audio_volume(0)

        video_file_name = wallpaper_config.get_string('Info', 'VideoFileName')
        if video_file_name is None:
            raise RuntimeError("Wallpaper config doesn't specify video file name")
        video_playback.set_uri(f'file://{path}/{video_file_name}')
        self.play()

        self.signals_setup(screen)

        self.set_content(video_content)
        logging.debug("Loaded VideoWallpaper")

    def on_unload(self):
        logging.debug('Unloading VideoWallpaper...')
        if self.video_progress_handle:
            video_playback.disconnect(self.video_progress_handle)
        self.stop()

    def __del__(self):
        logging.debug('Unloaded VideoWallpaper')

    def signals_setup(self, screen):
        def _on_focus_in_event(_1, _2, self):
            if Settings.pause_playback:
                self.play()
            return False

        def _on_focus_out_event(_1, _2, self):
            if Settings.pause_playback:
                self.pause()
            return False

        # We need the screen as it is the only entity with these focus signals
        screen.connect_weak('focus_in_event', _on_focus_in_event, self)
        screen.connect_weak('focus_out_event', _on_focus_out_event, self)

    def on_settings_changed(self, setting_key):
        if setting_key == ConfigKeys.MUTE_PLAYBACK:
            video_playback.set_audio_volume(0 if Settings.mute_playback else 1)
        elif setting_key == ConfigKeys.PAUSE_PLAYBACK:
            self.pause() if Settings.pause_playback else self.play()
        return False

    def _on_video_progress_event(self, playback, _):
        if playback.get_progress() >= 1.0:
            self.stop()
            self.play()

    def play(self):
        video_playback.set_playing(True)

    def pause(self):
        video_playback.set_playing(False)

    def stop(self):
        self.pause()
        video_playback.set_progress(0.0)
