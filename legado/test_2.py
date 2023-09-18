import numpy as np
from auvlib.data_tools import jsf_data, utils
from PIL import Image
import pygame
import tkinter as tk
import time
import socket
import cv2

class UDPWaterfallViewer:
    def __init__(self, width, height, path):
        self.width = width
        self.height = height
        self.path = path
        self.jsf_pings = None
        self.waterfall_img = None
        self.screen = None
        self.overlay_surface = None
        self.rectangles = {}
        self.rectangle_id = 0

    def run(self):
        self.setup()
        while True:
            self.receive_image_data()
            self.process_image()
            self.update_screen()
            self.handle_events()

    def setup(self):
        self.setup_udp_connection()
        self.load_jsf_data()
        self.initialize_pygame()
        self.initialize_screen()
        self.initialize_overlay_surface()

    def setup_udp_connection(self):
        localIP = "127.0.0.1"
        localPort = 3000
        bufferSize = 1024

        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPServerSocket.bind((localIP, localPort))

    def load_jsf_data(self):
        self.jsf_pings = jsf_data.jsf_sss_ping.parse_file(self.path)

    def initialize_pygame(self):
        pygame.init()

    def initialize_screen(self):
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Waterfall')

    def initialize_overlay_surface(self):
        self.overlay_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def receive_image_data(self):
        bytesAddressPair = self.UDPServerSocket.recvfrom(bufferSize)
        message = bytesAddressPair[0]
        image_data = b""
        image_data += message
        self.current_img = np.frombuffer(image_data, dtype=np.uint8)
        image = cv2.imdecode(self.current_img, cv2.IMREAD_UNCHANGED)
        brilho_aumentado = 50
        imagem_brilho_aumentado = cv2.add(image, brilho_aumentado)
        self.current_img = np.array(imagem_brilho_aumentado)

    def process_image(self):
        if self.waterfall_img is None:
            self.waterfall_img = self.current_img
        else:
            self.waterfall_img = np.concatenate((self.waterfall_img, self.current_img), axis=0)
            img = Image.fromarray(self.waterfall_img)
            pygame_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
            self.screen.blit(pygame_image, (0, self.height + self.scroll))
            self.screen.blit(self.overlay_surface, (0, 0))
            self.height -= 1

    def update_screen(self):
        pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.mouse_down = True
                    self.start_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_down:
                    self.end_pos = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.mouse_down = False
                    self.end_pos = pygame.mouse.get_pos()
                    self.rectangles.update({self.rectangle_id: [self.start_pos[0], self.start_pos[1],
                                                                 self.end_pos[0], self.end_pos[1]]})
                    self.rectangle_id += 1
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.scroll += 3
                    self.screen.fill((0, 0, 0))
                else:
                    self.scroll -= 3
                    self.screen.fill((0, 0, 0))
                pygame.display.flip()
            time.sleep(0.1)

# Constants
width = 512
height = 1000
path = '/home/douglas/desktop/TCC/SSS/codigos/received_file1.jsf'

viewer = UDPWaterfallViewer(width, height, path)
viewer.run()
