import customtkinter
import cv2
import os
import tkinter
import time
import socket
import socket
import pyproj
import pymoos
from collections import deque
from geopy.distance import geodesic as GD
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
#from auvlib.data_tools import jsf_data, utils
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from pyais import decode
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from mission_control import MissionControl
from tkinter import messagebox

#mpl.style.use('seaborn')
plt.style.use('dark_background')

# Configurations to access Moos server

IP_MOOS = "127.0.0.1" # Local
#IP_MOOS = "100.67.139.83" # Vessel's server
#IP_MOOS = "192.168.14.138" # Ekren
#IP_MOOS = "172.18.14.98" # Rasp WIFI
#IP_MOOS = "100.93.183.81" # Raspberry Pi 4 Tailscale
PORTA_MOOS = 9000

#LOCATION = "Salvador"
#LOCATION = "Rio de Janeiro"
#LOCATION = "MIT"
LOCATION = "Morgan City"
"""
xdiff = 
ydiff = 
"""

"""
Thrust limit for changing gear ###
The gear will only be changed if thrust < thrust_gear_limit
"""
thrust_gear_limit = 1
AUTONOMOUS_SPEED = 5 # knots
MAX_AUTONOMOUS_SPEED = 10 # knots
DEGREES_SECONDS = False # GPS notation in Degrees, Minutes, Seconds if True

"""
Variables for Kp, Ki and Kd control
"""
MAX_HEADING_KP = 2
MAX_HEADING_KI = 0.5
MAX_HEADING_KD = 1

MAX_SPEED_KP = 20
MAX_SPEED_KI = 5
MAX_SPEED_KD = 2

INITIAL_KP_VALUE = 0.9
INITIAL_KI_VALUE = 0.0
INITIAL_KD_VALUE = 0.2

CONNECTION_OK_COLOR = "#56a152"
CONNECTION_NOT_OK_COLOR = "#bf7258"

customtkinter.set_default_color_theme("blue")
customtkinter.set_appearance_mode("Dark")

class App(customtkinter.CTk):

    APP_NAME = "AVP-MOOS v0.2"
    WIDTH = 1600
    HEIGHT = 1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)
    
        #Auxiliar para plotagem dos pontos da derrota autonoma
        self.marker_autonomous_list = []

        # Convert Lat Long to minutes and seconds Option
        self.minutes_seconds = DEGREES_SECONDS

        # Create mission controller with Moos
        self.controller = MissionControl(IP_MOOS,PORTA_MOOS,LOCATION)
        
        self.__init_main_variables()
        self.__init_GUI()
        self.__main_loop()
        self.centralize_ship()

    def __init_GUI(self):
        """
        Inits main components of the User interface
        """
        #Carrego imagens para os ícones
        self.current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        #Imagem do meu navio
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red0.png"))
        ship_image = ImageTk.PhotoImage(self.ship_imagefile)

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============
        self.frame_left.grid_rowconfigure(8, weight=1) #Para deixar igualmente espaçados
        self.frame_left.grid_rowconfigure(9, weight=1)
        self.frame_left.grid_rowconfigure(10, weight=1)
        self.frame_left.grid_rowconfigure(11, weight=1)
        self.frame_left.grid_rowconfigure(12, weight=1)
        self.frame_left.grid_rowconfigure(13, weight=1)
        self.frame_left.grid_rowconfigure(14, weight=1)
        self.frame_left.grid_rowconfigure(15, weight=1)
        self.frame_left.grid_rowconfigure(16, weight=1)
        self.frame_left.grid_rowconfigure(17, weight=1)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Put Marker",
                                                command=self.set_marker_event)
        self.button_1.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Clear Markers",
                                                command=self.clear_marker_event)
        self.button_2.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Camera",
                                                command=self.open_camera)
        self.button_3.grid(pady=(20, 0), padx=(20, 20), row=2, column=0)

        self.button_4 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Deactivate Maps",
                                                command=self.destroy_maps)
        self.button_4.grid(pady=(20, 0), padx=(20, 20), row=3, column=0)

        self.button_5 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Remote Control",
                                                command=self.activate_remote_control)
        self.button_5.grid(pady=(20, 0), padx=(20, 20), row=4, column=0)

        self.button_controle_autonomo = customtkinter.CTkButton(master=self.frame_left,
                                                text="Autonomous Control",
                                                command=self.update_autonomous)
        self.button_controle_autonomo.grid(pady=(20, 0), padx=(20, 20), row=5, column=0)

        self.trajectory_button = customtkinter.CTkButton(master=self.frame_left,
                                                text="Trajectory Plot",
                                                command=self.trajectory_plot)
        self.trajectory_button.grid(pady=(20, 0), padx=(20, 20), row=6, column=0)

        #Texto da Latitude

        self.label_lat = customtkinter.CTkLabel(master=self.frame_left, text="Latitude: "+str(self.controller.nav_lat))
        self.label_lat.configure(font=("Segoe UI", 15))
        self.label_lat.grid(row=8, column=0,  padx=(20,20), pady=(50,0), sticky="")

        #Texto da Longitude

        self.label_long = customtkinter.CTkLabel(master=self.frame_left, text="Longitude: "+str(self.controller.nav_long))
        self.label_long.configure(font=("Segoe UI", 15))
        self.label_long.grid(row=9, column=0,  padx=(20,20), pady=(0,20), sticky="")

        #Texto do rumo

        self.label_heading = customtkinter.CTkLabel(master=self.frame_left, text="Heading: "+str(self.controller.nav_heading))
        self.label_heading.configure(font=("Segoe UI", 25))
        self.label_heading.grid(row=10, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Texto da veloc

        self.label_speed = customtkinter.CTkLabel(master=self.frame_left, text=f"Speed: {self.controller.nav_speed:.2f} knots",)
        self.label_speed.configure(font=("Segoe UI", 25))
        self.label_speed.grid(row=11, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Texto do angulo do leme

        self.label_yaw = customtkinter.CTkLabel(master=self.frame_left, text="Rudder Angle: "+str(round(self.controller.nav_yaw,2)))
        self.label_yaw.configure(font=("Segoe UI", 20))
        self.label_yaw.grid(row=12, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Connection Text

        if self.connection_ok:
            self.label_connection = customtkinter.CTkLabel(master=self.frame_left, text=f"Connection: {self.connection_ok}",fg_color=(CONNECTION_OK_COLOR))
        else:
            self.label_connection = customtkinter.CTkLabel(master=self.frame_left, text=f"Connection: {self.connection_ok}",fg_color=(CONNECTION_NOT_OK_COLOR))
        self.label_connection.configure(font=("Segoe UI", 20))
        self.label_connection.grid(row=13, column=0,  padx=(20,20), pady=(20,20), sticky="")
        

        #MAP

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Maps Server:", anchor="w")
        self.map_label.grid(row=14, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=15, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Appearance:", anchor="w")
        self.appearance_mode_label.grid(row=16, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=17, column=0, padx=(20, 20), pady=(10, 20))

        
        # ============ frame_right ============f

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)
        
        #Criação do mapa inicial
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(self.script_directory, "offline_tiles_rio.db")
        #Mapas offline
        #self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        #Mapas online
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        #self.map_widget.set_overlay_tile_server("http://t1.openseamap.org/seamark/{z}/{x}/{y}.png")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Type Address")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        self.botao_centralizar_navio = customtkinter.CTkButton(master=self.frame_right,
                                                text="Centralize Ship",
                                                width=90,
                                                command=self.centralize_ship)
        self.botao_centralizar_navio.grid(row=0, column=2, sticky="w", padx=(12, 0), pady=12)

        #Funções no mapa inicial
        self.map_widget.add_right_click_menu_command(label="Add mine",
                                            command=self.add_mine,
                                            pass_coords=True)
        
        #Ponto de derrota autônoma
        self.map_widget.add_right_click_menu_command(label="Add Autonomous Waypoint",
                                            command=self.add_autonomous_point,
                                            pass_coords=True)
        
        #Varredura sonar
        self.map_widget.add_right_click_menu_command(label="Add Base",
                                            command=self.add_base,
                                            pass_coords=True)

        
        #Safe Lock that Stops All
        self.checkbox = customtkinter.CTkCheckBox(master=self.frame_left, text="DISCONNECT", command=self.stop_all,variable=self.check_var, onvalue="on", offvalue="off")
        self.checkbox.grid(row=18, column=0, padx=(20, 20), pady=(10, 20))

        ###Imagem da camera
        self.vid = cv2.VideoCapture('teste.mp4')
        """
            rtsp_url = 'rtsp://172.18.14.214/axis-media/media.amp' #Para usar na lancha
            self.vid = cv2.VideoCapture(rtsp_url)
            self.camera_width , self.camera_height = 800,600

            # Set the width and height
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        """

        # Create a label and display it on app
        self.text_var = tkinter.StringVar(value="")
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        self.label_widget.grid(row=0,column=2,sticky="nsew",rowspan=1,columnspan=3)

        # Set default values
        self.map_widget.set_position(self.controller.LatOrigin, self.controller.LongOrigin) #Posição inicial do mapa
        self.map_widget.set_zoom(15) 
        #self.map_widget.set_address("Rio de Janeiro")
        self.map_option_menu.set("Google normal")
        self.appearance_mode_optionemenu.set("Dark")

        #Teste de marcadores
        self.marker_1 = self.map_widget.set_marker(self.controller.LatOrigin, self.controller.LongOrigin, text="USV", icon=ship_image, command=self.marker_callback)

    def __init_main_variables(self):
        # Variables for plotting the trajectory
        self.autonomous_points = []
        self.pontos_sonar = []
        self.autonomous_thrust = 0
        self.autonomous_speed = AUTONOMOUS_SPEED  # meters/s
        self.max_autonomous_speed = MAX_AUTONOMOUS_SPEED
        self.visited_points = []
        
        #Variables for control parameters
        self.max_heading_kp = MAX_HEADING_KP
        self.max_heading_ki = MAX_HEADING_KI
        self.max_heading_kd = MAX_HEADING_KD
        self.max_speed_kp = MAX_SPEED_KP
        self.max_speed_ki = MAX_SPEED_KI
        self.max_speed_kd = MAX_SPEED_KD

        #Variável auxiliar para ligar AIS da praticagem
        self.check_var = tkinter.StringVar(self,"off")
        self.check_var_constantheading = tkinter.StringVar(self,"off")

        #Auxilio na plotagem dos AIS
        self.marker_list = []

        #Variáveis auxiliares
        self.mmsi_list = []
        self.markers_ais = {} #Dicionário para colocar os marcadores
        self.markers_image = {} #Dicionário para imagens dos navios AIS
        self.camera_on = False
        self.last_ais_msg = None
        self.manual_control = False
        self.control_activation_counter = 0
        self.view_seglist = None
        self.view_point = None
        self.activate_point_marker = None
        self.station_keep_marker = None
        self.deploy = None
        self.return_var = None
        self.bhv_settings = None #Comportamento ativo no momento
        self.ivphelm_bhv_active = None 
        self.maximum_msg_time = 3 # seconds
        self.connection_ok = True
        self.trajectory_plot_is_toggled = False
        self.autonomous_control = False
        self.make_variables_plot = False
        self.active_animations = []
        self.selected_plot_variables = []

    def __main_loop(self):
        """
        Main functions to run in the loop
        """
        self.update_ship_position()
        self.update_gui()
        self.update_ais_contacts()
        #self.update_station_keep()
        #self.update_lista_praticagem()   
        # 
        self.check_connection()   

    def check_connection(self):
        """
        Checks the last time a messagem was received from MOOS, and if it is greater than the
        maximum defined time, a display is set to show that there is no connection
        """
        try:
            if pymoos.time() - self.controller.last_msg_time > self.maximum_msg_time:
                self.connection_ok = False
            else:
                self.connection_ok = True
        except AttributeError:
            self.connection_ok = False
        print(f"\nConnection is {self.connection_ok}")
        self.after(1000,self.check_connection)

    def trajectory_plot(self):
        """
        Plots the previous trajectory of the vessel
        """
        if len(self.visited_points) > 1:
            if self.trajectory_plot_is_toggled:
                self.trajectory_button.configure(text="Plot Trajectory")
                self.trajectory_plot_is_toggled = False
                self.path_trajectory.delete()
            else:
                self.trajectory_button.configure(text="Remove Trajectory")
                self.trajectory_plot_is_toggled = True
                self.path_trajectory = self.map_widget.set_path(self.visited_points, color='yellow',width=0.5)

    def centralize_ship(self):
        """
        Centers the map on the Ship's location
        """
        self.map_widget.set_position(self.controller.nav_lat,self.controller.nav_long)

    def decimal_degrees_to_dms(self,latitude):
        """
        Converts degrees to degrees, minutes and seconds
        """
        degrees = int(latitude)
        decimal_minutes = (latitude - degrees) * 60
        minutes = int(decimal_minutes)
        seconds = (decimal_minutes - minutes) * 60
        return degrees, minutes, seconds
    
    #Atualiza o station_keep
    def update_station_keep(self):
        if self.bhv_settings is not None and self.ivphelm_bhv_active == "end-station":
            vars_station = self.bhv_settings.split(",") #Divido variáveis
            
            x = float(vars_station[2][2:]) #Pego o valor de x do station keep
            y = float(vars_station[3][2:]) #Pego o valor de y do station keep
            
            #Converto x e y para lat e long
            inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, x-self.diff_x, y-self.diff_y)

            station_keep_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "circle_station_keep.png")).resize((70, 70)))
            
            
            if self.station_keep_marker is None:
                self.station_keep_marker = self.map_widget.set_marker(inv_latitude, inv_longitude, icon=station_keep_image)
            else:
                self.station_keep_marker.set_position(inv_latitude,inv_longitude)
        else:
            if self.station_keep_marker is not None:
                self.station_keep_marker.delete() #Deleto o marker
                self.station_keep_marker = None
                
        self.after(1000,self.update_station_keep)
        
    #Atualiza o ponto ativo no momento
    def update_active_autonomous_point(self):
        if self.view_point is not None:
            data_point = self.view_point.split(",")
            x = float(data_point[0][2:]) #Pego o valor de x do ponto ativo
            y = float(data_point[1][2:]) #Pego o valor de y do ponto ativo

            #Converto x e y para lat e long
            inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, x-self.diff_x, y-self.diff_y)

            #Ploto o marker do ponto ativo
            ponto_ativo_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "hit_marker.png")).resize((70, 70)))
            
            if self.activate_point_marker is None:
                self.activate_point_marker = self.map_widget.set_marker(inv_latitude, inv_longitude, icon=ponto_ativo_image)
            else:
                self.activate_point_marker.set_position(inv_latitude,inv_longitude)
            
            self.after(1000,self.update_active_autonomous_point)

        else:
            print("Variable VIEW_POINT is None \n")

    #Atualiza a derrota autônoma - Executar apenas quando ativar a opção de controle autônomo
    def update_autonomous(self):
        self.create_menu_autonomous()
        if self.view_seglist is not None: #Checa se a lista não está vazia
            #Extrair coordenadas da self.view_seglist
            start_index = self.view_seglist.find("pts={") + len("pts={")
            end_index = self.view_seglist.find("}")
            pts_string = self.view_seglist[start_index:end_index]
            points = pts_string.split(":")

            # Converte os pontos para coordenadas de mapa e armazena
            
            for match in points:
                match = match.split(",")
                #Conversão de coordenadas locais para globais
                #inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, float(match[0])-self.diff_x, float(match[1])-self.diff_y)
                inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, float(match[0]), float(match[1]))
                print(inv_latitude, inv_longitude)
                #Adiciono os pontos na lista
                self.autonomous_points.append((inv_latitude, inv_longitude))

            # Pontos para debug
            print(f"Autonomous Points: {self.autonomous_points}")

            #Defino o caminho
            #self.path_autonomous = self.map_widget.set_path(self.autonomous_points)
            self.path_autonomous.set_position_list(self.autonomous_points)

            #Definindo pontos da derrota como markers
            for ponto in self.autonomous_points:
                #self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.autonomous_points.index(ponto)+1)+" Ponto de derrota autônoma"))
                self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text=f"#{self.autonomous_points.index(ponto)+1} Pt"))
            
        
            # Ploto a derrota no mapa
            #path_1 = self.map_widget.set_path([self.marker_autonomous_list[0].position, self.marker_autonomous_list[1].position, (-43.15947614659043, -22.911947446774985), (-43.15947564792508, -22.908967568090326)])


    def add_autonomous_point(self,coords):
        """
        Adds points for the autonomous navigation trajectory
        """
        print("Adicionar ponto de derrota:", coords)
        #Adiciona ponto na lista de pontos
        self.autonomous_points.append(coords)
        #Defino o caminho
        if len(self.autonomous_points) > 1: #Para não criar o caminho c/ 1 ponto só
            try:
                self.path_autonomous.set_position_list(self.autonomous_points)
            except AttributeError:
                self.path_autonomous = self.map_widget.set_path(self.autonomous_points)

        #Definindo pontos da derrota como markers
        #Só adiciona pontos que não estão na lista
        for ponto in self.autonomous_points:
            if ponto not in self.marker_autonomous_list:
                self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.autonomous_points.index(ponto)+1)+" Autonomous Waypoint"))

    def add_base(self,coords):
        """
        Add a point to be the base of the USV
        """
        self.base_coords = coords
        base_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "home-icon.png")).resize((70, 70)))
        base_marker = self.map_widget.set_marker(coords[0], coords[1], text="USV Base",image=base_image)

    
    def destroy_autonomous(self):
        """
        Destroys the GUI for the autonomous navigation
        """

        self.autonomous_control = False

        #Deleto toda a derrota do mapa
        self.map_widget.delete_all_path()

        #Deleto os pontos do mapa
        for marker in self.marker_autonomous_list:
            marker.delete()
        #Alterar a função do botão
        self.button_controle_autonomo.configure(command=self.update_autonomous,text="Autonomous Control")
        self.slider_progressbar_frame1.destroy()
        self.label_machine1.destroy()
        self.activate_point_marker.destroy()
        
        self.controller.stop_autonomous_navigation()

    def create_menu_autonomous(self):
        """
        Create the GUI Menu for setting the desired autonomous trajectory and speed
        If the desired speed changes the Init button must be hit again
        """
        #Altero o texto do botão

        self.autonomous_control = True

        self.button_controle_autonomo.configure(command=self.destroy_autonomous,text="Deactivate Autonomous Control")

        #Crio o frame com o controle autônomo
        # create slider and progressbar frame
        self.slider_progressbar_frame1 = customtkinter.CTkFrame(self, fg_color="transparent",width=400,height=200)
        self.slider_progressbar_frame1.grid(row=0, column=5, padx=(20, 0), pady=(90, 0), sticky="nsew") #Mexer no pady se quiser abaixar mais o frame
        self.slider_progressbar_frame1.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame1.grid_rowconfigure(24, weight=1)
        
        #Label do Controle Autônomo
        self.label_machine1 = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text="Autonomous Control")
        self.label_machine1.configure(font=("Segoe UI", 30))
        self.label_machine1.grid(row=0, column=0, columnspan=2, padx=(50,50), pady=(10,5), sticky="")

        #Botão para iniciar 
        self.button_inicio_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Start",
                                                command=self.activate_autonomous)
        self.button_inicio_autonomo.grid(pady=(5, 5), padx=(5, 5), row=1, column=0)

        self.button_parada_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Stop",
                                                command=self.stop_autonomous)
        self.button_parada_autonomo.grid(pady=(5, 5), padx=(5, 35), row=1, column=1)

        self.button_parada_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Clear Path",
                                                command=self.clean_autonomous)
        self.button_parada_autonomo.grid(pady=(15, 5), padx=(35, 35), row=2, column=0)
        
        self.button_remove_ultimo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Remove Last Waypoint",
                                                command=self.clean_last_autonomous)
        self.button_remove_ultimo.grid(pady=(15, 5), padx=(35, 60), row=2, column=1)

        self.button_remove_ultimo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Return to the Base",
                                                command=self.return_to_base)
        self.button_remove_ultimo.grid(pady=(15, 5), padx=(60, 60), row=3, column=0)


        # Set desired thrust for autonomous controller

        self.label_desired_thrust = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"Desired Thrust: {float(self.autonomous_thrust)} %")
        self.label_desired_thrust.configure(font=("Segoe UI", 20))
        self.label_desired_thrust.grid(row=4, column=0, columnspan=2, padx=0, pady=(15,5), sticky="")
        
        self.slider_thrust = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, 
                                                    to=100, 
                                                    number_of_steps=200)
        self.slider_thrust.grid(row=5, column=0, columnspan=2, padx=(50, 50), pady=(15, 5), sticky="ew")
        self.slider_thrust.configure(command=self.update_desired_thrust)
        self.slider_thrust.set(self.autonomous_thrust)

        self.speed_progressbar = customtkinter.CTkProgressBar(master=self.slider_progressbar_frame1,width=300)
        self.speed_progressbar.grid(row=6, column=0, columnspan=2, padx=(50, 50), pady=(15, 15), sticky="ew")
        self.speed_progressbar.set(self.controller.desired_thrust/100)

        # Set option for Plotting Variables

        self.button_plot_variables = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Plot Variables",
                                                command=self.toggle_plot_variables)
        self.button_plot_variables.grid(pady=(5, 5), padx=(5, 5), row=7, column=0)        

        # Creates a listbox for selecting multiple variables to plot
        self.listbox_selection = ('RUDDER PLOT',
                                  'HEADING PLOT',
                                  'SPEED PLOT',
                                  'DEPTH PLOT')

        var = tkinter.Variable(value=self.listbox_selection)
        # selecmode can be MULTIPLE, SINGLE
        self.select_list = tkinter.Listbox(master=self.slider_progressbar_frame1,
                                           listvariable=var,
                                           height=len(self.listbox_selection),
                                           selectmode=tkinter.SINGLE)
        self.select_list.configure(background="#265aad",foreground="white",font=("Segoe UI", 10))
        self.select_list.grid(pady=(5, 5), padx=(5, 5), row=8, column=1)

        # Binds the variables chosen to an action 
        self.select_list.bind('<<ListboxSelect>>', self.items_selected) 
        
        #Heading automático
        self.checkbox_heading = customtkinter.CTkCheckBox(master=self.slider_progressbar_frame1, text="Constant Heading", variable=self.check_var_constantheading, onvalue="on", offvalue="off")
        self.checkbox_heading.grid(row=9, column=0, columnspan=2, padx=(20, 20), pady=(5, 5))
        self.checkbox_heading.configure(command=self.update_auto_heading)
        
        self.label_setpoint_heading = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"Heading: {round(float(self.controller.setpoint_heading),2)}")
        self.label_setpoint_heading.configure(font=("Segoe UI", 20))
        self.label_setpoint_heading.grid(row=10, column=0, columnspan=2, padx=(10,0), pady=(0,5), sticky="")

        self.slider_setpoint_heading = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=360, number_of_steps=360)
        self.slider_setpoint_heading.grid(row=11, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="ew")
        self.slider_setpoint_heading.configure(command=self.update_setpoint_heading)
        self.slider_setpoint_heading.set(self.controller.heading_kp)
        
        #Parâmetros do controle PID
        #Label de cima
        self.label_machine1 = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text="PID Heading Control")
        self.label_machine1.configure(font=("Segoe UI", 25))
        self.label_machine1.grid(row=12, column=0, columnspan=2, padx=(10,20), pady=(10,5), sticky="n")
        
        self.label_heading_kp = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KP: {self.controller.heading_kp:.2f}")
        self.label_heading_kp.configure(font=("Segoe UI", 20))
        self.label_heading_kp.grid(row=13, column=0, columnspan=2, padx=(10,0), pady=(0,5), sticky="n")
        
        self.slider_heading_kp = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_heading_kp, number_of_steps=200)
        self.slider_heading_kp.grid(row=14, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        self.slider_heading_kp.configure(command=self.update_heading_kp)
        self.slider_heading_kp.set(self.controller.heading_kp)
        
        self.label_heading_ki = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KI: {round(float(self.controller.heading_ki),2)}")
        self.label_heading_ki.configure(font=("Segoe UI", 20))
        self.label_heading_ki.grid(row=15, column=0, columnspan=2, padx=0, pady=(5,5), sticky="")
        
        self.slider_heading_ki = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_heading_ki, number_of_steps=200)
        self.slider_heading_ki.grid(row=16, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        self.slider_heading_ki.configure(command=self.update_heading_ki)
        self.slider_heading_ki.set(self.controller.heading_ki)
        
        self.label_heading_kd = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KD: {round(float(self.controller.heading_kd),2)}")
        self.label_heading_kd.configure(font=("Segoe UI", 20))
        self.label_heading_kd.grid(row=17, column=0, columnspan=2, padx=0, pady=(5,5), sticky="")
        
        self.slider_heading_kd = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_heading_kd, number_of_steps=200)
        self.slider_heading_kd.grid(row=18, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        self.slider_heading_kd.configure(command=self.update_heading_kd)
        self.slider_heading_kd.set(self.controller.heading_kd)

        #Update the values for the PID Control for initial values for the USV
        
        #Initial values for the PID Control
        self.controller.notify('HEADING_KP',INITIAL_KP_VALUE,pymoos.time())

        #Update label
        self.label_heading_kp.configure(text=f"KP: {INITIAL_KP_VALUE:.3f}")

        #Envio para o MOOS o valor da variável
        self.controller.notify('HEADING_KI',INITIAL_KI_VALUE,pymoos.time())

        #Update da label
        self.label_heading_ki.configure(text=f"KI: {INITIAL_KI_VALUE:.3f}")

        #Envio para o MOOS o valor da variável
        self.controller.notify('HEADING_KD',INITIAL_KD_VALUE,pymoos.time())
        
        #Update da label
        self.label_heading_kd.configure(text=f"KD: {INITIAL_KD_VALUE:.3f}")
        
        #self.label_machine1 = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text="Controle PID Speed")
        #self.label_machine1.configure(font=("Segoe UI", 25))
        #self.label_machine1.grid(row=17, column=0, columnspan=2, padx=(10,20), pady=(5,5), sticky="n")
        
        #self.label_speed_kp = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KP: {round(float(self.controller.speed_kp),2)}")
        #self.label_speed_kp.configure(font=("Segoe UI", 20))
        #self.label_speed_kp.grid(row=18, column=0, columnspan=2, padx=(10,0), pady=(0,5), sticky="n")
        
        #self.slider_speed_kp = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_speed_kp, number_of_steps=200)
        #self.slider_speed_kp.grid(row=19, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        #self.slider_speed_kp.configure(command=self.update_speed_kp)
        #self.slider_speed_kp.set(self.controller.speed_kp)
        
        #self.label_speed_ki = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KI: {round(float(self.controller.speed_ki),2)}")
        #self.label_speed_ki.configure(font=("Segoe UI", 20))
        #self.label_speed_ki.grid(row=20, column=0, columnspan=2, padx=0, pady=(5,5), sticky="")
        
        #self.slider_speed_ki = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_speed_ki, number_of_steps=200)
        #self.slider_speed_ki.grid(row=21, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        #self.slider_speed_ki.configure(command=self.update_speed_ki)
        #self.slider_speed_ki.set(self.controller.speed_ki)
        
        #self.label_speed_kd = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text=f"KD: {round(float(self.controller.speed_kd),2)}")
        #self.label_speed_kd.configure(font=("Segoe UI", 20))
        #self.label_speed_kd.grid(row=22, column=0, columnspan=2, padx=0, pady=(5,5), sticky="")
        
        #self.slider_speed_kd = customtkinter.CTkSlider(self.slider_progressbar_frame1, from_=0, to=self.max_speed_kd, number_of_steps=200)
        #self.slider_speed_kd.grid(row=23, column=0, columnspan=2, padx=0, pady=(5, 5), sticky="")
        #self.slider_speed_kd.configure(command=self.update_speed_kd)
        #self.slider_speed_kd.set(self.controller.speed_kd)
        
    def toggle_plot_variables(self):
        """
        Check if USER asked to plot variables
        """
        if self.make_variables_plot: # End plot
            self.button_plot_variables.configure(text=f"Plot Variables")
            self.make_variables_plot = False
            for animation in self.active_animations:
                animation.pause()
                plt.close()
                self.active_animations = []
        else: # Start plot
            if len(self.selected_plot_variables) > 0:
                self.make_variables_plot = True
                self.button_plot_variables.configure(text=f"Close Plot Variables")
                if len(self.active_animations) > 0:
                    for animation in self.active_animations:
                        animation.resume()
                else:
                    for plot_type in self.selected_plot_variables:
                        self.plot_variables(plot_type=plot_type)

    def items_selected(self, event):
        """
        Updates the selected variables to plot from the list
        """
        selected_indices = self.select_list.curselection()
        self.selected_plot_variables = [self.listbox_selection[i] for i in selected_indices]
        print(self.selected_plot_variables)

    def plot_variables(self, plot_type):
        """
        Plot Two Variables: var_des, intended for desired control variables
                            var_nav, the real value for the vessel
        """    # Clear the previous plot and plot the updated data
        MAXLEN = 100 # maximum stored values in the queue
        ALPHA = 0.1 # transparency of plot
        LINEWIDTH = 1 # line width of plot
        PLOT_INTERVAL = 200 # ms
        def animate_heading(i,heading_x_data,
                            heading_y_des_data,
                            heading_y_nav_data,
                            heading_y_out_data):
            x = time.time() - heading_init_time
            nav = self.controller.nav_heading
            if (self.controller.constant_heading == True) or (self.check_var_constantheading.get() == "on"):
                des = self.controller.setpoint_heading
            else:
                des = self.controller.desired_heading
            out = self.controller.desired_rudder

            heading_x_data.append(x)
            heading_y_des_data.append(des)
            heading_y_nav_data.append(nav)
            heading_y_out_data.append(out)

            plt.cla()
            axu.clear()
            axd.clear()
            axu.plot(heading_x_data, heading_y_nav_data,label="NAV_HEADING")
            axu.plot(heading_x_data, heading_y_des_data,label="DESIRED_HEADING")
            axd.set_xlabel('Time [s]')
            axu.set_ylabel('Value [°]')
            axu.set_ylim([0,365])
            axu.legend()

            axd.plot(heading_x_data, heading_y_out_data,label="PID OUTPUT")
            axd.set_ylabel('Value [°]')
            axd.set_ylim([-40,40])
            axd.legend()
            axu.set_title('Real-time Heading Plot')
            axd.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            axu.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            plt.tight_layout()

        def animate_rudder(i):
            x = time.time() - rudder_init_time
            nav = self.controller.nav_yaw
            des = self.controller.desired_rudder

            rudder_x_data.append(x)
            rudder_y_des_data.append(des)
            rudder_y_nav_data.append(nav)
            plt.cla()
            plt.plot(rudder_x_data, rudder_y_nav_data,label="NAV_RUDDER")
            plt.plot(rudder_x_data, rudder_y_des_data,label="DESIRED_RUDDER")
            plt.xlabel('Time [s]')
            plt.ylabel('Value [°]')
            plt.ylim([-45,45])
            plt.legend()
            plt.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            plt.title('Real-time Rudder Plot')

        def animate_speed(i,speed_x_data,
                            speed_y_des_data,
                            speed_y_nav_data,
                            speed_y_out_data):
            x = time.time() - speed_init_time
            nav = self.controller.nav_speed
            des = self.controller.desired_speed
            out = self.controller.desired_thrust

            speed_x_data.append(x)
            speed_y_des_data.append(des)
            speed_y_nav_data.append(nav)
            speed_y_out_data.append(out)

            plt.cla()
            axu.clear()
            axd.clear()
            axu.plot(speed_x_data, speed_y_nav_data,label="NAV_SPEED")
            axu.plot(speed_x_data, speed_y_des_data,label="DESIRED_SPEED")
            axu.set_ylabel('Value [knots]')
            axu.set_ylim([0,10])
            axu.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            axu.legend()

            axd.set_xlabel('Time [s]')
            axd.plot(speed_x_data, speed_y_out_data,label="PID OUTPUT")
            axd.set_ylabel('Value %')
            axd.set_ylim([0,100])
            axd.legend()
            axd.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            axu.set_title('Real-time Speed Plot')

        def animate_depth(i):
            x = time.time() - depth_init_time
            nav = self.controller.nav_depth

            depth_x_data.append(x)
            depth_y_nav_data.append(nav)
            plt.cla()
            plt.plot(depth_x_data, depth_y_nav_data,label="NAV_DEPTH")
            plt.xlabel('Time [s]')
            plt.ylabel('Value [m]')
            plt.legend()
            plt.grid(alpha=ALPHA,linewidth=LINEWIDTH)
            plt.title('Real-time Depth Plot')

        if plot_type == "RUDDER PLOT":
            print("\nMaking RUDDER PLOT\n")
            rudder_x_data = deque(maxlen=MAXLEN)
            rudder_y_des_data = deque(maxlen=MAXLEN)
            rudder_y_nav_data = deque(maxlen=MAXLEN)
            rudder_fig, ax = plt.subplots()
            rudder_init_time = time.time()
            self.rudder_plot_animation = FuncAnimation(rudder_fig, animate_rudder, interval=PLOT_INTERVAL)
            self.active_animations.append(self.rudder_plot_animation)
            plt.show()

        elif plot_type == "SPEED PLOT":
            print("\nMaking SPEED PLOT\n")
            speed_x_data = deque(maxlen=MAXLEN)
            speed_y_des_data = deque(maxlen=MAXLEN)
            speed_y_nav_data = deque(maxlen=MAXLEN)
            speed_y_out_data = deque(maxlen=MAXLEN)
            speed_fig, (axu,axd) = plt.subplots(nrows=2,sharex=True)
            speed_init_time = time.time()
            self.speed_plot_animation = FuncAnimation(speed_fig, animate_speed, fargs=(speed_x_data,
                                                                                             speed_y_des_data,
                                                                                             speed_y_nav_data,
                                                                                             speed_y_out_data),interval=PLOT_INTERVAL)
            self.active_animations.append(self.speed_plot_animation)
            plt.show()

        elif plot_type == "HEADING PLOT":
            print("\nMaking HEADING PLOT\n")
            heading_x_data = deque(maxlen=MAXLEN)
            heading_y_des_data = deque(maxlen=MAXLEN)
            heading_y_nav_data = deque(maxlen=MAXLEN)
            heading_y_out_data = deque(maxlen=MAXLEN)
            heading_fig, (axu,axd) = plt.subplots(nrows=2,sharex=True)
            heading_init_time = time.time()
            self.heading_plot_animation = FuncAnimation(heading_fig, animate_heading, fargs=(heading_x_data,
                                                                                             heading_y_des_data,
                                                                                             heading_y_nav_data,
                                                                                             heading_y_out_data),interval=PLOT_INTERVAL)
            self.active_animations.append(self.heading_plot_animation)
            plt.show()

        elif plot_type == "DEPTH PLOT":
            print("\nMaking DEPTH PLOT\n")
            depth_x_data = deque(maxlen=MAXLEN)
            depth_y_nav_data = deque(maxlen=MAXLEN)
            depth_fig, ax = plt.subplots()
            depth_init_time = time.time()
            self.depth_plot_animation = FuncAnimation(depth_fig, animate_depth, interval=PLOT_INTERVAL)
            self.active_animations.append(self.depth_plot_animation)
            plt.show()

    #TODO
    def update_desired_thrust(self,_):
        """
        Updates GUI of desired thrust in the autonomous menu and notifies the controller
        of the new desired thrust for the autonomous path
        """
        #Only sends if Stop is not pressed
        if self.autonomous_control == True:
            desired_thrust = self.slider_thrust.get()
            self.autonomous_thrust = desired_thrust
            #TODO ver se vai fazer funcionar só mandar a velocidade fixa
            self.controller.notify_thruster(desired_thrust)
            self.label_desired_thrust.configure(text=f"Desired Thrust: {self.autonomous_thrust} %")
        else:
            pass

    def update_heading_kp(self,value):
        """
        Updates kp value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('HEADING_KP',value,pymoos.time())
        
        #Update da label
        self.label_heading_kp.configure(text=f"KP: {self.controller.heading_kp:.3f}")
        
    def update_heading_ki(self,value):
        """
        Updates ki value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('HEADING_KI',value,pymoos.time())
        
        #Update da label
        self.label_heading_ki.configure(text=f"KI: {self.controller.heading_ki:.3f}")
        
    def update_heading_kd(self,value):
        """
        Updates kd value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('HEADING_KD',value,pymoos.time())
        
        #Update da label
        self.label_heading_kd.configure(text=f"KD: {self.controller.heading_kd:.3f}")
    
    def update_speed_kp(self,value):
        """
        Updates kp value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('SPEED_KP',value,pymoos.time())
        
        #Update da label
        self.label_speed_kp.configure(text=f"KP: {self.controller.speed_kp:.2f}")
        
    def update_speed_ki(self,value):
        """
        Updates ki value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('SPEED_KI',value,pymoos.time())
        
        #Update da label
        self.label_speed_ki.configure(text=f"KI: {self.controller.speed_ki:.2f}")
        
    def update_speed_kd(self,value):
        """
        Updates kd value in the control
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('SPEED_KD',value,pymoos.time())
        
        #Update da label
        self.label_speed_kd.configure(text=f"KD: {self.controller.speed_kd:.2f}")
        
    def update_setpoint_heading(self,value):
        """
        Updates setpoint heading value in the control (Constant Heading)
        """
        #Envio para o MOOS o valor da variável
        self.controller.notify('SETPOINT_HEADING',value,pymoos.time())
        
        #Update da label
        self.label_setpoint_heading.configure(text=f"Rumo: {self.controller.setpoint_heading:.2f}")
        
    def update_auto_heading(self):
        if self.check_var_constantheading.get() == "on":
            #Liguei o botão do heading constante, seto a variável para true no MOOS
            #Envio para o MOOS o valor da variável
            print("constant heading botton on")
            self.controller.notify('CONSTANT_HEADING','true',pymoos.time())
        else:
            self.controller.notify('CONSTANT_HEADING','false',pymoos.time())
            
    def activate_autonomous(self): 
        """
        Starts autonomous navigation and notifies MOOS
        """
        #Set variable for autonomous control for True
        self.autonomous_control = True
        self.controller.set_navigation_path(self.autonomous_points, self.autonomous_speed)
        self.update_active_autonomous_point()


    def stop_autonomous(self):
        """
        Stop the autonomous control without activating Station-Keep
        """
        #Set variable for autonomous control for false
        self.autonomous_control = False

        #Update values in the desired_thrust slider
        self.slider_thrust.set(0)
        self.speed_progressbar.set(0)
        self.autonomous_thrust = 0
        self.label_desired_thrust.configure(text=f"Desired Thrust: {self.autonomous_thrust} %")

        #Stops everything
        self.controller.stop_autonomous_navigation()
        self.controller.emergency_stop()

        
        
    def clean_last_autonomous(self):
        """
        Clean last added autonomous path point
        """
        
        # Delete all path
        #self.map_widget.delete_all_path()
        self.path_autonomous.delete()

        # Delete markers
        for marker in self.marker_autonomous_list:
            marker.delete()
        self.autonomous_points.pop() # Remove last point from the list
        self.marker_autonomous_list.pop() # Remove icon from list
        
        # Set path
        #self.path_autonomous = self.map_widget.set_path(self.pontos_autonomos)
        self.path_autonomous.set_position_list(self.autonomous_points)
        
        for ponto in self.autonomous_points:
            self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.autonomous_points.index(ponto)+1)+" Autonomous Waypoint"))
    
    def clean_autonomous(self):
        """
        Clean the current Autonomous Path from the map
        """

        # Delete created path
        #self.map_widget.delete_all_path()
        self.path_autonomous.delete()

        # Remove points from the list
        for marker in self.marker_autonomous_list:
            marker.delete()

        # Clean list
        self.autonomous_points = []

    def return_to_base(self):
        """
        Return to a base selected by the user
        """
        local_points = self.controller.convert_global2local(self.base_coords)
        formatted_points = [f"{x},{y}" for x, y in local_points]
        result = " : ".join(formatted_points)
        #Atualiza o ponto de retorno
        self.controller.notify('RETURN_UPDATE',f"points={result}",pymoos.time())
        #Envia a variável de retorno 
        self.controller.notify('RETURN','true',pymoos.time())


    ###################################################
    ### End of Functions for the Autonomous Control ###
    ###################################################

    def stop_all(self):

        if self.check_var.get() == "off":
            self.controller.notify('DEPLOY', 'true', pymoos.time())
        else:
            # Show confirmation popup
            response = messagebox.askyesno("Confirm Action", "Do you really want to disconnect?")

            if response:  # If "Yes" is clicked
                self.check_var.set("on")  # Update checkbox state (optional)
                self.controller.notify('DESIRED_GEAR', "N", pymoos.time())
                self.controller.notify('DESIRED_RUDDER', 0, pymoos.time())
                self.controller.notify('DESIRED_THRUST', 0, pymoos.time())

                self.controller.notify('DEPLOY', 'false', pymoos.time())
                self.controller.notify('MOOS_MANUAL_OVERIDE', 'false', pymoos.time())
            else:  # If "No" is clicked
                self.check_var.set("off")
                pass #Do nothin


    def update_lista_praticagem(self): 
        #Atualiza a lista de ctts AIS q vem da praticagem - Lembrar sempre de executar funções no final do programa
        if self.check_var.get() == "on":
            global sock
            sock.settimeout(0.0)  # modo não-bloqueante
            try:
                data = sock.recv(1024)
                # processa dados...
            except BlockingIOError:
                # não tinha nada pra ler, segue a vida...
                pass

            print("Received:", data.decode())
            mensagens_ais = data.decode().split('\r\n')
            #Create a marker for each ais message
            if (self.map_widget.winfo_exists() == 1): #Verifica se o mapa existe
                for msg in mensagens_ais:
                    decoded_msg = self.decode_ais_msg(msg) #Decodifico a msg
                    if decoded_msg is not None and hasattr(decoded_msg, 'heading') and decoded_msg.mmsi not in self.mmsi_list: #Caso não esteja na lista
                        self.mmsi_list.append(decoded_msg.mmsi) #Adiciono na lista
                        #Crio o marker
                        if int(decoded_msg.heading) > 360: 
                            decoded_msg.heading = int(decoded_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                        self.markers_image[decoded_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(decoded_msg.heading))+".png"))
                        ship_image = ImageTk.PhotoImage(self.markers_image[decoded_msg.mmsi])
                        self.markers_ais[decoded_msg.mmsi] = self.map_widget.set_marker(decoded_msg.lat, decoded_msg.lon, text="Contato_"+str(decoded_msg.mmsi), icon=ship_image, command=self.marker_callback)
                    elif hasattr(decoded_msg, 'heading') and decoded_msg is not None: #Caso já esteja na lista o navio
                        #Atualizo o marcador
                        self.markers_ais[decoded_msg.mmsi].set_position(decoded_msg.lat,decoded_msg.lon)
                        if int(decoded_msg.heading) > 360: 
                            decoded_msg.heading = int(decoded_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                        self.markers_image[decoded_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(decoded_msg.heading))+".png"))
                        ship_image = ImageTk.PhotoImage(self.markers_image[decoded_msg.mmsi])
                        self.markers_ais[decoded_msg.mmsi].change_icon(ship_image)
        else:
            pass


        self.after(1000,self.update_lista_praticagem) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa

    def add_mine(self,coords):
        """
        Add a Mine location in the Map
        """
        mina_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "mine.png")).resize((70, 70)))
        print("Adicionar Possível Mina:", coords)
        mina_marker = self.map_widget.set_marker(coords[0], coords[1], text="Possível mina",image=mina_image)
    
    def receive_sonar(self):
        """
        Plots the received image from the Side scan Sonar into the Map
        """
        self.pontos_sonar.append((self.controller.nav_lat-0.0001,self.controller.nav_long-0.0001))
        if (len(self.pontos_sonar) > 1):
            self.path_trajectory = self.map_widget.set_path(self.pontos_sonar)
                
        
        self.after(1000,self.receive_sonar) #A cada 0,1 segundo ele vai receber posição sonar  

    # TODO Adicionar função que ao clicar em um contato AIS abra um pop-up mostrando informações do navio
    # TODO Adicionar função no botão da AIS praticagem para remover todos os contatos da tela quando apertar no botão

    @staticmethod
    def decode_ais_msg(ais_msg):
        """
        Decode AIS messages
        """
        ais_msg = ais_msg.encode()
        #Catch errors and let them pass
        try:
            ais_msg = decode(ais_msg)
        except:
            ais_msg = None #Por enquanto vou retornar None caso esteja com erro
            pass
        return ais_msg
        
    def update_ais_contacts(self):
        """
        Updates AIS messages
        """
        #Decodifico a msg AIS
        if self.last_ais_msg is not None:
            ais_msg = self.last_ais_msg
            self.last_ais_msg = self.decode_ais_msg(ais_msg) 

        #Crio o marker no mapa
        if (self.map_widget.winfo_exists() == 1): #Verifica se o mapa existe
            if self.last_ais_msg is not None and self.last_ais_msg.mmsi not in self.mmsi_list: #Verifica se o mmsi já não está na lista
                #Adiciono código mmsi a lista
                self.mmsi_list.append(self.last_ais_msg.mmsi)
                #Imagem do marcador - coloquei isso pq alguns vinham maior q 360
                if int(self.last_ais_msg.heading) > 360: 
                    self.last_ais_msg.heading = int(self.last_ais_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                self.markers_image[self.last_ais_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(self.last_ais_msg.heading))+".png"))
                ship_image = ImageTk.PhotoImage(self.markers_image[self.last_ais_msg.mmsi])
                
                #Crio o marcador 
                self.markers_ais[self.last_ais_msg.mmsi] = self.map_widget.set_marker(self.last_ais_msg.lat, self.last_ais_msg.lon, text="Contato_"+str(self.last_ais_msg.mmsi), icon=ship_image, command=self.marker_callback)
                
            elif self.last_ais_msg is not None: #Caso o navio já esteja na lista
                #Atualizo a posição do marcador
                self.markers_ais[self.last_ais_msg.mmsi].set_position(self.last_ais_msg.lat,self.last_ais_msg.lon)
                #Atualizo a imagem do marcador
                if int(self.last_ais_msg.heading) > 360: 
                    self.last_ais_msg.heading = int(self.last_ais_msg.heading) - 360 #Corrige o ângulo do navio caso seja maior q 360
                self.markers_image[self.last_ais_msg.mmsi] = Image.open(os.path.join(self.current_path, "images", "ship_green"+str(int(self.last_ais_msg.heading))+".png"))
                ship_image = ImageTk.PhotoImage(self.markers_image[self.last_ais_msg.mmsi])
                self.markers_ais[self.last_ais_msg.mmsi].change_icon(ship_image)
        self.after(1000,self.update_ais_contacts) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa

    def update_gui(self):
        """
        Updates the Ship's data in the GUI
        """
        if self.minutes_seconds:
            degrees, minutes, seconds = self.decimal_degrees_to_dms(self.controller.nav_lat)
            self.label_lat.configure(text=f"Latitude: {degrees}° {minutes}' {seconds:.2f}\"")
            degrees, minutes, seconds = self.decimal_degrees_to_dms(self.controller.nav_long)
            self.label_long.configure(text=f"Longitude: {degrees}° {minutes}' {seconds:.2f}\"")

        else:
            self.label_lat.configure(text=f"Latitude: {self.controller.nav_lat:.6f}")
            self.label_long.configure(text=f"Longitude: {self.controller.nav_long:.6f}")

        self.label_heading.configure(text="Heading: "+str(int(self.controller.nav_heading))+" °")
        self.label_speed.configure(text=f"Speed: {self.controller.nav_speed:.2f} knots")
        self.label_yaw.configure(text="Rudder Angle: "+str(round(self.controller.nav_yaw,2)))
        if self.connection_ok:
            self.label_connection.configure(text=f"Connection: {self.connection_ok}",fg_color=(CONNECTION_OK_COLOR))
        else:
            self.label_connection.configure(text=f"Connection: {self.connection_ok}",fg_color=(CONNECTION_NOT_OK_COLOR))

        if self.manual_control:
            rudder_progress_value = ((self.controller.nav_yaw + 40)*1.25)/100
            self.rudder_progressbar.set(rudder_progress_value)

        if self.autonomous_control:
            self.speed_progressbar.set(self.controller.nav_speed/self.max_autonomous_speed)

        # Configure time to re-update GUI
        self.after(1000,self.update_gui) # 1sec

    def add_visited_point(self):
        """
        Update the ship's visited points if the distance between the current and last point
        is greater than a threshold
        """
        points = (self.controller.nav_lat,self.controller.nav_long)
        if len(self.visited_points) > 0:
            dist = GD(points,tuple(self.last_loc_global)).km 
            if dist > 0.02: # 50 meters
                #xy = self.controller.convert_global2local((self.controller.nav_lat,self.controller.nav_long))[0]
                self.visited_points.append(points)
                self.last_loc_global = points
                if self.trajectory_plot_is_toggled:
                    self.path_trajectory.set_position_list(self.visited_points)

                #self.marker_trajectory_list.append(self.map_widget.set_marker(xy[0], xy[1], text="#"+str(self.visited_points.index(xy)+1)+"Local visitado"))
        else:
            #xy = self.controller.convert_global2local([self.controller.nav_lat,self.controller.nav_long])[0]
            self.visited_points.append(points)
            self.last_loc_global = points

            #self.marker_trajectory_list.append(self.map_widget.set_marker(xy[0], xy[1], text="#"+str(self.visited_points.index(xy)+1)+"Local visitado"))       

    #Função em loop utilizada para atualizar a posição do meu navio
    def update_ship_position(self):
        if (self.map_widget.winfo_exists() == 1): #Checa se existe o mapa 
            # correção da posição para o mapa
            #self.marker_1.set_position(self.controller.nav_lat-0.0001,self.controller.nav_long-0.0001) #Ajustar os valores para ter uma melhor posição do navio
            self.marker_1.set_position(self.controller.nav_lat,self.controller.nav_long)

            #self.map_widget.set_position(self.nav_lat,self.nav_long) #Centraliza o mapa no navio, colocar uma opção para ativar ela 
            #self.map_widget.set_zoom(15)
            self.label_widget.configure(text=str(self.controller.nav_lat)+" "+str(self.controller.nav_long))

            #Atualiza a imagem do navio de acordo com o ângulo self.nav_heading
            self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.controller.nav_heading))+".png"))
            ship_image = ImageTk.PhotoImage(self.ship_imagefile)
            self.marker_1.change_icon(ship_image)

            self.add_visited_point()

        else:
            print("Mapa inativo")

        self.after(1000,self.update_ship_position) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa

    #Funções da GUI abaixo

    def marker_callback(self,marker): #O que acontece quando clica no marker
        print(marker.text)

    #################################################
    ### Begin of functions for the Remote Control ###
    #################################################

    def destroy_control(self): 
        """
        Destroys the GUI for autonomous control
        """
        self.button_5.configure(command=self.activate_remote_control,text="Remote Control")
        self.slider_progressbar_frame.destroy()
        self.label_machine.destroy()
        self.label_rudder_value.destroy()
        self.label_rudder.destroy()
        self.label_gear.destroy()
        self.label_control.destroy()
        self.rudder_progressbar.destroy()
        self.thrust_progressbar.destroy()
        self.slider_rudder.destroy()
        self.thrust_slider.destroy()
        self.gear_slider.destroy()
        self.label_gear_value.destroy()

        self.controller.stop_autonomous_navigation()
        self.manual_control = False
        
    def activate_remote_control(self): 
        """
        Creates the GUI of Remote Control
        Sends configurations for manual control to Moos-IvP
        """
        
        self.controller.activate_remote_control()
        self.manual_control = True
            
        self.button_5.configure(command=self.destroy_control,text="Deactivate Remote Control")
        #Frame com slider para controle de velocidade   

        # create slider and progressbar frame
        self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent",width=200,height=200)
        self.slider_progressbar_frame.grid(row=0, column=5, padx=(20, 0), pady=(90, 0), sticky="nsew") #Mexer no pady se quiser abaixar mais o frame
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_columnconfigure(2, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(5, weight=0)
        self.slider_progressbar_frame.grid_rowconfigure(6, weight=2)
        self.slider_progressbar_frame.grid_rowconfigure(1, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(11,weight=1)
        
        #Label do Controle Remoto
        self.label_remote = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Remote Control")
        self.label_remote.configure(font=("Segoe UI", 30))
        self.label_remote.grid(row=0, column=0, columnspan=1, padx=(10,0), pady=(10,30), sticky="")

        #Label de Marcha
        self.label_gear = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Gear")
        self.label_gear.configure(font=("Segoe UI", 20))
        self.label_gear.grid(row=3, column=3, columnspan=1, padx=(5,0), pady=(10,20), sticky="")

        self.gear_slider = customtkinter.CTkSlider(master=self.slider_progressbar_frame, from_=-1, to=1, number_of_steps=2, orientation="vertical",height=100)
        self.gear_slider.grid(row=0, column=3, rowspan=5, padx=(10, 15), pady=(20, 10))

        self.bind("r", self.backward_gear)
        self.bind("n", self.neutral_gear)
        self.bind("a", self.forward_gear)   

        #Label do Leme
        self.label_rudder = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Rudder")
        self.label_rudder.configure(font=("Segoe UI", 20))
        self.label_rudder.grid(row=3, column=0, columnspan=1, padx=(10,0), pady=(10,20), sticky="")

        self.rudder_progressbar = customtkinter.CTkProgressBar(master=self.slider_progressbar_frame,width=300)
        self.rudder_progressbar.grid(row=5, column=0, padx=(20, 10), pady=(0, 0),sticky="nsew")
        
        self.slider_rudder = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=-40, to=40, number_of_steps=80)
        self.slider_rudder.grid(row=4, column=0, padx=(20, 10), pady=(15, 15), sticky="ew")
        self.bind("<Left>", self.decrement_rudder_slider) #Configuração para teclas de seta
        self.bind("<Right>", self.increment_rudder_slider)

        #Label de Máquina
        self.label_thrust = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Thrust")
        self.label_thrust.configure(font=("Segoe UI", 20))
        self.label_thrust.grid(row=1, column=0, columnspan=1, padx=(190,0), pady=(20,20), sticky="")

        self.thrust_progressbar = customtkinter.CTkProgressBar(self.slider_progressbar_frame, orientation="vertical",height=400)
        self.thrust_progressbar.grid(row=0, column=2, rowspan=5, padx=(10, 20), pady=(20, 10))

        self.thrust_slider = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=0, to=1, number_of_steps=100, orientation="vertical",height=400)
        self.thrust_slider.grid(row=0, column=1, rowspan=5, padx=(10, 15), pady=(20, 10))
        self.thrust_slider.set(0) #Zero o slider de máquinas
        self.bind("<Up>", self.increment_thrust_slider)
        self.bind("<Down>", self.decrement_thrust_slider)

        # Configurando a barra de progresso
        self.slider_rudder.configure(command=self.update_value_rudder) #Configurei o slider para setar a barra de progresso
        self.thrust_progressbar.set(self.thrust_slider.get())
        self.rudder_progressbar.set((self.controller.nav_yaw+40)*1.25)
        self.thrust_slider.configure(command=self.update_value_thrust)
        self.gear_slider.configure(command=self.update_value_gear)

        #Porcentagem de Máquinas 
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.thrust_slider.get()*100))+"%")
        self.label_machine.configure(font=("Segoe UI", 15))
        self.label_machine.grid(row=0, column=2, columnspan=1, padx=(5,15), pady=(5,5), sticky="n")

        #Angulo do Leme
        self.label_rudder_value = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.slider_rudder.get()))+"°")
        self.label_rudder_value.configure(font=("Segoe UI", 25))
        self.label_rudder_value.grid(row=6, column=0, columnspan=2,rowspan=1, padx=(5,10), pady=(0,10), sticky="s")

        #Valor de Marcha
        self.label_gear_value = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=self.gear_value2text())
        self.label_gear_value.configure(font=("Segoe UI", 15))
        self.label_gear_value.grid(row=0, column=3, columnspan=1, padx=(5,15), pady=(5,5), sticky="n")   
        
        #Texto
        self.label_control = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Control Mode")
        self.label_control.configure(font=("Segoe UI", 25))
        self.label_control.grid(row=9, column=0, rowspan=1, columnspan=2, padx=(5,10), pady=(60,15), sticky="")
        
        #Menu para escolha
        self.combobox = customtkinter.CTkOptionMenu(master=self.slider_progressbar_frame,
                                       values=["Manual", "Joystick"],
                                       command=self.optionmenu_callback)
        self.combobox.grid(row=10, column=0, rowspan=1,columnspan=2, padx=(5,10), pady=(0,205), sticky="")

        # Set option for Plotting Variables

        self.button_plot_variables = customtkinter.CTkButton(master=self.slider_progressbar_frame,
                                                text="Plot Variables",
                                                command=self.toggle_plot_variables)
        self.button_plot_variables.grid(pady=(5, 5), padx=(5, 5), row=10, column=0)        

        # Creates a listbox for selecting multiple variables to plot
        self.listbox_selection = ('RUDDER PLOT',
                                  'DEPTH PLOT')

        var = tkinter.Variable(value=self.listbox_selection)
        # selecmode can be MULTIPLE, SINGLE
        self.select_list = tkinter.Listbox(master=self.slider_progressbar_frame,
                                           listvariable=var,
                                           height=len(self.listbox_selection),
                                           selectmode=tkinter.SINGLE)
        self.select_list.configure(background="#265aad",foreground="white",font=("Segoe UI", 10))
        self.select_list.grid(pady=(5, 5), padx=(5, 5), row=10, column=1)

        # Binds the variables chosen to an action 
        self.select_list.bind('<<ListboxSelect>>', self.items_selected) 

    def gear_value2text(self):
        """
        Converts the GUI value of Gear to the corresponded gear configuration in text
        """
        dict_gear_value = {1:"Ahead",0:"Neutral",-1:"Reverse"}
        gear_str = str(dict_gear_value[int(self.gear_slider.get())])
        return gear_str

    def neutral_gear(self,event):
        """
        Updates Gear GUI to neutral
        """
        if int(self.thrust_slider.get() * 100) < thrust_gear_limit:
            self.gear_slider.set(0)
            self.update_value_gear(None)

    def forward_gear(self,event):
        """
        Updates Gear GUI to forward
        """
        if int(self.thrust_slider.get() * 100) < thrust_gear_limit:
            self.gear_slider.set(1)
            self.update_value_gear(None)

    def backward_gear(self,event):
        """
        Updates Gear GUI to backward
        """
        if int(self.thrust_slider.get() * 100) < thrust_gear_limit:
            self.gear_slider.set(-1)
            self.update_value_gear(None)

    def decrement_rudder_slider(self, event):
        """
        Decrements the rudder slider GUI by 1
        """
        current_value = self.slider_rudder.get()
        new_value = current_value - 1
        self.slider_rudder.set(new_value)
        self.update_value_rudder(new_value)

    def increment_rudder_slider(self, event):
        """
        Increments the rudder slider GUI by 1
        """
        current_value = self.slider_rudder.get()
        new_value = current_value + 1
        self.slider_rudder.set(new_value)
        self.update_value_rudder(new_value)

    def decrement_thrust_slider(self, event):
        """
        Decrements the thrust slider GUI by 1
        """
        current_value = self.thrust_slider.get()
        new_value = current_value - 0.01
        self.thrust_slider.set(new_value)
        self.update_value_thrust(new_value)

    def increment_thrust_slider(self, event):
        """
        Increments the thrust slider GUI by 1
        """
        current_value = self.thrust_slider.get()
        new_value = current_value + 0.01
        self.thrust_slider.set(new_value)
        self.update_value_thrust(new_value)
        
    def optionmenu_callback(self,choice):
        print("optionmenu dropdown clicked:", choice)

    def update_value_thrust(self,other):
        """
        Sends to Moos the desired thrust value and updates the GUI
        """
        value_thrust = int(self.thrust_slider.get()*100)
        self.thrust_progressbar.set(self.thrust_slider.get())
        print(self.thrust_slider.get())
        self.label_machine.configure(text=str(value_thrust)+"%")

        if self.manual_control is True:
            self.controller.notify_thruster(value_thrust)
            print("DESIRED_THRUST: ", value_thrust)

    def update_value_rudder(self,other):
        """
        Sends to Moos the desired rudder value and updates the GUI
        """
        value_rudder = int(self.slider_rudder.get())
        rudder_progress_value = ((self.controller.nav_yaw + 40)*1.25)/100
        self.rudder_progressbar.set(rudder_progress_value)
        self.label_rudder_value.configure(text=str(value_rudder)+"°")

        if self.manual_control is True:
            self.controller.notify_rudder(value_rudder)
            print("DESIRED_RUDDER: ", value_rudder)

    def update_value_gear(self,other):
        """
        Sends to Moos the desired gear value if the acceleration is
        smaller than the limit. and updates the GUI
        """
        if int(self.thrust_slider.get() * 100) < thrust_gear_limit:
            dict_gear = {0:0,-1:1,1:2}
            value_gear = dict_gear[int(self.gear_slider.get())]
            self.label_gear_value.configure(text=self.gear_value2text())

            #self.label_machine.configure(text=str(value_thrust)+"%")
            
            #Mods to Morgan City Demo
            if value_gear == 2:
                gear = "A" #Coloco o valor para ser ahead
            elif value_gear == 1:
                gear = "R"
            elif value_gear == 0:
                gear = "N"

            if self.manual_control is True:
                self.controller.notify_gear(gear)
                print("DESIRED_GEAR: ", gear)

    ###################################################
    ### End of the functions for the Remote Control ###
    ###################################################

    def destroy_maps(self):
        self.map_widget.destroy() #Deleta o mapa
        self.entry.destroy() #Deleta a pesquisa
        self.button_6.destroy() #Deleta o botão de pesquisa
        self.button_4.configure(command=self.open_maps,text="Activate Maps") #Configura o botão para ativar os mapas novamente
        #self.frame_right.grid_columnconfigure(3, weight=2) #Configura o grid para que o label da câmera ocupe todo o espaço
        self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe") #Coloco a câmera no centro

    def open_maps(self):
        self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe") #Câmera no canto
        
        #Cria o mapa
        
        #Offline Maps
        #self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        #Online Maps
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        #self.map_widget.set_overlay_tile_server("http://t1.openseamap.org/seamark/{z}/{x}/{y}.png")
        self.map_widget.set_zoom(15)     
        self.map_widget.set_position(self.controller.nav_lat,self.controller.nav_long) #Atualiza com a última posição do navio

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        #Plota o meu navio
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.controller.nav_heading))+".png"))
        self.ship_image = ImageTk.PhotoImage(self.ship_imagefile)
        self.marker_1 = self.map_widget.set_marker(self.controller.nav_lat, self.controller.nav_long, text="USV", icon=self.ship_image, command=self.marker_callback)
        self.marker_1.change_icon(self.ship_image)
        

        #Crio a barra de pesquisas
        
        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite o Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Busca",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)
        self.button_4.configure(command=self.destroy_maps,text="Deactivate Maps")

    def destroy_camera(self):
        self.label_widget.destroy() #Destruo o label da câmera
        self.button_3.configure(command=self.destroy_camera,text="Camera")
        #Crio o label de novo
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        if (self.map_widget.winfo_exists() == 1): #Checa se o mapa está ativo
            self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe")
        else:
            self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe")
        self.button_3.configure(command=self.open_camera) #Configuro para abrir a câmera novamente

    def open_camera(self):
            self.button_3.configure(command=self.destroy_camera,text="Deactivate Camera") #Coloco o botão para tirar a câmera
  
            # Capture the video frame by frame
            _, frame = self.vid.read()
        
            # Convert image from one color space to other
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        
            # Capture the latest frame and transform to image
            captured_image = Image.fromarray(opencv_image)
        
            # Convert captured image to photoimage
            photo_image = ImageTk.PhotoImage(image=captured_image)
        
            # Displaying photoimage in the label
            self.label_widget.photo_image = photo_image
        
            # Configure image in the label
            self.label_widget.configure(image=photo_image)
        
            # Repeat the same process after every 10 seconds
            self.label_widget.after(5, self.open_camera)

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
            self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()

if __name__ == "__main__":
    app = App()
    app.start()