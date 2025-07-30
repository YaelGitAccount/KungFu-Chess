from pynput import keyboard
from queue import Queue, Empty

class KeyboardController:
    def __init__(self):
        self.queue = Queue()
        self.listener = keyboard.Listener(on_release=self.on_release)
        self.listener.start()

        self.key_map = {
            # Player 2 movement (WASD)
            'w': "W",
            'W': "W",
            'a': "A", 
            'A': "A",
            's': "S",
            'S': "S",
            'd': "D",
            'D': "D",
            
            # Hebrew equivalents for WASD
            "'": "W",  # ' -> W
            'ש': "A",  # ש -> A  
            'ד': "S",  # ד -> S
            'ג': "D",  # ג -> D
            
            # Player 1 movement (Arrow keys)
            'up': "MOVE_UP",
            'down': "MOVE_DOWN",
            'left': "MOVE_LEFT",
            'right': "MOVE_RIGHT",
            
            # Player 1 action
            'space': "SPACE",
            'enter': "ENTER",  
            
            # Player 2 action
            'shift': "SHIFT",
            'shift_l': "SHIFT",  # Left shift
            'shift_r': "SHIFT",  # Right shift
            'tab': "TAB",  
            
            # General controls
            'esc': "ESC",
            'q': "QUIT",
        }

    def on_release(self, key):
        try:
            # Try to get character representation first
            if hasattr(key, 'char') and key.char:
                key_char = key.char.lower()
            else:
                # Handle special keys (arrows, space, enter, etc.)
                key_char = str(key).replace('Key.', '').lower()
        except AttributeError:
            # Handle special keys (arrows, space, enter, etc.)
            key_char = str(key).replace('Key.', '').lower()

        if key_char and key_char in self.key_map:
            action = self.key_map[key_char]
            self.queue.put(action)

    def get_action(self) -> str:
        try:
            return self.queue.get_nowait()
        except Empty:
            return None

    def stop(self):
        self.listener.stop()


# keyboard_controller = KeyboardController()
# keyboard_controller.listener.join()