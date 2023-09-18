import numpy as np
from auvlib.data_tools import jsf_data, utils
from PIL import Image
import pygame
import tkinter as tk
import time
import socket
import cv2


#Dados da conexão UDP

localIP     = "127.0.0.1"

localPort   = 3000

bufferSize  = 1024

# Create a datagram socket

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip

UDPServerSocket.bind((localIP, localPort))






# Constants
width = 512
height = 1000

# Path to the JSF file
path = '/home/douglas/desktop/TCC/SSS/codigos/received_file1.jsf'

# Load jsf data
jsf_pings = jsf_data.jsf_sss_ping.parse_file(path)

# Initialize Pygame
pygame.init()

# Waterfall_img variable
waterfall_img = None

# Display settings
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Waterfall')
i = 500
k = 0
scroll = 0  # Variável para o scroll

# Objects

# Mouse state variables
mouse_down = False
start_pos = None
end_pos = None

# Create an overlay surface for drawing rectangles
overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)

# List to store rectangle positions
rectangles = {}
rectangle_id = 0

# Game loop
while True:

    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    image_data = b""

    image_data += message

    current_img = np.frombuffer(image_data, dtype=np.uint8)
    image = cv2.imdecode(current_img, cv2.IMREAD_COLOR)
    current_img = np.array(image)
    #current_img = np.array(current_img)
    

    
    #current_img = np.array(current_img)  # Pedaço de imagem vinda do ping

    # Adiciono esse pedaço de imagem a um pedaço maior de imagem
    if waterfall_img is None:
        waterfall_img = current_img
    else:
        waterfall_img = np.concatenate((current_img,waterfall_img), axis=0)
        img = Image.fromarray(waterfall_img)
        pygame_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode)    
        screen.blit(pygame_image, (0, i + scroll))
        screen.blit(overlay_surface, (0, i + scroll))
        i += 1    
        

    # Update the main screen
    pygame.display.update()

    # Draw rectangles on the overlay surface
    overlay_surface.fill((0, 0, 0, 0))  # Clear the overlay

    # Draw existing rectangles
    for key in rectangles:
        x1 = rectangles[key][0]
        y1 = rectangles[key][1]
        x2 = rectangles[key][2]
        y2 = rectangles[key][3]

        rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)
        pygame.draw.rect(overlay_surface, (255, 0, 0), rect, 1)
        
        #Update value of rectangle position
        rectangles.update({key:[x1, y1-1, x2, y2-1]})

    # Draw new rectangle
    if start_pos is not None and end_pos is not None:
        rect_x = min(start_pos[0], end_pos[0])
        rect_y = min(start_pos[1], end_pos[1])
        rect_width = abs(end_pos[0] - start_pos[0])
        rect_height = abs(end_pos[1] - start_pos[1])
        #rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
        #pygame.draw.rect(overlay_surface, (255, 0, 0), rect, 1)
        

    # Blit the overlay onto the screen
    screen.blit(overlay_surface, (0, i + scroll))

    pygame.display.flip()  # Update the entire screen

    time.sleep(0.1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_down = True
                start_pos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEMOTION:
            if mouse_down:
                end_pos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                mouse_down = False
                end_pos = pygame.mouse.get_pos()
                # Add the new rectangle position to the dictionary
                rectangles.update({rectangle_id:[start_pos[0], start_pos[1], end_pos[0], end_pos[1]]})
                rectangle_id +=1

        elif event.type == pygame.MOUSEWHEEL:
               print(event)
               print(event.x, event.y)
               print(event.flipped)
               if (event.y > 0):
                scroll += 3
                screen.fill((0,0,0))
                #pygame.display.flip()
               else:
                scroll -= 3
                screen.fill((0,0,0))
                #pygame.display.flip()

pygame.quit()