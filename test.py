import tkinter as tk

class CustomWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Custom Window")
        self.geometry("200x200")
        self.label = tk.Label(self, text="This is a custom window")
        self.label.pack()

def open_custom_window():
    window = CustomWindow(root)

root = tk.Tk()

button = tk.Button(root, text="Open Custom Window", command=open_custom_window)
button.pack()

root.mainloop()