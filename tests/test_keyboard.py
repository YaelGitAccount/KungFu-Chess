from pynput import keyboard
from pynput.keyboard import Key

def on_key_release(key):
    if key == Key.right:
        print("Right key clicked")
    elif key == Key.left:
        print("Left key clicked")
    elif key == Key.up:
        print("Up key clicked")
    elif key == Key.down:
        print("Down key clicked")
    
    elif key == Key.esc:
        exit()
    
    elif key == Key.space:
        print(f"Space key clicked: {key}")    
    elif key == Key.enter:
        print(f"Enter key clicked: {key}")    
    
    elif hasattr(key, 'char'):
        if key.char in ('w', 'W'):
            print("W key clicked")
        elif key.char in ('a', 'A'):
            print("S key clicked")
        elif key.char in ('s', 'S'):
            print("S key clicked")
        elif key.char in ('d', 'D'):
            print("D key clicked")          
                
    


with keyboard.Listener(on_release=on_key_release) as listener:
    listener.join()