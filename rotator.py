import ctypes
import time
import math

user32 = ctypes.windll.user32
VK_SPACE = 0x20
VK_ESCAPE = 0x1B

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def set_mouse_pos(x, y):
    user32.SetCursorPos(int(x), int(y))

def click_down():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

def click_up():
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def get_mouse_pos():
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def main():
    print("=== Vinyl Auto Spinner ===")
    print("1. Place your cursor EXACTLY in the center of the app's vinyl.")
    print("2. Press SPACE to start the automatic spin.")
    print("3. Press SPACE again to stop it.")
    print("4. Press ESC to exit the script.")
    print("---------------------------------------------------------")
    
    radius = 50
    rps = 33.3333 / 60.0
    angular_velocity = rps * 2 * math.pi
    
    is_spinning = False
    center_x, center_y = 0, 0
    start_time = 0
    
    # Debounce for space key
    space_was_pressed = False
    
    while True:
        # Exit with ESC
        if user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
            if is_spinning:
                click_up()
            print("Exiting...")
            break
            
        space_pressed = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
        
        # Detect falling edge (when key is pressed)
        if space_pressed and not space_was_pressed:
            if not is_spinning:
                is_spinning = True
                center_x, center_y = get_mouse_pos()
                
                # Move mouse to 50px radius (angle 0)
                set_mouse_pos(center_x + radius, center_y)
                time.sleep(0.05)
                
                # Left click down
                click_down()
                start_time = time.time()
                print("Spinning at 33.33 RPM! Listen to the audio...")
            else:
                is_spinning = False
                click_up()
                print("Spin stopped.")
                
        space_was_pressed = space_pressed
        
        # Update position if spinning
        if is_spinning:
            elapsed = time.time() - start_time
            current_angle = elapsed * angular_velocity
            
            new_x = center_x + radius * math.cos(current_angle)
            new_y = center_y + radius * math.sin(current_angle)
            
            set_mouse_pos(new_x, new_y)
            
        time.sleep(0.01) # Update rate de ~100Hz

if __name__ == "__main__":
    main()