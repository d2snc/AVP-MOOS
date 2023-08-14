from pyPS4Controller.controller import Controller
from pynput.keyboard import Controller as KeyboardController, Key

# Create an instance of the Keyboard Controller
keyboard = KeyboardController()

# Define a custom controller class
class MyController(Controller):
    def __init__(self, **kwargs):
        Controller.__init__(self, **kwargs)

    def on_L3_right(self, value):
        keyboard.press(Key.right)
        keyboard.release(Key.right)
    
    def on_L3_left(self, value):
        keyboard.press(Key.left)
        keyboard.release(Key.left)

    def on_L3_up(self, value):
        keyboard.press(Key.up)
        keyboard.release(Key.up)

    def on_L3_down(self, value):
        keyboard.press(Key.down)
        keyboard.release(Key.down)




# Create an instance of the custom controller
controller = MyController(interface="/dev/input/js0")

# Start listening for controller events
controller.listen()