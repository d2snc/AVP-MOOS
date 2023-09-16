from tkinter import *
from PIL import Image, ImageTk
import tkinter
import tkintermapview
import cv2

#Setup da GUI
root = Tk()
root.geometry('1700x1500')
root.title("AVP-MOOS v0.1")
root.configure(bg='#01386a')
root.rowconfigure(0, weight=1) #Configuração para expandir o widget do mapa - Mudar se colocar mais coisa
root.columnconfigure(1, weight=2)

#CV2 para video

# Define a video capture object
vid = cv2.VideoCapture(0) #imagem da webcam
vid = cv2.VideoCapture('teste.mp4') #abre arquivo mp4
  
# Declare the width and height in variables
width, height = 800, 600
  
# Set the width and height
vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
  
  
# Create a label and display it on app
label_widget = Label(root)
label_widget.grid(row=0,column=2,sticky="nsew")
  
# Create a function to open camera and
# display it in the label_widget on app
  
  
def open_camera():
  
    # Capture the video frame by frame
    _, frame = vid.read()
  
    # Convert image from one color space to other
    opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
  
    # Capture the latest frame and transform to image
    captured_image = Image.fromarray(opencv_image)
  
    # Convert captured image to photoimage
    photo_image = ImageTk.PhotoImage(image=captured_image)
  
    # Displaying photoimage in the label
    label_widget.photo_image = photo_image
  
    # Configure image in the label
    label_widget.configure(image=photo_image)
  
    # Repeat the same process after every 10 seconds
    label_widget.after(10, open_camera)
  
  
# Create a button to open the camera in GUI app
button1 = Button(root, text="Abrir Câmera", command=open_camera)
button1.grid(row=1,column=2,sticky="n")



#Configs do menu lateral

min_w = 50 # Minimum width of the frame
max_w = 200 # Maximum width of the frame
cur_width = min_w # Increasing width of the frame
expanded = False # Check if it is completely exanded

def expand():
    global cur_width, expanded
    cur_width += 10 # Increase the width by 10
    rep = root.after(5,expand) # Repeat this func every 5 ms
    frame.config(width=cur_width) # Change the width to new increase width
    if cur_width >= max_w: # If width is greater than maximum width 
        expanded = True # Frame is expended
        root.after_cancel(rep) # Stop repeating the func
        fill()

def contract():
    global cur_width, expanded
    cur_width -= 10 # Reduce the width by 10 
    rep = root.after(5,contract) # Call this func every 5 ms
    frame.config(width=cur_width) # Change the width to new reduced width
    if cur_width <= min_w: # If it is back to normal width
        expanded = False # Frame is not expanded
        root.after_cancel(rep) # Stop repeating the func
        fill()

def fill():
    if expanded: # If the frame is exanded
        # Show a text, and remove the image
        home_b.config(text='Home',image='',font=(0,21))
        set_b.config(text='Settings',image='',font=(0,21))
        ring_b.config(text='Bell Icon',image='',font=(0,21))
    else:
        # Bring the image back
        home_b.config(image=home,font=(0,21))
        set_b.config(image=settings,font=(0,21))
        ring_b.config(image=ring,font=(0,21))

# Define the icons to be shown and resize it
home = ImageTk.PhotoImage(Image.open('home.png').resize((40,40),Image.ANTIALIAS))
settings = ImageTk.PhotoImage(Image.open('settings.png').resize((40,40),Image.ANTIALIAS))
ring = ImageTk.PhotoImage(Image.open('ring.png').resize((40,40),Image.ANTIALIAS))

root.update() # For the width to get updated
frame = Frame(root,bg='#01386a',width=50,height=root.winfo_height())
frame.grid(row=0,column=0,sticky="nsew") 

# Make the buttons with the icons to be shown
home_b = Button(frame,image=home,bg='#01386a',relief='flat',highlightthickness=0)
set_b = Button(frame,image=settings,bg='#01386a',relief='flat',highlightthickness=0)
ring_b = Button(frame,image=ring,bg='#01386a',relief='flat',highlightthickness=0)

# Put them on the frame
home_b.grid(row=0,column=0,pady=10)
set_b.grid(row=1,column=0,pady=50)
ring_b.grid(row=2,column=0)

# Bind to the frame, if entered or left
frame.bind('<Enter>',lambda e: expand())
frame.bind('<Leave>',lambda e: contract())

# So that it does not depend on the widgets inside the frame
frame.grid_propagate(False)

# create map widget
map_widget = tkintermapview.TkinterMapView(root, width=800, height=600, corner_radius=0)
map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
map_widget.grid(row=0,column=1,sticky="nsew",rowspan=3) #Posição na grid do widget do mapa
#map_widget.pack(fill="both", expand=True)
map_widget.set_position(-22.911663710002028, -43.15942144574782)
map_widget.set_zoom(15)
map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")  # sea-map overlay




root.mainloop()