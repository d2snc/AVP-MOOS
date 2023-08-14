import customtkinter
import cv2
import os
import tkinter
import time
import pymoos
import socket
import numpy as np
import socket
import io
import re
import pyproj
from auvlib.data_tools import jsf_data, utils
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from pyais import decode
#Para safar imagens truncadas do sonar
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from tkinter import ttk, simpledialog

#Configuração do acesso ao moos-ivp
IP_MOOS = "127.0.0.1"
PORTA_MOOS = 9000

# Configuração do AIS da PRT
ip_address = '201.76.184.242' 
port = 8000

# Create a TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
#sock.connect((ip_address, port))


customtkinter.set_default_color_theme("blue")
customtkinter.set_appearance_mode("Dark")


class App(customtkinter.CTk):

    APP_NAME = "AVP-MOOS v0.1"
    WIDTH = 1000
    HEIGHT = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        #Variáveis para a conversão de coordenadas no controle autônomo
        #Dados para Salvador
        #LatOrigin = -12.97933112028696
        #LongOrigin = -38.5666610393065
        #Dados para o RJ
        LatOrigin = -22.93335 
        LongOrigin = -43.136666665 
        #Dados para o lago do MIT
        #LatOrigin  = 43.825300 
        #LongOrigin = -70.330400 
        self.projection_local = pyproj.Proj(proj='aeqd', ellps='WGS84',
                              datum='WGS84', lat_0=LatOrigin, lon_0=LongOrigin)
        self.projection_global = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        self.diff_x = 25.1
        self.diff_y = 38.6
        

        #Auxiliar na plotagem da derrota autônoma
        self.pontos_autonomos = []
        self.pontos_sonar = []


        #Auxiliar para plotagem dos pontos da derrota autonoma
        self.marker_autonomous_list = []

        #Socket para conectar ao sonar
        self.sonar_ip = "127.0.0.1"
        self.sonar_port = 3000
        self.sonar_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sonar_socket.bind((self.sonar_ip, self.sonar_port))
        
        #Variável auxiliar para ligar AIS da praticagem
        self.check_var = tkinter.StringVar(self,"off")

        #Auxilio na plotagem dos AIS
        self.marker_list = []

        #Init pymoos comms
        self.comms = pymoos.comms()

        #Variáveis do sonar plot
        self.waterfall_img = None
        self.markers_sonar = None
        #self.markers_sonar = {} #Dicionário para marcações do sonar
        self.contador_sonar = 0 #Contador de marcações sonar

        #Variáveis auxiliares
        self.mmsi_list = []
        self.markers_ais = {} #Dicionário para colocar os marcadores
        self.markers_image = {} #Dicionário para imagens dos navios AIS
        self.camera_on = False
        self.nav_lat = 0
        self.nav_long = 0
        self.nav_yaw = 0 #leme do navio
        self.nav_heading = 0
        self.nav_speed = 0
        self.last_ais_msg = None
        self.controle_manual = False
        self.contador_ativacao_controle = 0
        self.view_seglist = None
        self.view_point = None
        self.ponto_ativo_marker = None
        self.station_keep_marker = None
        self.deploy = None
        self.return_var = None
        self.bhv_settings = None #Comportamento ativo no momento
        self.ivphelm_bhv_active = None 

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

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Colocar Marcador",
                                                command=self.set_marker_event)
        self.button_1.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Limpar Marcadores",
                                                command=self.clear_marker_event)
        self.button_2.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Câmera",
                                                command=self.open_camera)
        self.button_3.grid(pady=(20, 0), padx=(20, 20), row=2, column=0)

        self.button_4 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Desativar Mapas",
                                                command=self.destroy_maps)
        self.button_4.grid(pady=(20, 0), padx=(20, 20), row=3, column=0)

        self.button_5 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Controle Remoto",
                                                command=self.activate_control)
        self.button_5.grid(pady=(20, 0), padx=(20, 20), row=4, column=0)

        self.button_controle_autonomo = customtkinter.CTkButton(master=self.frame_left,
                                                text="Controle Autônomo",
                                                command=self.update_autonomous)
        self.button_controle_autonomo.grid(pady=(20, 0), padx=(20, 20), row=5, column=0)

        self.sss_button = customtkinter.CTkButton(master=self.frame_left,
                                                text="SSS",
                                                command=self.activate_sss)
        self.sss_button.grid(pady=(20, 0), padx=(20, 20), row=6, column=0)

        self.plot_sonar_button = customtkinter.CTkButton(master=self.frame_left,
                                                text="Sonar Plot",
                                                command=self.receive_sonar)
        self.plot_sonar_button.grid(pady=(20, 0), padx=(20, 20), row=7, column=0)

        #Texto da Latitude

        self.label_lat = customtkinter.CTkLabel(master=self.frame_left, text="Latitude: "+str(self.nav_lat))
        self.label_lat.configure(font=("Segoe UI", 15))
        self.label_lat.grid(row=8, column=0,  padx=(20,20), pady=(50,0), sticky="")

        #Texto da Longitude

        self.label_long = customtkinter.CTkLabel(master=self.frame_left, text="Longitude: "+str(self.nav_long))
        self.label_long.configure(font=("Segoe UI", 15))
        self.label_long.grid(row=9, column=0,  padx=(20,20), pady=(0,20), sticky="")

        #Texto do rumo

        self.label_heading = customtkinter.CTkLabel(master=self.frame_left, text="Rumo: "+str(self.nav_heading))
        self.label_heading.configure(font=("Segoe UI", 25))
        self.label_heading.grid(row=10, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Texto da veloc

        self.label_speed = customtkinter.CTkLabel(master=self.frame_left, text="Velocidade: "+str(self.nav_speed)+" nós",)
        self.label_speed.configure(font=("Segoe UI", 25))
        self.label_speed.grid(row=11, column=0,  padx=(20,20), pady=(20,20), sticky="")

        #Texto do angulo do leme

        self.label_yaw = customtkinter.CTkLabel(master=self.frame_left, text="Ângulo do Leme: "+str(round(self.nav_yaw,2)))
        self.label_yaw.configure(font=("Segoe UI", 20))
        self.label_yaw.grid(row=12, column=0,  padx=(20,20), pady=(20,20), sticky="")

        

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Servidor de Mapas:", anchor="w")
        self.map_label.grid(row=13, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=14, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Aparência:", anchor="w")
        self.appearance_mode_label.grid(row=15, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=16, column=0, padx=(20, 20), pady=(10, 20))

        

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)
        
        #Criação do mapa inicial
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(self.script_directory, "offline_tiles_rio.db")
        #Mapas offline
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        #Mapas online
        #self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="Digite Endereço")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_6 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Buscar",
                                                width=90,
                                                command=self.search_event)
        self.button_6.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        self.botao_centralizar_navio = customtkinter.CTkButton(master=self.frame_right,
                                                text="Centralizar Navio",
                                                width=90,
                                                command=self.centralizar_navio)
        self.botao_centralizar_navio.grid(row=0, column=2, sticky="w", padx=(12, 0), pady=12)

        #Funções no mapa inicial
        self.map_widget.add_right_click_menu_command(label="Adicionar mina",
                                            command=self.add_mina,
                                            pass_coords=True)
        
        #Ponto de derrota autônoma
        self.map_widget.add_right_click_menu_command(label="Adicionar ponto de derrota autônoma",
                                            command=self.add_autonomous_point,
                                            pass_coords=True)
        
        #Varredura sonar
        self.map_widget.add_right_click_menu_command(label="Adicionar varredura sonar",
                                            command=self.add_sonar_sweep,
                                            pass_coords=True)

        
        #Botão que liga/desliga AIS da praticagem
        self.checkbox = customtkinter.CTkCheckBox(master=self.frame_left, text="AIS Praticagem", command=self.update_lista_praticagem(),variable=self.check_var, onvalue="on", offvalue="off")
        self.checkbox.grid(row=17, column=0, padx=(20, 20), pady=(10, 20))

        ###Imagem da camera
        self.vid = cv2.VideoCapture('teste.mp4')
        #rtsp_url = 'rtsp://172.18.14.214/axis-media/media.amp' #Para usar na lancha
        #self.vid = cv2.VideoCapture(rtsp_url)
        self.camera_width , self.camera_height = 800,600

        # Set the width and height
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)

        # Create a label and display it on app
        self.text_var = tkinter.StringVar(value="")
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        self.label_widget.grid(row=0,column=2,sticky="nsew",rowspan=1,columnspan=3)


        # Set default values
        self.map_widget.set_position(-22.911663710002028, -43.15942144574782) #Posição inicial do mapa
        self.map_widget.set_zoom(15) 
        #self.map_widget.set_address("Rio de Janeiro")
        self.map_option_menu.set("Google normal")
        self.appearance_mode_optionemenu.set("Dark")

        

        #Teste de marcadores
        self.marker_1 = self.map_widget.set_marker(-22.910369249774234, -43.15891349244546, text="VSNT-Lab", icon=ship_image, command=self.marker_callback)

        #Conexão com a database do MOOS
        
        self.comms.set_on_connect_callback(self.onc)
        self.comms.set_on_mail_callback(self.onm)
        self.comms.run(IP_MOOS, PORTA_MOOS, 'avp-moos') #Aq configuramos o ip do computador com MOOS para fazer a conexão

        #Loop para atualizar a posição do navio
        
        #Loop principal
        self.update_ship_position() #Loop para atualizar a posição do navio
        self.update_gui() #Loop para atualizar dados na GUI
        self.update_ais_contacts() #Loop para atualizar os contatos AIS
        self.update_station_keep() #Loop para atualizar posição do station keep
        #self.update_lista_praticagem() #Loop para atualizar a lista de praticagem



    def activate_sss(self):
        os.popen('python3 funcionando_recebendo_img.py')

    #Função para centralizar o navio na tela
    def centralizar_navio(self):
        self.map_widget.set_position(self.nav_lat,self.nav_long)

    #Função para converter de graus para graus, minutos e segundos
    def decimal_degrees_to_dms(self,latitude):
        degrees = int(latitude)
        decimal_minutes = (latitude - degrees) * 60
        minutes = int(decimal_minutes)
        seconds = (decimal_minutes - minutes) * 60
        return degrees, minutes, seconds

    #Funções para comunicação do Pymoos
    def onc(self):
        #Variáveis do MOOS para exibição do navio 
        self.comms.register('NAV_LAT', 0)
        self.comms.register('NAV_LONG', 0)
        self.comms.register('NAV_HEADING', 0)
        self.comms.register('NAV_SPEED', 0)
        self.comms.register('NAV_YAW', 0)
        #self.comms.register('LAST_AIS_MSG', 0)
        self.comms.register('MSG_UDP', 0)

        #Variáveis do MOOS para controle do navio
        self.comms.register('DEPLOY', 0)
        self.comms.register('MOOS_MANUAL_OVERIDE', 0)
        self.comms.register('RETURN', 0)
        self.comms.register('DESIRED_RUDDER', 0)
        self.comms.register('DESIRED_THRUST', 0)

        #Variáveis do MOOS para o controle autônomo
        self.comms.register('VIEW_SEGLIST', 0) #rela de pontos
        self.comms.register('VIEW_POINT', 0) #Ponto autônomo ativo no momento
        self.comms.register('BHV_SETTINGS', 0) #Comportamento ativo no momento
        self.comms.register('IVPHELM_BHV_ACTIVE', 0) #Comportamento ativo no momento

        
        return True
    
    def onm(self):
        msg_list = self.comms.fetch()

        for msg in msg_list:
            val = msg.double()

            if msg.name() == 'NAV_LAT':
                self.nav_lat = val
                #print("Latitude: "+str(round(self.nav_lat,8)))
            elif msg.name() == 'NAV_LONG':
                self.nav_long = val
                #print("Longitude: "+str(round(self.nav_long,8)))
            elif msg.name() == 'NAV_HEADING':
                self.nav_heading = val
            elif msg.name() == 'NAV_SPEED':
                self.nav_speed = val
            elif msg.name() == 'MSG_UDP':
                val = msg.string()
                #print(val)
                if val.startswith('!AIVDM'):
                    self.last_ais_msg = val
                    #print(val)
            elif msg.name() == 'VIEW_SEGLIST':
                val = msg.string()
                self.view_seglist = val
                #print(val)
            elif msg.name() == 'NAV_YAW': #Leme do navio
                self.nav_yaw = val
                #print(val)
            elif msg.name() == 'VIEW_POINT': #Ponto autônomo ativo no momento
                val = msg.string()
                self.view_point = val
            elif msg.name() == 'DEPLOY':
                val = msg.string()
                self.deploy = val
                #print("Deploy: "+val)
            elif msg.name() == 'BHV_SETTINGS': 
                val = msg.string()
                self.bhv_settings = val
                #print('Comportamento ativo no momento: '+self.bhv_settings)
            elif msg.name() == 'IVPHELM_BHV_ACTIVE':
                val = msg.string()
                self.ivphelm_bhv_active = val
                print(self.ivphelm_bhv_active)
            elif msg.name() == 'RETURN':
                val = msg.string()
                self.return_var = val
                
                
            
        return True
    
    #### Funções do controle autônomo ###
    
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
        data_point = self.view_point.split(",")
        x = float(data_point[0][2:]) #Pego o valor de x do ponto ativo
        y = float(data_point[1][2:])#Pego o valor de y do ponto ativo

        #Converto x e y para lat e long
        inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, x-self.diff_x, y-self.diff_y)

        #Ploto o marker do ponto ativo
        ponto_ativo_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "hit_marker.png")).resize((70, 70)))
        #print("Ponto ativo no controle autônomo: lat:"+str(inv_latitude)+" long:"+str(inv_longitude))
        
        if self.ponto_ativo_marker is None:
            self.ponto_ativo_marker = self.map_widget.set_marker(inv_latitude, inv_longitude, icon=ponto_ativo_image)
        else:
            self.ponto_ativo_marker.set_position(inv_latitude,inv_longitude)
        
        self.after(1000,self.update_active_autonomous_point)

    
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
                inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, float(match[0])-self.diff_x, float(match[1])-self.diff_y)

                #Adiciono os pontos na lista
                self.pontos_autonomos.append((inv_latitude, inv_longitude))

            # Pontos para debug
            print(self.pontos_autonomos)

            #Defino o caminho
            self.path_1 = self.map_widget.set_path(self.pontos_autonomos)

            #Definindo pontos da derrota como markers
            for ponto in self.pontos_autonomos:
                self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.pontos_autonomos.index(ponto)+1)+" Ponto de derrota autônoma"))

            
        
            # Ploto a derrota no mapa
            #path_1 = self.map_widget.set_path([self.marker_autonomous_list[0].position, self.marker_autonomous_list[1].position, (-43.15947614659043, -22.911947446774985), (-43.15947564792508, -22.908967568090326)])

    #Adiciona a varredura sonar no mapa
    def add_sonar_sweep(self,coords):
        
        #Transformo coordenadas globais em locais
        
        x, y = pyproj.transform(self.projection_global, self.projection_local, coords[1], coords[0])
        
        string_varredura_inicial='points=format=lawnmower,x='+str(round(x,2))+',y='+str(round(y,2))+',degs=0,height=500,width=1800,lane_width=150'
        print(string_varredura_inicial)
        #Envia a varredura sonar para o MOOS
        self.comms.notify('WPT_UPDATE', string_varredura_inicial,pymoos.time())
        
        print("Enviado para o MOOS -> WPT_UPDATE="+string_varredura_inicial)
        
        #Inicia e depois para
        if self.deploy == 'false' or self.return_var == 'true':
            self.comms.notify('DEPLOY', 'true',pymoos.time())
            self.comms.notify('MOOS_MANUAL_OVERIDE', 'false',pymoos.time())
            self.comms.notify('RETURN', 'false',pymoos.time())
        self.comms.notify('END', 'false',pymoos.time())
        #Caso não atualize a varredura, aumentar o delay aqui
        time.sleep(1)
        self.comms.notify('END', 'true',pymoos.time())
        
        #Após enviar atualiza os pontos na tela
        
        #Deleta pontos de indicação da derrota
        for marker in self.marker_autonomous_list:
            marker.delete()
            
        #Deleta o caminho do mapa
        self.map_widget.delete_all_path()
        
        #Limpo a lista self.pontos_autonomos
        self.pontos_autonomos = []
        
        #Pega os pontos da variável e cria a nova derrota
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
                inv_longitude, inv_latitude = pyproj.transform(self.projection_local, self.projection_global, float(match[0])-self.diff_x, float(match[1])-self.diff_y)

                #Adiciono os pontos na lista
                self.pontos_autonomos.append((inv_latitude, inv_longitude))
                
            #Defino o caminho
            self.path_1 = self.map_widget.set_path(self.pontos_autonomos)

            #Definindo pontos da derrota como markers
            for ponto in self.pontos_autonomos:
                self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.pontos_autonomos.index(ponto)+1)+" Ponto de derrota autônoma"))

    
    #Adiciona ponto de derrota autônoma no mapa

    def add_autonomous_point(self,coords):
        print("Adicionar ponto de derrota:", coords)
        #Adiciona ponto na lista de pontos
        self.pontos_autonomos.append(coords)
        #Defino o caminho
        if len(self.pontos_autonomos) > 1: #Para não criar o caminho c/ 1 ponto só
            self.path_1 = self.map_widget.set_path(self.pontos_autonomos)

        #Definindo pontos da derrota como markers
        #Só adiciona pontos que não estão na lista
        for ponto in self.pontos_autonomos:
            if ponto not in self.marker_autonomous_list:
                self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.pontos_autonomos.index(ponto)+1)+" Ponto de derrota autônoma"))

    #Destrói a GUI de controle autônomo
    def destroy_autonomous(self):
        #Deleto toda a derrota do mapa
        self.map_widget.delete_all_path()
        #Deleto os pontos do mapa
        for marker in self.marker_autonomous_list:
            marker.delete()
        #Alterar a função do botão
        self.button_controle_autonomo.configure(command=self.update_autonomous,text="Controle Autônomo")
        self.slider_progressbar_frame1.destroy()
        self.label_machine1.destroy()
        self.ponto_ativo_marker.destroy()
        
        #Desativa o pHelmIvP do MOOS
        self.comms.notify('END', 'true',pymoos.time())
        
        #Atualiza a posição da station keep
         #Converto para coordenadas locais antes de enviar
        x, y = pyproj.transform(self.projection_global, self.projection_local, self.nav_long, self.nav_lat)
        string= str(round(x,2)+self.diff_x)+","+str(round(y,2)+self.diff_y)
        self.comms.notify('STATION_UPDATES', 'station_pt='+string,pymoos.time())
        

        pass

    #Função para ativar o controle autônomo
    def create_menu_autonomous(self):
        #Altero o texto do botão
        self.button_controle_autonomo.configure(command=self.destroy_autonomous,text="Desativar Controle Autônomo")

        #Crio o frame com o controle autônomo
        # create slider and progressbar frame
        self.slider_progressbar_frame1 = customtkinter.CTkFrame(self, fg_color="transparent",width=400,height=200)
        self.slider_progressbar_frame1.grid(row=0, column=5, padx=(20, 0), pady=(90, 0), sticky="nsew") #Mexer no pady se quiser abaixar mais o frame
        self.slider_progressbar_frame1.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame1.grid_rowconfigure(3, weight=1)
        
        #Label do Controle Autônomo
        self.label_machine1 = customtkinter.CTkLabel(master=self.slider_progressbar_frame1, text="Controle Autônomo")
        self.label_machine1.configure(font=("Segoe UI", 30))
        self.label_machine1.grid(row=0, column=0, columnspan=2, padx=(50,50), pady=(10,25), sticky="")

        #Botão para iniciar 
        self.button_inicio_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Iniciar",
                                                command=self.activate_autonomous)
        self.button_inicio_autonomo.grid(pady=(5, 5), padx=(5, 5), row=1, column=0)

        self.button_parada_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Parar",
                                                command=self.stop_autonomous)
        self.button_parada_autonomo.grid(pady=(5, 5), padx=(5, 35), row=1, column=1)

        self.button_parada_autonomo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Limpar Derrota",
                                                command=self.clean_autonomous)
        self.button_parada_autonomo.grid(pady=(15, 5), padx=(35, 35), row=2, column=0)
        
        self.button_remove_ultimo = customtkinter.CTkButton(master=self.slider_progressbar_frame1,
                                                text="Remover Último Ponto",
                                                command=self.clean_last_autonomous)
        self.button_remove_ultimo.grid(pady=(15, 5), padx=(35, 60), row=2, column=1)


    #Função para ativar o início da derrota autônoma no MOOS-IvP
    def activate_autonomous(self): 
        string_update = []
        #Crio a lista com todos os pontos da derrota autônoma
        for ponto in self.pontos_autonomos:
            #Converto para coordenadas locais antes de enviar
            x, y = pyproj.transform(self.projection_global, self.projection_local, ponto[1], ponto[0])
            string_update.append(str(round(x,2)+self.diff_x)+","+str(round(y,2)+self.diff_y)+":")
        #Junto os pontos
        string_update = ''.join(string_update)
        string_update = string_update[:-1] #Removo o último ":" da string
        string_update = 'polygon='+string_update #colocar entre aspas para o MOOS-IvP entender

        #Caso o deploy seja false, passo para true
        if self.deploy == 'false' or self.return_var == 'true':
            self.comms.notify('DEPLOY', 'true',pymoos.time())
            self.comms.notify('MOOS_MANUAL_OVERIDE', 'false',pymoos.time())
            self.comms.notify('RETURN', 'false',pymoos.time())
        
        #Atualizo a derrota no MOOS
        self.comms.notify('WPT_UPDATE', string_update,pymoos.time())
        #Configuro a endflag END para false e assim retomar o controle autonomo
        self.comms.notify('END', 'false',pymoos.time())
        #Executo a função para mostrar o waypoint ativo
        self.update_active_autonomous_point()

    #Função para parar o controle autônomo no MOOS-IvP
    def stop_autonomous(self):
        #Desativa o pHelmIvP no MOOS
        self.comms.notify('END', 'true',pymoos.time())
        #Atualiza a posição da station keep
         #Converto para coordenadas locais antes de enviar
        x, y = pyproj.transform(self.projection_global, self.projection_local, self.nav_long, self.nav_lat)
        string= str(round(x,2)+self.diff_x)+","+str(round(y,2)+self.diff_y)
        self.comms.notify('STATION_UPDATES', 'station_pt='+string,pymoos.time())
        #Envio o RETURN=true - Ele só parava assim
        self.comms.notify('RETURN', 'true',pymoos.time())
        

    #Função para deletar o último ponto da derrota autônoma criada
    def clean_last_autonomous(self):
        
        #Deleta pontos de indicação da derrota
        for marker in self.marker_autonomous_list:
            marker.delete()
        self.pontos_autonomos.pop() #Removo o último ponto na lista
        self.marker_autonomous_list.pop() #Deleta da lista o ícone
        
        #Deleto toda a derrota do mapa
        self.map_widget.delete_all_path()
        
        #Defino o caminho
        self.path_1 = self.map_widget.set_path(self.pontos_autonomos)
        
        #Crio a derrota
        for ponto in self.pontos_autonomos:
            self.marker_autonomous_list.append(self.map_widget.set_marker(ponto[0], ponto[1], text="#"+str(self.pontos_autonomos.index(ponto)+1)+" Ponto de derrota autônoma"))


        
        
        
        
    
    #Função para limpar a derrota autônoma no MOOS-IvP
    def clean_autonomous(self):
        #Deleto os caminhos criados
        self.map_widget.delete_all_path()

        #Removo pontos da lista self.marker_autonomous_list
        for marker in self.marker_autonomous_list:
            marker.delete()

        #Limpo a lista self.pontos_autonomos
        self.pontos_autonomos = []

    ### Fim de funções para o controle autônomo ###
    
    #Atualiza a lista de ctts AIS q vem da praticagem - Lembrar sempre de executar funções no final do programa
    
    def update_lista_praticagem(self): 
        if self.check_var.get() == "on":
            global sock
            data = sock.recv(1024)
            if not data:
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


    #Adiciona mina no mapa
    def add_mina(self,coords):
        mina_image = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "mine.png")).resize((70, 70)))
        print("Adicionar Possível Mina:", coords)
        mina_marker = self.map_widget.set_marker(coords[0], coords[1], text="Possível mina",image=mina_image)
    

    

    #Plota a imagem vinda do sonar na carta náutica
    def receive_sonar(self):
        self.pontos_sonar.append((self.nav_lat-0.0001,self.nav_long-0.0001))
        if (len(self.pontos_sonar) > 1):
            self.path_2 = self.map_widget.set_path(self.pontos_sonar)
                
        
        self.after(1000,self.receive_sonar) #A cada 0,1 segundo ele vai receber posição sonar
            


    #TODO Adicionar função que ao clicar em um contato AIS abra um pop-up mostrando informações do navio
    #TODO Adicionar função no botão da AIS praticagem para remover todos os contatos da tela quando apertar no botão

    #Decodificar msgs AIS - Coloquei estático pq a função decode não usa self
    @staticmethod
    def decode_ais_msg(ais_msg):
        ais_msg = ais_msg.encode()
        #Catch errors and let them pass
        try:
            ais_msg = decode(ais_msg)
        except:
            ais_msg = None #Por enquanto vou retornar None caso esteja com erro
            pass
        return ais_msg
        

    #Função para atualizar os contatos AIS
    def update_ais_contacts(self):
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

        
        

    
    #Função para atualizar dados na GUI:
    def update_gui(self):
        degrees, minutes, seconds = self.decimal_degrees_to_dms(self.nav_lat)
        self.label_lat.configure(text=f"Latitude: {degrees}° {minutes}' {seconds:.2f}\"")
        degrees, minutes, seconds = self.decimal_degrees_to_dms(self.nav_long)
        self.label_long.configure(text=f"Longitude: {degrees}° {minutes}' {seconds:.2f}\"")
        self.label_heading.configure(text="Rumo: "+str(int(self.nav_heading))+" °")
        self.label_speed.configure(text="Velocidade: "+str(int(self.nav_speed))+" nós")
        self.label_yaw.configure(text="Ângulo Leme: "+str(round(self.nav_yaw,2)))
        self.after(1000,self.update_gui)


    #Função em loop utilizada para atualizar a posição do meu navio
    def update_ship_position(self):
        if (self.map_widget.winfo_exists() == 1): #Checa se existe o mapa
            # correção da posição para o mapa
            self.marker_1.set_position(self.nav_lat-0.0001,self.nav_long-0.0001) #Ajustar os valores para ter uma melhor posição do navio
            #self.map_widget.set_position(self.nav_lat,self.nav_long) #Centraliza o mapa no navio, colocar uma opção para ativar ela 
            #self.map_widget.set_zoom(15)
            self.label_widget.configure(text=str(self.nav_lat)+" "+str(self.nav_long))

            #Atualiza a imagem do navio de acordo com o ângulo self.nav_heading
            self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.nav_heading))+".png"))
            ship_image = ImageTk.PhotoImage(self.ship_imagefile)
            self.marker_1.change_icon(ship_image)
        else:
            print("Mapa inativo")

        self.after(1000,self.update_ship_position) #Coloco essa função em loop para repetir a cada 1 seg dentro do programa


    #Funções da GUI abaixo

    def marker_callback(self,marker): #O que acontece quando clica no marker
        print(marker.text)

        

    def destroy_control(self): #Destrói o frame com o controle
        self.button_5.configure(command=self.activate_control,text="Controle Remoto")
        self.slider_progressbar_frame.destroy()
        self.label_machine.destroy()
        self.label_leme.destroy()
        self.label_controle.destroy()
        self.progressbar_2.destroy()
        self.progressbar_3.destroy()
        self.slider_1.destroy()
        self.slider_2.destroy()
        #self.combobox.destroy()

        #Desativa o controle manual no MOOS
        self.comms.notify('MOOS_MANUAL_OVERIDE', 'false',pymoos.time())
        self.controle_manual = False

        #Desativa o pHelmIvP no MOOS
        self.comms.notify('END', 'true',pymoos.time())
        
        #Atualiza a posição da station keep
         #Converto para coordenadas locais antes de enviar
        x, y = pyproj.transform(self.projection_global, self.projection_local, self.nav_long, self.nav_lat)
        string= str(round(x,2)+self.diff_x)+","+str(round(y,2)+self.diff_y)
        self.comms.notify('STATION_UPDATES', 'station_pt='+string,pymoos.time())
        


        

    def activate_control(self): #Cria o frame com o controle
        #Envia a configuração para o MOOS-Ivp para o controle manual começar
        
        ## Comandos para iniciar o pHelmIvP
        #Só executa quando lança a função pela primeira vez
        #Notifico o deploy=true
        if self.deploy == 'false':
            self.comms.notify('DEPLOY', 'true',pymoos.time()) 
        
        #Passo o comando para manual
        self.comms.notify('MOOS_MANUAL_OVERIDE', 'true',pymoos.time())
        #Seto a variável auxiliar para True
        self.controle_manual = True
            


        self.button_5.configure(command=self.destroy_control,text="Desativar Controle Remoto")
        #Frame com slider para controle de velocidade   

        # create slider and progressbar frame
        self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent",width=200,height=200)
        self.slider_progressbar_frame.grid(row=0, column=5, padx=(20, 0), pady=(90, 0), sticky="nsew") #Mexer no pady se quiser abaixar mais o frame
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(5, weight=0)
        self.slider_progressbar_frame.grid_rowconfigure(6, weight=2)
        self.slider_progressbar_frame.grid_rowconfigure(1, weight=1)
        
        #Label do Controle Remoto
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Controle Remoto")
        self.label_machine.configure(font=("Segoe UI", 30))
        self.label_machine.grid(row=0, column=0, columnspan=1, padx=(10,0), pady=(10,30), sticky="")

        #Label do Leme
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Leme")
        self.label_machine.configure(font=("Segoe UI", 20))
        self.label_machine.grid(row=3, column=0, columnspan=1, padx=(10,0), pady=(10,20), sticky="")

        #Label das Máquinas
        
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Máquinas")
        self.label_machine.configure(font=("Segoe UI", 20))
        self.label_machine.grid(row=1, column=0, columnspan=1, padx=(190,0), pady=(20,20), sticky="")

        self.progressbar_2 = customtkinter.CTkProgressBar(self.slider_progressbar_frame,width=300)
        self.progressbar_2.grid(row=5, column=0, padx=(20, 10), pady=(0, 0),sticky="nsew")
        
        self.slider_1 = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=-40, to=40, number_of_steps=80)
        self.slider_1.grid(row=4, column=0, padx=(20, 10), pady=(15, 15), sticky="ew")
        self.bind("<Left>", self.decrement_slider1) #Configuração para teclas de seta
        self.bind("<Right>", self.increment_slider1)
        self.bind("<Up>", self.increment_slider2)
        self.bind("<Down>", self.decrement_slider2)
        self.slider_2 = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=0, to=1, number_of_steps=100, orientation="vertical",height=400)
        self.slider_2.grid(row=0, column=1, rowspan=5, padx=(10, 15), pady=(20, 10))
        self.slider_2.set(0) #Zero o slider de máquinas
        self.progressbar_3 = customtkinter.CTkProgressBar(self.slider_progressbar_frame, orientation="vertical",height=400)
        self.progressbar_3.grid(row=0, column=2, rowspan=5, padx=(10, 20), pady=(20, 10))

        #Configurando a barra de progresso
        self.slider_1.configure(command=self.update_value_leme) #Configurei o slider para setar a barra de progresso
        self.progressbar_3.set(self.slider_2.get())
        self.slider_2.configure(command=self.update_value_maquinas)

        #Porcentagem de Máquinas 
        self.label_machine = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.slider_2.get()*100))+"%")
        self.label_machine.configure(font=("Segoe UI", 15))
        self.label_machine.grid(row=0, column=2, columnspan=1, padx=(5,15), pady=(5,5), sticky="n")

        #Angulo do Leme
        self.label_leme = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text=str(int(self.slider_1.get()))+"°")
        self.label_leme.configure(font=("Segoe UI", 25))
        self.label_leme.grid(row=6, column=0, columnspan=2,rowspan=1, padx=(5,10), pady=(0,10), sticky="s")
        
        #Texto
        self.label_controle = customtkinter.CTkLabel(master=self.slider_progressbar_frame, text="Modo de controle")
        self.label_controle.configure(font=("Segoe UI", 25))
        self.label_controle.grid(row=9, column=0, rowspan=1, columnspan=2, padx=(5,10), pady=(60,15), sticky="")
        
        #Menu para escolha
        self.combobox = customtkinter.CTkOptionMenu(master=self.slider_progressbar_frame,
                                       values=["Manual", "Joystick"],
                                       command=self.optionmenu_callback)
        self.combobox.grid(row=10, column=0, rowspan=1,columnspan=2, padx=(5,10), pady=(0,205), sticky="")


    def decrement_slider1(self, event):
        current_value = self.slider_1.get()
        new_value = current_value - 1
        self.slider_1.set(new_value)
        self.update_value_leme(new_value)

    def increment_slider1(self, event):
        current_value = self.slider_1.get()
        new_value = current_value + 1
        self.slider_1.set(new_value)
        self.update_value_leme(new_value)

    def decrement_slider2(self, event):
        current_value = self.slider_2.get()
        new_value = current_value - 0.01
        self.slider_2.set(new_value)
        self.update_value_maquinas(new_value)

    def increment_slider2(self, event):
        current_value = self.slider_2.get()
        new_value = current_value + 0.01
        self.slider_2.set(new_value)
        self.update_value_maquinas(new_value)
        
    def optionmenu_callback(self,choice):
        print("optionmenu dropdown clicked:", choice)

    def update_value_maquinas(self,other):
        #print(other)
        self.progressbar_3.set(self.slider_2.get())
        self.label_machine.configure(text=str(int(self.slider_2.get()*100))+"%")

        if self.controle_manual is True:
            self.comms.notify('DESIRED_THRUST', int(self.slider_2.get()*100),pymoos.time())
            print("DESIRED_THRUST: ", int(self.slider_2.get()))

    def update_value_leme(self,other):
        #print(other)
        self.progressbar_2.set(self.slider_1.get())
        self.label_leme.configure(text=str(int(self.slider_1.get()))+"°")

        if self.controle_manual is True:
            self.comms.notify('DESIRED_RUDDER', int(self.slider_1.get()),pymoos.time())
            print("DESIRED_RUDDER: ", int(self.slider_1.get()))
        

    def destroy_maps(self):
        self.map_widget.destroy() #Deleta o mapa
        self.entry.destroy() #Deleta a pesquisa
        self.button_6.destroy() #Deleta o botão de pesquisa
        self.button_4.configure(command=self.open_maps,text="Ativar Mapas") #Configura o botão para ativar os mapas novamente
        #self.frame_right.grid_columnconfigure(3, weight=2) #Configura o grid para que o label da câmera ocupe todo o espaço
        self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe") #Coloco a câmera no centro

        

    def open_maps(self):
        self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe") #Câmera no canto
        
        #Cria o mapa
        
        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0,use_database_only=True,database_path=self.database_path)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))
        self.map_widget.set_overlay_tile_server("http://tiles.openseamap.org/seamark//{z}/{x}/{y}.png")
        self.map_widget.set_zoom(15)     
        self.map_widget.set_position(self.nav_lat,self.nav_long) #Atualiza com a última posição do navio

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
        self.ship_imagefile = Image.open(os.path.join(self.current_path, "images", "ship_red"+str(int(self.nav_heading))+".png"))
        self.ship_image = ImageTk.PhotoImage(self.ship_imagefile)
        self.marker_1 = self.map_widget.set_marker(self.nav_lat, self.nav_long, text="VSNT-Lab", icon=self.ship_image, command=self.marker_callback)
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
        self.button_4.configure(command=self.destroy_maps,text="Desativar Mapas")

    def destroy_camera(self):
        self.label_widget.destroy() #Destruo o label da câmera
        self.button_3.configure(command=self.destroy_camera,text="Câmera")
        #Crio o label de novo
        self.label_widget = customtkinter.CTkLabel(self,textvariable=self.text_var)
        if (self.map_widget.winfo_exists() == 1): #Checa se o mapa está ativo
            self.label_widget.grid(row=0, rowspan=1, column=2, columnspan=3, sticky="nswe")
        else:
            self.label_widget.grid(row=0, rowspan=1, column=1, columnspan=3, sticky="nswe")
        self.button_3.configure(command=self.open_camera) #Configuro para abrir a câmera novamente

    def open_camera(self):
            self.button_3.configure(command=self.destroy_camera,text="Desativar Câmera") #Coloco o botão para tirar a câmera
  
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
