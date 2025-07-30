import pygame
import os

class SoundManager:
    def __init__(self, event_bus):
        pygame.mixer.init()
        self.sounds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sounds")
        self.sounds = {}
        self.channels = {}  # Tracks sound channels
        self.active_sounds = {}  # Active sounds by piece
        self.event_bus = event_bus
        self._load_sounds()
        self._subscribe_to_events()
    
    def _load_sounds(self):
        sound_files = {
            "start_game": "start_game.mp3",
            "move": "move_state.mp3",
            "jump": "jump_state.mp3",
            "capture": "piece_captured.mp3",
            "end_game": "end_game.mp3"
        }

        for sound_name, filename in sound_files.items():
            filepath = os.path.join(self.sounds_dir, filename)
            if os.path.exists(filepath):
                self.sounds[sound_name] = pygame.mixer.Sound(filepath)
    
    def stop_piece_sound(self, piece_id: str):
        # Stop active sound for given piece
        if piece_id in self.active_sounds:
            channel = self.active_sounds[piece_id]
            if channel and channel.get_busy():
                channel.stop()
            del self.active_sounds[piece_id]
    
    def play_sound(self, sound_name: str, piece_id: str = None, loop: bool = False):
        # Play sound, optionally loop and track per piece
        if sound_name not in self.sounds:
            return

        if sound_name == "capture":
            for pid in list(self.active_sounds.keys()):
                self.stop_piece_sound(pid)

        if piece_id:
            self.stop_piece_sound(piece_id)

        channel = pygame.mixer.find_channel()
        if channel:
            if loop:
                channel.play(self.sounds[sound_name], loops=-1)
            else:
                channel.play(self.sounds[sound_name])
            if piece_id:
                self.active_sounds[piece_id] = channel
    
    def on_piece_state_changed(self, data):
        # Stop sound on state change
        piece_id = data.get("piece_id")
        new_state = data.get("state")
        self.stop_piece_sound(piece_id)
        if new_state in ["idle", "long_rest", "short_rest"]:
            pass
    
    def on_piece_moved(self, data):
        # Play move sound in loop
        piece_id = data.get("piece_id")
        self.play_sound("move", piece_id, loop=True)
    
    def on_piece_captured(self, data):
        # Play capture sound and stop all others
        self.play_sound("capture")
    
    def on_piece_jumped(self, data):
        # Play jump sound once
        piece_id = data.get("piece_id")
        self.play_sound("jump", piece_id, loop=False)
    
    def on_game_started(self, data):
        self.play_sound("start_game")
    
    def on_game_ended(self, data):
        self.play_sound("end_game")
    
    def _subscribe_to_events(self):
        # Register event listeners
        self.event_bus.subscribe("game_started", self.on_game_started)
        self.event_bus.subscribe("game_ended", self.on_game_ended)
        self.event_bus.subscribe("game_over", self.on_game_ended)
        self.event_bus.subscribe("piece_captured", self.on_piece_captured)
        self.event_bus.subscribe("piece_moved", self.on_piece_moved)
        self.event_bus.subscribe("piece_jumped", self.on_piece_jumped)
        self.event_bus.subscribe("piece_state_changed", self.on_piece_state_changed)
